package com.example.offlinelicensingmodel

import android.content.Context
import android.util.Base64
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.TimeZone

/**
 * Bộ xác thực License ngoại tuyến (Offline 100%) cho PDA.
 *
 * Triển khai 4 lớp phòng thủ:
 * 1. Định dạng JWT RFC 8037 (EdDSA).
 * 2. Xác thực chữ ký Ed25519 trong tầng C++ NDK (Bảo vệ Public Key).
 * 3. So khớp phần cứng qua Device Fingerprint (16 ký tự Crockford Base32).
 * 4. Zero Trust Anti-Clock Rollback: Kiểm tra hạn dùng và chống lùi đồng hồ hệ thống.
 */
class LicenseValidator(private val context: Context) {

    companion object {
        init {
            System.loadLibrary("offlinelicensingmodel")
        }

        // Dung sai trôi đồng hồ cho phép: 5 phút (300 giây)
        private const val CLOCK_TOLERANCE_SECONDS = 300L
    }

    /**
     * Hàm JNI Native gọi xuống C++ để xác thực chữ ký Ed25519 với Public Key được mã hóa XOR.
     */
    private external fun verifyNativeSignature(
        signingInput: ByteArray,
        signature: ByteArray
    ): Int

    enum class LicenseStatus {
        VALID,
        INVALID_FORMAT,
        INVALID_SIGNATURE,
        DEVICE_MISMATCH,
        EXPIRED,
        NOT_YET_VALID,
        CLOCK_ROLLBACK_DETECTED,
        ROOT_DEVICE_DETECTED
    }

    data class LicensePayload(
        val iss: String,
        val sub: String,
        val df: String,
        val type: String,
        val iat: Long,
        val exp: Long,
        val features: List<String>,
        val customer: String,
        val model: String
    )

    data class ValidationResult(
        val status: LicenseStatus,
        val message: String,
        val payload: LicensePayload? = null
    )

    private val storage = LicenseStorage(context)
    private val rootChecker = RootChecker(context)

    /**
     * Xác thực toàn diện một chuỗi Token JWT.
     * Nếu hợp lệ, tự động cập nhật mốc last_known_time và lưu token vào bộ nhớ an toàn.
     */
    fun validateAndActivate(jwtToken: String): ValidationResult {
        val result = validateToken(jwtToken)
        if (result.status == LicenseStatus.VALID) {
            storage.saveLicense(jwtToken)
            storage.updateLastKnownTime(System.currentTimeMillis() / 1000)
        }
        return result
    }

    /**
     * Xác thực Token đang lưu trong bộ nhớ (dùng khi khởi động app hoặc kiểm tra định kỳ).
     */
    fun validateSavedLicense(): ValidationResult {
        // Kiểm tra Root ngay cả với License đã lưu
        val rootStatus = rootChecker.checkRoot()
        if (rootStatus.isRooted) {
            return ValidationResult(
                status = LicenseStatus.ROOT_DEVICE_DETECTED,
                message = "CẢNH BÁO BẢO MẬT: ${rootStatus.details} Hệ thống khóa bản quyền trên thiết bị Root!"
            )
        }

        val savedToken = storage.getSavedLicense()
            ?: return ValidationResult(
                status = LicenseStatus.INVALID_FORMAT,
                message = "Thiết bị chưa được kích hoạt bản quyền."
            )
        return validateToken(savedToken)
    }

    /**
     * Hàm kiểm tra 4 lớp phòng thủ cho chuỗi JWT token.
     */
    fun validateToken(jwtToken: String): ValidationResult {
        // ==============================================================
        // LỚP 0: KIỂM TRA MÔI TRƯỜNG THIẾT BỊ (ROOT CHECKER)
        // ==============================================================
        val rootStatus = rootChecker.checkRoot()
        if (rootStatus.isRooted) {
            return ValidationResult(
                status = LicenseStatus.ROOT_DEVICE_DETECTED,
                message = "TỪ CHỐI BẢN QUYỀN: ${rootStatus.details} Không hỗ trợ thiết bị đã Root!"
            )
        }

        val parts = jwtToken.trim().split(".")
        if (parts.size != 3) {
            return ValidationResult(
                status = LicenseStatus.INVALID_FORMAT,
                message = "Định dạng License không đúng chuẩn JWT (thiếu thành phần)."
            )
        }

        val headerB64 = parts[0]
        val payloadB64 = parts[1]
        val signatureB64 = parts[2]

        // 1. Phân tích Header
        val headerJson = try {
            val headerBytes = Base64.decode(headerB64, Base64.URL_SAFE or Base64.NO_WRAP)
            JSONObject(String(headerBytes, Charsets.UTF_8))
        } catch (e: Exception) {
            return ValidationResult(
                status = LicenseStatus.INVALID_FORMAT,
                message = "Lỗi giải mã Header: ${e.message}"
            )
        }

        if (headerJson.optString("alg") != "EdDSA") {
            return ValidationResult(
                status = LicenseStatus.INVALID_FORMAT,
                message = "Thuật toán không được hỗ trợ (yêu cầu EdDSA)."
            )
        }

        // 2. Phân tích Payload
        val payload = try {
            val payloadBytes = Base64.decode(payloadB64, Base64.URL_SAFE or Base64.NO_WRAP)
            val json = JSONObject(String(payloadBytes, Charsets.UTF_8))

            val featuresList = mutableListOf<String>()
            val featArray = json.optJSONArray("features")
            if (featArray != null) {
                for (i in 0 until featArray.length()) {
                    featuresList.add(featArray.getString(i))
                }
            }

            val meta = json.optJSONObject("meta")
            val customer = meta?.optString("customer") ?: "N/A"
            val model = meta?.optString("model") ?: "N/A"

            LicensePayload(
                iss = json.optString("iss"),
                sub = json.optString("sub"),
                df = json.optString("df"),
                type = json.optString("type", "UNKNOWN"),
                iat = json.optLong("iat", 0L),
                exp = json.optLong("exp", 0L),
                features = featuresList,
                customer = customer,
                model = model
            )
        } catch (e: Exception) {
            return ValidationResult(
                status = LicenseStatus.INVALID_FORMAT,
                message = "Lỗi giải mã Payload JSON: ${e.message}"
            )
        }

        // 3. Giải mã Signature (Chữ ký 64 bytes)
        val signatureBytes = try {
            Base64.decode(signatureB64, Base64.URL_SAFE or Base64.NO_WRAP)
        } catch (e: Exception) {
            return ValidationResult(
                status = LicenseStatus.INVALID_FORMAT,
                message = "Lỗi giải mã Base64 chữ ký số."
            )
        }

        if (signatureBytes.size != 64) {
            return ValidationResult(
                status = LicenseStatus.INVALID_FORMAT,
                message = "Kích thước chữ ký Ed25519 không đúng (yêu cầu 64 bytes, thực tế: ${signatureBytes.size})."
            )
        }

        // ==============================================================
        // TẦNG 1: XÁC THỰC CHỮ KÝ ED25519 BẰNG TẦNG C++ NDK
        // ==============================================================
        val signingInputBytes = "$headerB64.$payloadB64".toByteArray(Charsets.UTF_8)
        val nativeVerifyCode = verifyNativeSignature(signingInputBytes, signatureBytes)
        if (nativeVerifyCode != 0) {
            return ValidationResult(
                status = LicenseStatus.INVALID_SIGNATURE,
                message = "Chữ ký số Ed25519 không hợp lệ! License đã bị chỉnh sửa hoặc giả mạo."
            )
        }

        // ==============================================================
        // TẦNG 2: SO KHỚP DEVICE FINGERPRINT PHẦN CỨNG THIẾT BỊ
        // ==============================================================
        val currentDeviceDetails = DeviceFingerprintManager.getDeviceDetails(context)
        val currentDfClean = cleanDf(currentDeviceDetails.dfCode)
        val licenseDfClean = cleanDf(payload.df)

        if (currentDfClean != licenseDfClean) {
            return ValidationResult(
                status = LicenseStatus.DEVICE_MISMATCH,
                message = "Mã thiết bị trong License (${payload.df}) không khớp với PDA này (${currentDeviceDetails.dfCode}). Không thể dùng chéo máy!",
                payload = payload
            )
        }

        // ==============================================================
        // TẦNG 3: ZERO TRUST TIME & CHỐNG GIAN LẬN LÙI THỜI GIAN
        // ==============================================================
        val nowSec = System.currentTimeMillis() / 1000
        val lastKnownTime = storage.getLastKnownTime()

        // Kiểm tra lùi giờ hệ thống: Giờ hiện tại bị chỉnh nhỏ hơn mốc đã ghi nhận trước đó
        if (lastKnownTime > 0 && nowSec < (lastKnownTime - CLOCK_TOLERANCE_SECONDS)) {
            val dateNow = formatEpoch(nowSec)
            val dateLast = formatEpoch(lastKnownTime)
            return ValidationResult(
                status = LicenseStatus.CLOCK_ROLLBACK_DETECTED,
                message = "Phát hiện gian lận lùi đồng hồ! Giờ hiện tại ($dateNow) nhỏ hơn lần sử dụng trước ($dateLast). Vui lòng đặt lại đúng giờ.",
                payload = payload
            )
        }

        // Kiểm tra thời gian hệ thống trước ngày cấp bản quyền
        if (nowSec < (payload.iat - CLOCK_TOLERANCE_SECONDS)) {
            return ValidationResult(
                status = LicenseStatus.NOT_YET_VALID,
                message = "Thời gian hệ thống (${formatEpoch(nowSec)}) trước ngày phát hành bản quyền (${formatEpoch(payload.iat)}).",
                payload = payload
            )
        }

        // Kiểm tra hết hạn
        if (nowSec > payload.exp) {
            return ValidationResult(
                status = LicenseStatus.EXPIRED,
                message = "Bản quyền đã hết hạn vào ngày ${formatEpoch(payload.exp)}.",
                payload = payload
            )
        }

        // Nếu tất cả các tầng phòng thủ đều vượt qua: Cập nhật mốc last_known_time
        storage.updateLastKnownTime(nowSec)

        return ValidationResult(
            status = LicenseStatus.VALID,
            message = "Bản quyền hợp lệ! Gói [${payload.type}] - Hạn đến: ${formatEpoch(payload.exp)}.",
            payload = payload
        )
    }

    private fun cleanDf(df: String): String {
        return df.trim().uppercase(Locale.US).replace("-", "").replace(" ", "")
    }

    private fun formatEpoch(epochSec: Long): String {
        val sdf = SimpleDateFormat("dd/MM/yyyy HH:mm:ss", Locale.getDefault())
        sdf.timeZone = TimeZone.getDefault()
        return sdf.format(Date(epochSec * 1000))
    }
}

