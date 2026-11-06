package com.example.offlinelicensingmodel

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.Build
import android.os.Bundle
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.util.Log

/**
 * Quản lý cụm mắt quét laser / 2D phần cứng chuyên dụng đa năng (Universal Hardware Scanner).
 *
 * Tự động hỗ trợ các dòng máy PDA công nghiệp phổ biến trên thị trường:
 * - Newland (NLS-MT90, N7, v.v.): nlscan.action.SCANNER_RESULT
 * - Zebra Technologies (TC21, TC26, TC52, TC57, MC3300...): Zebra DataWedge API
 * - Honeywell (ScanPal, Dolphin, EDA series): com.honeywell.decode.intent.action.SCAN_RESULT
 * - Urovo / Point Mobile / Datalogic / Generic OEMs
 */
class HardwareScannerManager(
    private val context: Context,
    private val onBarcodeScanned: (String) -> Unit
) {

    companion object {
        private const val TAG = "HardwareScanner"

        // 1. Newland MT90 Actions & Extras
        const val ACTION_NEWLAND_RESULT = "nlscan.action.SCANNER_RESULT"
        const val EXTRA_NEWLAND_BARCODE = "SCAN_BARCODE1"
        const val ACTION_NEWLAND_TRIG = "nlscan.action.SCANNER_TRIG"
        const val ACTION_NEWLAND_CONFIG = "ACTION_BAR_SCANCFG"
        const val EXTRA_NEWLAND_SCAN_MODE = "EXTRA_SCAN_MODE"
        const val EXTRA_NEWLAND_TRIG_MODE = "EXTRA_TRIG_MODE"
        const val EXTRA_NEWLAND_SCAN_POWER = "EXTRA_SCAN_POWER"

        // 2. Zebra DataWedge Actions & Extras
        const val ACTION_ZEBRA_SCAN = "com.symbol.datawedge.ACTION"
        const val ACTION_ZEBRA_SCAN_ALT = "com.symbol.datawedge.action.ACTION"
        const val ACTION_ZEBRA_BARCODE = "com.zebra.action.BARCODE"
        const val ACTION_ZEBRA_DW_EXAMPLE = "com.dwexample.ACTION"
        const val EXTRA_ZEBRA_DATA = "com.symbol.datawedge.data_string"
        const val EXTRA_ZEBRA_DATA_ALT = "data_string"
        const val ACTION_ZEBRA_API = "com.symbol.datawedge.api.ACTION"

        // 3. Honeywell Actions & Extras
        const val ACTION_HONEYWELL_RESULT = "com.honeywell.decode.intent.action.SCAN_RESULT"
        const val EXTRA_HONEYWELL_DATA = "data"
        const val ACTION_HONEYWELL_TRIG = "com.honeywell.decode.intent.action.SCAN_CONTROL"

        // 4. Urovo & Datalogic & Generic OEM Actions
        const val ACTION_UROVO_SCAN = "android.intent.ACTION_DECODE_DATA"
        const val ACTION_DATALOGIC_SCAN = "com.datalogic.decodewedge.decode_action"
        const val ACTION_GENERIC_SCAN = "scan.rcv.message"
    }

    private var isRegistered = false

    private val scanReceiver = object : BroadcastReceiver() {
        override fun onReceive(ctx: Context?, intent: Intent?) {
            if (intent == null) return
            val action = intent.action ?: return
            Log.d(TAG, "Nhận Broadcast Intent từ phần cứng quét: $action")

            var barcode: String? = null

            // 1. Kiểm tra định dạng Zebra DataWedge
            barcode = intent.getStringExtra(EXTRA_ZEBRA_DATA)
                ?: intent.getStringExtra(EXTRA_ZEBRA_DATA_ALT)

            // 2. Kiểm tra định dạng Newland
            if (barcode.isNullOrEmpty()) {
                barcode = intent.getStringExtra(EXTRA_NEWLAND_BARCODE)
                if (barcode.isNullOrEmpty()) {
                    val barcodeBytes = intent.getByteArrayExtra(EXTRA_NEWLAND_BARCODE)
                    if (barcodeBytes != null && barcodeBytes.isNotEmpty()) {
                        barcode = String(barcodeBytes, Charsets.UTF_8).trim()
                    }
                }
            }

            // 3. Kiểm tra định dạng Honeywell
            if (barcode.isNullOrEmpty()) {
                barcode = intent.getStringExtra(EXTRA_HONEYWELL_DATA)
            }

            // 4. Kiểm tra các dòng máy OEM khác (Urovo, Datalogic, Generic)
            if (barcode.isNullOrEmpty()) {
                barcode = intent.getStringExtra("barcode_string")
                    ?: intent.getStringExtra("barcode")
                    ?: intent.getStringExtra("msg_data")
                    ?: intent.getStringExtra("scan_result")
                    ?: intent.getStringExtra("value")
            }

            if (!barcode.isNullOrEmpty()) {
                val cleanBarcode = barcode.trim()
                Log.d(TAG, "Trích xuất thành công mã từ đầu đọc phần cứng [$action]: $cleanBarcode")
                vibrateFeedback()
                onBarcodeScanned(cleanBarcode)
            }
        }
    }

    /**
     * Đăng ký lắng nghe sự kiện quét từ phần cứng khi Activity hiển thị (onResume).
     * Hỗ trợ đồng thời Newland, Zebra DataWedge, Honeywell, Urovo, Datalogic.
     */
    fun startListening() {
        if (!isRegistered) {
            val filter = IntentFilter().apply {
                // Newland
                addAction(ACTION_NEWLAND_RESULT)
                // Zebra DataWedge
                addAction(ACTION_ZEBRA_SCAN)
                addAction(ACTION_ZEBRA_SCAN_ALT)
                addAction(ACTION_ZEBRA_BARCODE)
                addAction(ACTION_ZEBRA_DW_EXAMPLE)
                // Honeywell
                addAction(ACTION_HONEYWELL_RESULT)
                // Urovo & Datalogic & Generic
                addAction(ACTION_UROVO_SCAN)
                addAction(ACTION_DATALOGIC_SCAN)
                addAction(ACTION_GENERIC_SCAN)
            }

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                context.registerReceiver(scanReceiver, filter, Context.RECEIVER_EXPORTED)
            } else {
                context.registerReceiver(scanReceiver, filter)
            }
            isRegistered = true

            // Tự động cấu hình mắt quét trên Newland MT90 và Zebra DataWedge
            autoConfigureNewlandScanner()
            autoConfigureZebraDataWedge()

            Log.d(TAG, "Đã kích hoạt bộ lắng nghe Universal Scanner (Zebra, Newland, Honeywell).")
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
     * Bắn tín hiệu trigger tương ứng cho cả Newland, Zebra và Honeywell.
     */
    fun triggerHardwareScan() {
        try {
            // 1. Kích hoạt Newland MT90
            // Đảm bảo bật nguồn động cơ giải mã và cấu hình API Broadcast mode
            val newlandPower = Intent(ACTION_NEWLAND_CONFIG).apply {
                putExtra(EXTRA_NEWLAND_SCAN_MODE, 3)   // API Broadcast mode
                putExtra(EXTRA_NEWLAND_TRIG_MODE, 0)   // Trigger mode
                putExtra(EXTRA_NEWLAND_SCAN_POWER, 1)  // Bật nguồn mắt quét
            }
            context.sendBroadcast(newlandPower)

            val newlandTrigger = Intent(ACTION_NEWLAND_TRIG).apply {
                putExtra("SCAN_TIMEOUT", 4)
                putExtra("SCAN_STATE", 1)
            }
            context.sendBroadcast(newlandTrigger)

            // Dự phòng trigger action phụ của Newland
            context.sendBroadcast(Intent("nlscan.action.START_SCAN"))

            // 2. Kích hoạt Zebra DataWedge Soft Scan Trigger
            val zebraTrigger = Intent(ACTION_ZEBRA_API).apply {
                putExtra("com.symbol.datawedge.api.SOFT_SCAN_TRIGGER", "START_SCANNING")
            }
            context.sendBroadcast(zebraTrigger)

            // 3. Kích hoạt Honeywell Scan Control
            val honeywellTrigger = Intent(ACTION_HONEYWELL_TRIG).apply {
                putExtra("com.honeywell.decode.intent.extra.SCAN_COMMAND", 1)
            }
            context.sendBroadcast(honeywellTrigger)

            Log.d(TAG, "Đã phát lệnh kích hoạt tia quét phần cứng (Newland / Zebra / Honeywell).")
        } catch (e: Exception) {
            Log.w(TAG, "Lỗi kích hoạt tia quét: ${e.message}")
        }
    }

    /**
     * Tự động cấu hình mắt quét phần cứng trên dòng Newland MT90 qua ACTION_BAR_SCANCFG:
     * - EXTRA_SCAN_MODE = 3 (Chế độ Broadcast Intent API)
     * - EXTRA_TRIG_MODE = 0 (Chế độ bấm cò / kích hoạt phần mềm)
     * - EXTRA_SCAN_POWER = 1 (Bật nguồn module phần cứng mắt quét)
     */
    private fun autoConfigureNewlandScanner() {
        try {
            val configIntent = Intent(ACTION_NEWLAND_CONFIG).apply {
                putExtra(EXTRA_NEWLAND_SCAN_MODE, 3)
                putExtra(EXTRA_NEWLAND_TRIG_MODE, 0)
                putExtra(EXTRA_NEWLAND_SCAN_POWER, 1)
            }
            context.sendBroadcast(configIntent)
            Log.d(TAG, "Đã gửi cấu hình tự động cho Newland MT90 Scan Engine.")
        } catch (e: Exception) {
            Log.w(TAG, "Không thể gửi cấu hình Newland: ${e.message}")
        }
    }

    /**
     * Tự động đăng ký Profile "OfflineLicensing" trên Zebra DataWedge qua Broadcast Intent.
     * Giúp máy Zebra tự động chuyển sang chế độ Broadcast Intent mà người dùng không cần chỉnh tay.
     */
    private fun autoConfigureZebraDataWedge() {
        try {
            val profileName = "OfflineLicensing"

            // 1. Tạo Profile nếu chưa tồn tại
            val createIntent = Intent(ACTION_ZEBRA_API).apply {
                putExtra("com.symbol.datawedge.api.CREATE_PROFILE", profileName)
            }
            context.sendBroadcast(createIntent)

            // 2. Gán Profile này cho ứng dụng và cấu hình Intent Output
            val profileConfig = Bundle().apply {
                putString("PROFILE_NAME", profileName)
                putString("PROFILE_ENABLED", "true")
                putString("CONFIG_MODE", "UPDATE")

                // Liên kết với package của app
                val appConfig = Bundle().apply {
                    putString("PACKAGE_NAME", context.packageName)
                    putStringArray("ACTIVITY_LIST", arrayOf("*"))
                }
                putParcelableArray("APP_LIST", arrayOf(appConfig))

                // Cấu hình Plugin INTENT Output
                val intentConfig = Bundle().apply {
                    putString("PLUGIN_NAME", "INTENT")
                    putString("RESET_CONFIG", "true")
                    val intentProps = Bundle().apply {
                        putString("intent_output_enabled", "true")
                        putString("intent_action", ACTION_ZEBRA_SCAN)
                        putString("intent_delivery", "2") // 2 = Broadcast Intent
                    }
                    putBundle("PARAM_LIST", intentProps)
                }
                putBundle("PLUGIN_CONFIG", intentConfig)
            }

            val setConfigIntent = Intent(ACTION_ZEBRA_API).apply {
                putExtra("com.symbol.datawedge.api.SET_CONFIG", profileConfig)
            }
            context.sendBroadcast(setConfigIntent)
            Log.d(TAG, "Đã gửi cấu hình tự động cho Zebra DataWedge Profile [$profileName].")
        } catch (_: Exception) {
            // Không phải máy Zebra thì bỏ qua an toàn
        }
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

