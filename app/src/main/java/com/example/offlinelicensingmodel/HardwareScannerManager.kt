package com.example.offlinelicensingmodel

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.Build
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.util.Log

/**
 * Quản lý cụm mắt quét laser / 2D phần cứng chuyên dụng trên PDA Newland NLS-MT90.
 *
 * Tương tác qua hệ thống Broadcast Intent của Newland Barcode Service:
 * - Nhận kết quả quét: action "nlscan.action.SCANNER_RESULT", extra "SCAN_BARCODE1".
 * - Bật tia quét laser mềm: broadcast action "nlscan.action.SCANNER_TRIG".
 */
class HardwareScannerManager(
    private val context: Context,
    private val onBarcodeScanned: (String) -> Unit
) {

    companion object {
        private const val TAG = "HardwareScanner"

        // Newland MT90 Actions & Extras
        const val ACTION_SCANNER_RESULT = "nlscan.action.SCANNER_RESULT"
        const val EXTRA_SCAN_BARCODE1 = "SCAN_BARCODE1"
        const val EXTRA_SCAN_STATE = "SCAN_STATE"
        const val ACTION_SCANNER_TRIG = "nlscan.action.SCANNER_TRIG"

        // Fallback generic OEM actions
        private const val ACTION_GENERIC_SCAN = "scan.rcv.message"
    }

    private var isRegistered = false

    private val scanReceiver = object : BroadcastReceiver() {
        override fun onReceive(ctx: Context?, intent: Intent?) {
            if (intent == null) return
            val action = intent.action

            if (action == ACTION_SCANNER_RESULT || action == ACTION_GENERIC_SCAN) {
                // 1. Thử đọc chuỗi ký tự String
                var barcode = intent.getStringExtra(EXTRA_SCAN_BARCODE1)

                // 2. Fallback nếu Newland trả về mảng bytes
                if (barcode.isNullOrEmpty()) {
                    val barcodeBytes = intent.getByteArrayExtra(EXTRA_SCAN_BARCODE1)
                    if (barcodeBytes != null && barcodeBytes.isNotEmpty()) {
                        barcode = String(barcodeBytes, Charsets.UTF_8).trim()
                    }
                }

                // 3. Fallback cho các dòng máy OEM khác
                if (barcode.isNullOrEmpty()) {
                    barcode = intent.getStringExtra("barcode_string")
                        ?: intent.getStringExtra("data")
                        ?: intent.getStringExtra("scan_result")
                }

                if (!barcode.isNullOrEmpty()) {
                    val cleanBarcode = barcode.trim()
                    Log.d(TAG, "Nhận mã vạch từ đầu đọc phần cứng: $cleanBarcode")
                    vibrateFeedback()
                    onBarcodeScanned(cleanBarcode)
                }
            }
        }
    }

    /**
     * Đăng ký lắng nghe sự kiện quét từ phần cứng khi Activity hiển thị (onResume).
     */
    fun startListening() {
        if (!isRegistered) {
            val filter = IntentFilter().apply {
                addAction(ACTION_SCANNER_RESULT)
                addAction(ACTION_GENERIC_SCAN)
            }
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                context.registerReceiver(scanReceiver, filter, Context.RECEIVER_EXPORTED)
            } else {
                context.registerReceiver(scanReceiver, filter)
            }
            isRegistered = true
            Log.d(TAG, "Đã đăng ký lắng nghe mắt quét phần cứng Newland MT90.")
        }
    }

    /**
     * Hủy đăng ký lắng nghe khi Activity tạm dừng (onPause) để tiết kiệm pin.
     */
    fun stopListening() {
        if (isRegistered) {
            try {
                context.unregisterReceiver(scanReceiver)
            } catch (e: Exception) {
                Log.w(TAG, "Lỗi hủy receiver: ${e.message}")
            }
            isRegistered = false
            Log.d(TAG, "Đã dừng lắng nghe mắt quét phần cứng.")
        }
    }

    /**
     * Bật tia sáng quét laser của máy bằng phần mềm (Software Trigger).
     */
    fun triggerHardwareScan() {
        val triggerIntent = Intent(ACTION_SCANNER_TRIG)
        context.sendBroadcast(triggerIntent)
        Log.d(TAG, "Đã gửi lệnh kích hoạt tia laser quét phần cứng.")
    }

    /**
     * Rung nhẹ phản hồi xúc giác khi đọc thành công mã.
     */
    private fun vibrateFeedback() {
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                val vm = context.getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as VibratorManager
                vm.defaultVibrator.vibrate(VibrationEffect.createOneShot(100, VibrationEffect.DEFAULT_AMPLITUDE))
            } else {
                @Suppress("DEPRECATION")
                val v = context.getSystemService(Context.VIBRATOR_SERVICE) as Vibrator
                @Suppress("DEPRECATION")
                v.vibrate(100)
            }
        } catch (_: Exception) { }
    }
}

