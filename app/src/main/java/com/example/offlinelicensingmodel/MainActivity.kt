package com.example.offlinelicensingmodel

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.graphics.Color
import android.os.Bundle
import android.view.inputmethod.EditorInfo
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.example.offlinelicensingmodel.databinding.ActivityMainBinding
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

    companion object {
        // Token mẫu demo cho thiết bị Newland MT90 vật lý (DF: MN73-006Q-5G96-S3E8)
        private const val DEMO_TOKEN_MT90 =
            "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJUYW5IdW5nSGEtT0xNIiwic3ViIjoiUERBLUxpY2Vuc2UiLCJkZiI6Ik1ONzMtMDA2US01Rzk2LVMzRTgiLCJ0eXBlIjoiUFJPIiwiaWF0IjoxNzkzNzYyNjc1LCJleHAiOjE4MjUyOTg2NzUsImZlYXR1cmVzIjpbIlNDQU5ORVIiLCJJTlZFTlRPUlkiLCJESVJFQ1RfUFJJTlQiXSwibWV0YSI6eyJjdXN0b21lciI6IlRcdTAwZTJuIEhcdTAxYjBuZyBIXHUwMGUwIC0gS2hcdTAwZTFjaCBIXHUwMGUwbmcgVGhcdTFlYWR0IiwibW9kZWwiOiJOTFMtTVQ5MCIsImlzc3VlZF9hdF91dGMiOiIyMDI2LTExLTA0IDAzOjI0OjM1IFVUQyIsImV4cGlyZXNfYXRfdXRjIjoiMjAyNy0xMS0wNCAwMzoyNDozNSBVVEMifX0.4uaCFEUgMUsbxgj60YWAg91spjrl3C53OpL0fk0RvqN5eS0QN87Q7fprkapwo6e9xoND6iuA_Px-hdZcxk6rDw"
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

        // 2. Nút kích hoạt tia laser quét mã vạch phần cứng
        binding.btnTriggerLaser.setOnClickListener {
            hardwareScanner.triggerHardwareScan()
            Toast.makeText(this, "Đang chiếu tia laser quét mã...", Toast.LENGTH_SHORT).show()
        }

        // 3. Nút kích hoạt bản quyền thủ công
        binding.btnActivate.setOnClickListener {
            val token = binding.edtLicenseToken.text.toString().trim()
            if (token.isEmpty()) {
                Toast.makeText(this, "Vui lòng nhập hoặc dán chuỗi License Token!", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }

            val result = validator.validateAndActivate(token)
            displayValidationResult(result)
        }

        // Xử lý tự kích hoạt khi đầu đọc ở chế độ bàn phím ảo (Keystroke Emulation)
        binding.edtLicenseToken.setOnEditorActionListener { _, actionId, _ ->
            if (actionId == EditorInfo.IME_ACTION_DONE || actionId == EditorInfo.IME_NULL) {
                val token = binding.edtLicenseToken.text.toString().trim()
                if (token.isNotEmpty()) {
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
            refreshLicenseStatus()
            checkAndDisplayRootStatus()
            Toast.makeText(this, "Đã cập nhật kiểm tra bản quyền!", Toast.LENGTH_SHORT).show()
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
        sb.append("DRM UNIQUE ID   : ${details.drmId}\n")
        sb.append("HÃNG SẢN XUẤT   : ${details.manufacturer}\n")
        sb.append("MODEL MÁY       : ${details.model}\n")
        sb.append("BO MẠCH (BOARD) : ${details.board}\n")
        sb.append("CHIP (HARDWARE) : ${details.hardware}\n")
        sb.append("CPU ABIs        : ${details.supportedAbis}\n")
        sb.append("MÀN HÌNH CHUẨN  : ${details.displayResolution}\n")
        sb.append("RAM ĐỊNH DANH   : ${details.totalRamGb} GB (Thực tế: ${details.actualRamMb} MB)\n")
        sb.append("SỐ CẢM BIẾN     : ${details.sensorCount} sensors\n")
        sb.append("HASH CẢM BIẾN   : ${details.sensorHash.take(16)}...\n")

        sb.append("\n=== THÔNG TIN CHẨN ĐOÁN (KHÔNG ĐƯA VÀO HASH DF) ===\n")
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
                binding.tvLicenseStatus.text = "HỢP LỆ (GÓI ${p.type})"
                binding.tvLicenseStatus.setTextColor(Color.parseColor("#2E7D32")) // Green

                val details = StringBuilder()
                details.append("Trạng thái: Hoạt động bình thường\n")
                details.append("Khách hàng: ${p.customer}\n")
                details.append("Model chỉ định: ${p.model}\n")
                details.append("Mã DF kích hoạt: ${p.df}\n")
                details.append("Ngày cấp: ${formatEpoch(p.iat)}\n")
                details.append("Hạn sử dụng: ${formatEpoch(p.exp)}\n")
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
}
