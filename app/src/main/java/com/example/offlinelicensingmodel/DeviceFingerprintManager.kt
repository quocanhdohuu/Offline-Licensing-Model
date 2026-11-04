package com.example.offlinelicensingmodel

import android.app.ActivityManager
import android.content.Context
import android.hardware.Sensor
import android.hardware.SensorManager
import android.media.MediaDrm
import android.os.Build
import android.os.StatFs
import android.util.DisplayMetrics
import android.view.WindowManager
import java.security.MessageDigest
import java.util.Locale
import java.util.UUID

/**
 * Quản lý và chuẩn hóa Device Fingerprint (DF) cho mô hình Offline Licensing Model (OLM).
 *
 * Tuân thủ nguyên tắc Zero Trust:
 * - Tier 1: Hardware DRM UUID (Lõi bất biến).
 * - Tier 2: Thuộc tính phần cứng tĩnh, màn hình chuẩn hóa xoay, RAM làm tròn mốc GB, cảm biến sorted hash.
 * - Tier 3: Loại bỏ Build.FINGERPRINT và dung lượng Storage khỏi hash định danh để kháng lỗi cập nhật OTA.
 * - Đầu ra: Mã 16 ký tự Crockford Base32 (80-bit entropy) định dạng XXXX-XXXX-XXXX-XXXX.
 */
object DeviceFingerprintManager {

    const val DEFAULT_SALT = "THH_OLM_SALT_SECURE_2026"
    private const val CROCKFORD_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

    data class DeviceDetails(
        val drmId: String,
        val manufacturer: String,
        val model: String,
        val board: String,
        val hardware: String,
        val supportedAbis: String,
        val displayResolution: String,
        val totalRamGb: Int,
        val actualRamMb: Long,
        val sensorCount: Int,
        val sensorHash: String,
        val sensorList: List<String>,
        val buildFingerprint: String, // Chỉ dùng chẩn đoán, không đưa vào hash DF
        val storageGb: Double,        // Chỉ dùng chẩn đoán
        val canonicalString: String,
        val fullSha256Hex: String,
        val dfCode: String
    )

    /**
     * Thu thập thông tin và sinh mã Device Fingerprint chuẩn hóa.
     */
    fun getDeviceDetails(context: Context, salt: String = DEFAULT_SALT): DeviceDetails {
        // 1. Tier 1 - MediaDrm Widevine UUID
        val drmId = getMediaDrmId()

        // 2. Tier 2 - Thông số cấu hình phần cứng tĩnh
        val manufacturer = Build.MANUFACTURER.trim().uppercase(Locale.US)
        val model = Build.MODEL.trim().uppercase(Locale.US)
        val board = Build.BOARD.trim().uppercase(Locale.US)
        val hardware = Build.HARDWARE.trim().uppercase(Locale.US)
        val supportedAbis = Build.SUPPORTED_ABIS.joinToString(",").uppercase(Locale.US)

        // Màn hình: chuẩn hóa không phụ thuộc góc xoay (min x max @ dpi)
        val wm = context.getSystemService(Context.WINDOW_SERVICE) as WindowManager
        val metrics = DisplayMetrics()
        @Suppress("DEPRECATION")
        wm.defaultDisplay.getRealMetrics(metrics)
        val minDim = kotlin.math.min(metrics.widthPixels, metrics.heightPixels)
        val maxDim = kotlin.math.max(metrics.widthPixels, metrics.heightPixels)
        val displayResolution = "${minDim}x${maxDim}@${metrics.densityDpi}"

        // RAM: Làm tròn lên mức GB gần nhất (MT90 ~ 3.8GB -> 4GB) để tránh lệch khi kernel thay đổi video memory
        val activityManager = context.getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager
        val memoryInfo = ActivityManager.MemoryInfo()
        activityManager.getMemoryInfo(memoryInfo)
        val actualRamMb = memoryInfo.totalMem / (1024 * 1024)
        val totalRamGb = kotlin.math.round(memoryInfo.totalMem.toDouble() / (1024.0 * 1024.0 * 1024.0)).toInt()

        // Cảm biến: Sắp xếp theo tên và băm SHA-256 danh sách để tạo giá trị định danh phần cứng cảm biến
        val sensorManager = context.getSystemService(Context.SENSOR_SERVICE) as SensorManager
        val sensors = sensorManager.getSensorList(Sensor.TYPE_ALL)
        val sensorNames = sensors.map { it.name.trim() }.sorted()
        val sensorHash = sha256Hex(sensorNames.joinToString(","))

        // 3. Thông tin chẩn đoán (Diagnostic only - không cho vào hash DF)
        val buildFingerprint = Build.FINGERPRINT
        val statFs = StatFs(context.filesDir.path)
        val storageGb = statFs.totalBytes / (1024.0 * 1024.0 * 1024.0)

        // 4. Ghép chuỗi chuẩn tắc Canonical String
        val canonicalString = "DRM=$drmId" +
                "|MF=$manufacturer" +
                "|MD=$model" +
                "|BOARD=$board" +
                "|HW=$hardware" +
                "|ABI=$supportedAbis" +
                "|DISP=$displayResolution" +
                "|RAM=${totalRamGb}GB" +
                "|SNS=$sensorHash" +
                "|SALT=$salt"

        // 5. Băm SHA-256
        val digest = MessageDigest.getInstance("SHA-256")
        val sha256Bytes = digest.digest(canonicalString.toByteArray(Charsets.UTF_8))
        val fullSha256Hex = sha256Bytes.joinToString("") { "%02X".format(it) }

        // 6. Lấy 10 bytes đầu tiên (80 bits) và mã hóa Crockford Base32 (16 ký tự)
        val rawBase32 = encodeCrockfordBase32(sha256Bytes.copyOfRange(0, 10))
        val dfCode = formatDfCode(rawBase32)

        return DeviceDetails(
            drmId = drmId,
            manufacturer = manufacturer,
            model = model,
            board = board,
            hardware = hardware,
            supportedAbis = supportedAbis,
            displayResolution = displayResolution,
            totalRamGb = totalRamGb,
            actualRamMb = actualRamMb,
            sensorCount = sensors.size,
            sensorHash = sensorHash,
            sensorList = sensorNames,
            buildFingerprint = buildFingerprint,
            storageGb = storageGb,
            canonicalString = canonicalString,
            fullSha256Hex = fullSha256Hex,
            dfCode = dfCode
        )
    }

    /**
     * Lấy MediaDrm Unique ID (Widevine Lõi phần cứng).
     */
    private fun getMediaDrmId(): String {
        val widevineUuid = UUID.fromString("edef8ba9-79d6-4ace-a3c8-27dcd51d21ed")
        if (!MediaDrm.isCryptoSchemeSupported(widevineUuid)) {
            // Fallback an toàn nếu máy không có Widevine (rất hiếm trên PDA Android 10+)
            return "FALLBACK-NOWIDEVINE"
        }

        var drm: MediaDrm? = null
        return try {
            drm = MediaDrm(widevineUuid)
            val deviceId = drm.getPropertyByteArray(MediaDrm.PROPERTY_DEVICE_UNIQUE_ID)
            deviceId.joinToString("") { "%02X".format(it.toInt() and 0xFF) }
        } catch (e: Exception) {
            "ERR-${e.javaClass.simpleName.uppercase(Locale.US)}"
        } finally {
            try {
                drm?.release()
            } catch (_: Exception) { }
        }
    }

    /**
     * Mã hóa mảng bytes sang chuỗi Crockford Base32.
     * 10 bytes = 80 bits = 16 ký tự 5-bit.
     */
    private fun encodeCrockfordBase32(data: ByteArray): String {
        val result = StringBuilder()
        var buffer = 0L
        var bitsLeft = 0

        for (b in data) {
            buffer = (buffer shl 8) or (b.toLong() and 0xFF)
            bitsLeft += 8
            while (bitsLeft >= 5) {
                val index = ((buffer ushr (bitsLeft - 5)) and 0x1F).toInt()
                result.append(CROCKFORD_ALPHABET[index])
                bitsLeft -= 5
            }
        }

        if (bitsLeft > 0) {
            val index = ((buffer shl (5 - bitsLeft)) and 0x1F).toInt()
            result.append(CROCKFORD_ALPHABET[index])
        }

        return result.toString()
    }

    /**
     * Định dạng chuỗi 16 ký tự thành dạng XXXX-XXXX-XXXX-XXXX để tiện đọc và nhập liệu.
     */
    private fun formatDfCode(raw16: String): String {
        val padded = raw16.padEnd(16, '0').take(16)
        return listOf(
            padded.substring(0, 4),
            padded.substring(4, 8),
            padded.substring(8, 12),
            padded.substring(12, 16)
        ).joinToString("-")
    }

    private fun sha256Hex(input: String): String {
        val digest = MessageDigest.getInstance("SHA-256")
        val hash = digest.digest(input.toByteArray(Charsets.UTF_8))
        return hash.joinToString("") { "%02X".format(it) }
    }
}

