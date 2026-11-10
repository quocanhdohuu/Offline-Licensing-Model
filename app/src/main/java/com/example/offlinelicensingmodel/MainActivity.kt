package com.example.offlinelicensingmodel

import android.Manifest
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.pm.PackageManager
import android.graphics.Color
import android.os.Bundle
import android.view.inputmethod.EditorInfo
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import com.example.offlinelicensingmodel.databinding.ActivityMainBinding
import com.journeyapps.barcodescanner.ScanContract
import com.journeyapps.barcodescanner.ScanOptions
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.TimeZone

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private lateinit var validator: LicenseValidator
    private lateinit var storage: LicenseStorage
    private lateinit var rootChecker: RootChecker
    private lateinit var hardwareScanner: HardwareScannerManager

    // Bộ khởi chạy giao diện quét mã QR bằng Camera (ZXing 100% Offline)
    private val qrScannerLauncher = registerForActivityResult(ScanContract()) { result ->
        if (result.contents != null) {
            val scannedToken = result.contents.trim()
            binding.edtLicenseToken.setText(scannedToken)
            val res = validator.validateAndActivate(scannedToken)
            displayValidationResult(res)
            Toast.makeText(this, "Camera: ${res.message}", Toast.LENGTH_SHORT).show()
        }
    }

    // Bộ xin cấp quyền Camera thời gian thực (Runtime Permission)
    private val cameraPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { isGranted: Boolean ->
        if (isGranted) {
            startCameraScanner()
        } else {
            Toast.makeText(this, "Cần cấp quyền Camera để quét mã QR License!", Toast.LENGTH_LONG).show()
        }
    }

    companion object {
        // Token mẫu demo cho thiết bị Newland MT90 vật lý (DF chuẩn kháng Factory Reset: 8ZRB-JNNA-TXYP-K7V9)
        private const val DEMO_TOKEN_MT90 =
            "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJUYW5IdW5nSGEtT0xNIiwic3ViIjoiUERBLUxpY2Vuc2UiLCJkZiI6IjhaUkItSk5OQS1UWFlQLUs3VjkiLCJ0eXBlIjoiUFJPIiwiaWF0IjoxNzkzODQ3MzU1LCJleHAiOjE4MjUzODMzNTUsImZlYXR1cmVzIjpbIlNDQU5ORVIiLCJJTlZFTlRPUlkiLCJESVJFQ1RfUFJJTlQiXSwibWV0YSI6eyJjdXN0b21lciI6IlRhbiBIdW5nIEhhIC0gUmVhbCBNVDkwIChGYWN0b3J5IFJlc2V0IFJlc2lzdGFudCkiLCJtb2RlbCI6Ik5MUy1NVDkwIiwiaXNzdWVkX2F0X3V0YyI6IjIwMjYtMTEtMDUgMDI6NTU6NTUgVVRDIiwiZXhwaXJlc19hdF91dGMiOiIyMDI3LTExLTA1IDAyOjU1OjU1IFVUQyJ9fQ.W7rUwsZHjYGf_CgHxFV74r2IItehUuo0YldOHtzCOOfXQAKpl5V4H3eqpdZUsC3gTXBMdSH-atQKkNB6u7OZCw"
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        validator = LicenseValidator(this)
        storage = LicenseStorage(this)
        rootChecker = RootChecker(this)

        // Khởi tạo bộ thu phát đầu đọc quét mã phần cứng Newland MT90
        hardwareScanner = HardwareScannerManager(this) { barcode ->
            runOnUiThread {
                binding.edtLicenseToken.setText(barcode)
                val res = validator.validateAndActivate(barcode)
                displayValidationResult(res)
                Toast.makeText(this, "Đầu đọc MT90: ${res.message}", Toast.LENGTH_SHORT).show()
            }
        }

        initViews()
        loadDeviceFingerprint()
        checkAndDisplayRootStatus()

        val testTokenExtra = intent.getStringExtra("ACTIVATE_TOKEN")
        if (!testTokenExtra.isNullOrEmpty()) {
            val res = validator.validateAndActivate(testTokenExtra)
            displayValidationResult(res)
            android.util.Log.d("OLM_DF", "INTENT_ACTIVATION_RESULT: ${res.status} - ${res.message}")
        } else {
            refreshLicenseStatus()
        }
    }

    override fun onResume() {
        super.onResume()
        hardwareScanner.startListening()
        checkAndDisplayRootStatus()
    }

    override fun onPause() {
        super.onPause()
        hardwareScanner.stopListening()
    }

    private fun checkAndDisplayRootStatus() {
        val rootStatus = rootChecker.checkRoot()
        if (rootStatus.isRooted) {
            binding.tvRootSecurityStatus.text = "BẢO MẬT: CẢNH BÁO MÁY ĐÃ ROOT! (${rootStatus.details})"
            binding.tvRootSecurityStatus.setTextColor(Color.parseColor("#B71C1C"))
            binding.tvRootSecurityStatus.setBackgroundColor(Color.parseColor("#FFEBEE"))
        } else {
            binding.tvRootSecurityStatus.text = "BẢO MẬT HỆ THỐNG: THIẾT BỊ AN TOÀN (NON-ROOT)"
            binding.tvRootSecurityStatus.setTextColor(Color.parseColor("#2E7D32"))
            binding.tvRootSecurityStatus.setBackgroundColor(Color.parseColor("#E8F5E9"))
        }
    }

    private fun initViews() {
        // 1. Nút sao chép mã DF
        binding.btnCopyDf.setOnClickListener {
            val df = binding.tvDfCode.text.toString()
            val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
            val clip = ClipData.newPlainText("Device Fingerprint", df)
            clipboard.setPrimaryClip(clip)
            Toast.makeText(this, "Đã sao chép mã DF: $df", Toast.LENGTH_SHORT).show()
        }

        // 2. Nút kích hoạt tia laser quét mã vạch phần cứng (Newland MT90)
        binding.btnTriggerLaser.setOnClickListener {
            hardwareScanner.triggerHardwareScan()
            Toast.makeText(this, "Đang chiếu tia laser quét mã...", Toast.LENGTH_SHORT).show()
        }

        // 2b. Nút kích hoạt Camera quét mã QR (Hỗ trợ máy không có laser)
        binding.btnScanCamera.setOnClickListener {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) {
                startCameraScanner()
            } else {
                cameraPermissionLauncher.launch(Manifest.permission.CAMERA)
            }
        }

        // 3. Nút kích hoạt bản quyền thủ công
        binding.btnActivate.setOnClickListener {
            val rawText = binding.edtLicenseToken.text.toString().trim()
            if (rawText.isEmpty()) {
                Toast.makeText(this, "Vui lòng nhập hoặc dán chuỗi License Token!", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }

            // Nếu đầu đọc bàn phím ảo quét nối đuôi vào mã cũ, tự động trích xuất JWT mới nhất
            val lastJwtIdx = rawText.lastIndexOf("eyJ")
            val token = if (lastJwtIdx > 0) rawText.substring(lastJwtIdx).trim() else rawText
            if (lastJwtIdx > 0) {
                binding.edtLicenseToken.setText(token)
            }

            val result = validator.validateAndActivate(token)
            displayValidationResult(result)
        }

        // Xử lý tự kích hoạt khi đầu đọc ở chế độ bàn phím ảo (Keystroke Emulation)
        binding.edtLicenseToken.setOnEditorActionListener { _, actionId, _ ->
            if (actionId == EditorInfo.IME_ACTION_DONE || actionId == EditorInfo.IME_NULL) {
                val rawText = binding.edtLicenseToken.text.toString().trim()
                if (rawText.isNotEmpty()) {
                    val lastJwtIdx = rawText.lastIndexOf("eyJ")
                    val token = if (lastJwtIdx > 0) rawText.substring(lastJwtIdx).trim() else rawText
                    if (lastJwtIdx > 0) {
                        binding.edtLicenseToken.setText(token)
                    }
                    val result = validator.validateAndActivate(token)
                    displayValidationResult(result)
                }
                true
            } else {
                false
            }
        }

        // 4. Nút nạp chuỗi Token Demo
        binding.btnLoadDemo.setOnClickListener {
            binding.edtLicenseToken.setText(DEMO_TOKEN_MT90)
            Toast.makeText(this, "Đã nạp chuỗi Token mẫu MT90 vào ô nhập!", Toast.LENGTH_SHORT).show()
        }

        // 5. Nút kiểm tra lại trạng thái bản quyền
        binding.btnReverify.setOnClickListener {
            val currentToken = binding.edtLicenseToken.text.toString().trim()
            if (currentToken.isNotEmpty()) {
                // Ưu tiên thẩm định lại chuỗi Token đang hiển thị trong ô nhập (đảm bảo tính nhất quán khi test Case 1, 2, 3, 4)
                val result = validator.validateToken(currentToken)
                displayValidationResult(result)
                Toast.makeText(this, "Đã kiểm tra lại mã trên màn hình: ${result.status}", Toast.LENGTH_SHORT).show()
            } else {
                // Nếu ô nhập trống, thẩm định lại bản quyền đã lưu trong máy
                refreshLicenseStatus()
                Toast.makeText(this, "Đã kiểm tra lại bản quyền lưu trong máy!", Toast.LENGTH_SHORT).show()
            }
            checkAndDisplayRootStatus()
        }

        // 6. Nút xóa bản quyền (Reset)
        binding.btnResetLicense.setOnClickListener {
            storage.clearLicense()
            binding.edtLicenseToken.setText("")
            refreshLicenseStatus()
            Toast.makeText(this, "Đã xóa bản quyền lưu trên máy!", Toast.LENGTH_SHORT).show()
        }
    }

    private fun loadDeviceFingerprint() {
        val details = DeviceFingerprintManager.getDeviceDetails(this)
        android.util.Log.d("OLM_DF", "ACTUAL_PDA_DF: ${details.dfCode}")
        binding.tvDfCode.text = details.dfCode

        val sb = StringBuilder()
        sb.append("=== THÔNG SỐ PHẦN CỨNG CHUẨN HÓA ===\n")
        sb.append("MÃ DF (16 chars): ${details.dfCode}\n")
        sb.append("HARDWARE SERIAL : ${details.serial}\n")
        sb.append("HÃNG SẢN XUẤT   : ${details.manufacturer}\n")
        sb.append("MODEL MÁY       : ${details.model}\n")
        sb.append("BO MẠCH (BOARD) : ${details.board}\n")
        sb.append("CHIP (HARDWARE) : ${details.hardware}\n")
        sb.append("CPU ABIs        : ${details.supportedAbis}\n")
        sb.append("MÀN HÌNH CHUẨN  : ${details.displayResolution}\n")
        sb.append("RAM ĐỊNH DANH   : ${details.totalRamGb} GB (Thực tế: ${details.actualRamMb} MB)\n")

        sb.append("\n=== THÔNG TIN CHẨN ĐOÁN (KHÔNG ĐƯA VÀO HASH DF) ===\n")
        sb.append("DRM UNIQUE ID   : ${details.drmId}\n")
        sb.append("SỐ CẢM BIẾN     : ${details.sensorCount} sensors\n")
        sb.append("HASH CẢM BIẾN   : ${details.sensorHash.take(16)}...\n")
        sb.append("BUILD ROM       : ${details.buildFingerprint}\n")
        sb.append("BỘ NHỚ LƯU TRỮ  : %.2f GB\n".format(details.storageGb))

        sb.append("\n=== CANONICAL STRING TRƯỚC KHI BĂM ===\n")
        sb.append("${details.canonicalString}\n")

        sb.append("\n=== SHA-256 HASH (256-BIT) ===\n")
        sb.append("${details.fullSha256Hex}\n")

        binding.sampleText.text = sb.toString()
    }

    private fun refreshLicenseStatus() {
        val result = validator.validateSavedLicense()
        android.util.Log.d("OLM_DF", "SAVED_LICENSE_STATUS: ${result.status} - ${result.message}")
        displayValidationResult(result)
    }

    private fun displayValidationResult(result: LicenseValidator.ValidationResult) {
        when (result.status) {
            LicenseValidator.LicenseStatus.VALID -> {
                val p = result.payload!!
                val statusLabel = if (p.isPermanent && !p.type.contains("VĨNH VIỄN")) {
                    "HỢP LỆ (GÓI ${p.type} VĨNH VIỄN)"
                } else {
                    "HỢP LỆ (GÓI ${p.type})"
                }
                binding.tvLicenseStatus.text = statusLabel
                binding.tvLicenseStatus.setTextColor(Color.parseColor("#2E7D32")) // Green

                val expDisplay = if (p.isPermanent) "VĨNH VIỄN (Không thời hạn)" else formatEpoch(p.exp)
                val details = StringBuilder()
                details.append("Trạng thái: Hoạt động bình thường (v${p.version})\n")
                details.append("Khách hàng: ${p.customer}\n")
                details.append("Model chỉ định: ${p.model}\n")
                details.append("Mã DF kích hoạt: ${p.df}\n")
                details.append("Ngày cấp: ${formatEpoch(p.iat)}\n")
                details.append("Hạn sử dụng: $expDisplay\n")
                details.append("Tính năng mở: ${p.features.joinToString(", ")}")
                binding.tvLicenseDetails.text = details.toString()
            }
            LicenseValidator.LicenseStatus.ROOT_DEVICE_DETECTED -> {
                binding.tvLicenseStatus.text = "TỪ CHỐI: MÁY ĐÃ ROOT"
                binding.tvLicenseStatus.setTextColor(Color.parseColor("#B71C1C"))
                binding.tvLicenseDetails.text = result.message
            }
            LicenseValidator.LicenseStatus.DEVICE_MISMATCH -> {
                binding.tvLicenseStatus.text = "SAI THIẾT BỊ (DEVICE MISMATCH)"
                binding.tvLicenseStatus.setTextColor(Color.parseColor("#E65100")) // Orange
                binding.tvLicenseDetails.text = result.message
            }
            LicenseValidator.LicenseStatus.INVALID_SIGNATURE -> {
                binding.tvLicenseStatus.text = "CHỮ KÝ KHÔNG HỢP LỆ / FAKE"
                binding.tvLicenseStatus.setTextColor(Color.parseColor("#C53030")) // Red
                binding.tvLicenseDetails.text = result.message
            }
            LicenseValidator.LicenseStatus.EXPIRED -> {
                binding.tvLicenseStatus.text = "BẢN QUYỀN ĐÃ HẾT HẠN"
                binding.tvLicenseStatus.setTextColor(Color.parseColor("#C53030")) // Red
                binding.tvLicenseDetails.text = result.message
            }
            LicenseValidator.LicenseStatus.CLOCK_ROLLBACK_DETECTED -> {
                binding.tvLicenseStatus.text = "GIAN LẬN LÙI ĐỒNG HỒ!"
                binding.tvLicenseStatus.setTextColor(Color.parseColor("#B71C1C")) // Dark Red
                binding.tvLicenseDetails.text = result.message
            }
            LicenseValidator.LicenseStatus.NOT_YET_VALID -> {
                binding.tvLicenseStatus.text = "CHƯA ĐẾN NGÀY HIỆU LỰC"
                binding.tvLicenseStatus.setTextColor(Color.parseColor("#E65100"))
                binding.tvLicenseDetails.text = result.message
            }
            LicenseValidator.LicenseStatus.INVALID_FORMAT -> {
                binding.tvLicenseStatus.text = "CHƯA KÍCH HOẠT"
                binding.tvLicenseStatus.setTextColor(Color.parseColor("#718096")) // Gray
                binding.tvLicenseDetails.text = result.message
            }
        }
    }

    private fun formatEpoch(epochSec: Long): String {
        val sdf = SimpleDateFormat("dd/MM/yyyy HH:mm:ss", Locale.getDefault())
        sdf.timeZone = TimeZone.getDefault()
        return sdf.format(Date(epochSec * 1000))
    }

    /**
     * Mở giao diện Camera quét mã QR License (sử dụng thư viện ZXing Android Embedded 100% Offline).
     */
    private fun startCameraScanner() {
        val options = ScanOptions().apply {
            setDesiredBarcodeFormats(ScanOptions.QR_CODE)
            setPrompt("Hướng camera vào mã QR License để tự động kích hoạt")
            setCameraId(0) // Sử dụng camera sau
            setBeepEnabled(true)
            setBarcodeImageEnabled(false)
            setOrientationLocked(false)
        }
        qrScannerLauncher.launch(options)
    }
}
