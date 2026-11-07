package com.example.offlinelicensingmodel

import android.app.ActivityManager
import android.content.Context
import android.hardware.Sensor
import android.hardware.SensorManager
import android.media.MediaDrm
import android.net.Uri
import android.os.Build
import android.os.StatFs
import android.util.DisplayMetrics
import android.util.Log
import android.view.WindowManager
import java.security.MessageDigest
import java.util.Locale
import java.util.UUID

/**
 * Quản lý và chuẩn hóa Device Fingerprint (DF) cho mô hình Offline Licensing Model (OLM).
 *
 * Tuân thủ nguyên tắc Zero Trust:
 * - Tier 1: Hardware Serial bất biến vật lý (Vendor Property MTK/Newland NVRAM & Kernel Sysfs node).
 * - Tier 2: Thuộc tính phần cứng tĩnh (Manufacturer, Model, Board, Chipset, ABIs, Physical Pixel Res, RAM chuẩn hóa GB).
 * - Tier 3: Loại bỏ Widevine L3, Sensor List, Display DPI, Storage, Build.FINGERPRINT khỏi chuỗi băm để kháng 100% Factory Reset và cập nhật OTA.
 * - Đầu ra: Mã 16 ký tự Crockford Base32 (80-bit entropy) định dạng XXXX-XXXX-XXXX-XXXX.
 */
object DeviceFingerprintManager {

    const val DEFAULT_SALT = "THH_OLM_SALT_SECURE_2026"
    private const val CROCKFORD_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

    data class DeviceDetails(
        val serial: String,
        val drmId: String,            // Chỉ dùng chẩn đoán
        val manufacturer: String,
        val model: String,
        val board: String,
        val hardware: String,
        val supportedAbis: String,
        val displayResolution: String,
        val totalRamGb: Int,
        val actualRamMb: Long,
        val sensorCount: Int,         // Chỉ dùng chẩn đoán
        val sensorHash: String,       // Chỉ dùng chẩn đoán
        val sensorList: List<String>, // Chỉ dùng chẩn đoán
        val buildFingerprint: String, // Chỉ dùng chẩn đoán
        val storageGb: Double,        // Chỉ dùng chẩn đoán
        val canonicalString: String,
        val fullSha256Hex: String,
        val dfCode: String
    )

    /**
     * Thu thập thông tin và sinh mã Device Fingerprint chuẩn hóa kháng Factory Reset.
     */
    fun getDeviceDetails(context: Context, salt: String = DEFAULT_SALT): DeviceDetails {
        // 1. Tier 1 - Hardware Serial vật lý bất biến (khắc Laser / NVRAM chip / Zebra OEMinfo)
        val serial = getSafeHardwareSerial(context)

        // 2. Tier 2 - Thông số cấu hình phần cứng tĩnh
        val manufacturer = Build.MANUFACTURER.trim().uppercase(Locale.US)
        val model = Build.MODEL.trim().uppercase(Locale.US)
        val board = Build.BOARD.trim().uppercase(Locale.US)
        val hardware = Build.HARDWARE.trim().uppercase(Locale.US)
        val supportedAbis = Build.SUPPORTED_ABIS.joinToString(",").uppercase(Locale.US)

        // Màn hình: Chuẩn hóa theo kích thước điểm ảnh vật lý của tấm nền (Physical Pixels)
        // Loại bỏ densityDpi để kháng mọi thay đổi thu phóng giao diện sau Factory Reset
        val wm = context.getSystemService(Context.WINDOW_SERVICE) as WindowManager
        val metrics = DisplayMetrics()
        @Suppress("DEPRECATION")
        wm.defaultDisplay.getRealMetrics(metrics)
        val minDim = kotlin.math.min(metrics.widthPixels, metrics.heightPixels)
        val maxDim = kotlin.math.max(metrics.widthPixels, metrics.heightPixels)
        val displayResolution = "${minDim}x${maxDim}"

        // RAM: Làm tròn lên mức GB gần nhất (MT90 ~ 3.8GB -> 4GB) để tránh lệch khi kernel thay đổi video memory
        val activityManager = context.getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager
        val memoryInfo = ActivityManager.MemoryInfo()
        activityManager.getMemoryInfo(memoryInfo)
        val actualRamMb = memoryInfo.totalMem / (1024 * 1024)
        val totalRamGb = kotlin.math.round(memoryInfo.totalMem.toDouble() / (1024.0 * 1024.0 * 1024.0)).toInt()

        // 3. Thông tin chẩn đoán (Diagnostic only - không cho vào hash DF)
        val drmId = getMediaDrmId()
        val sensorManager = context.getSystemService(Context.SENSOR_SERVICE) as SensorManager
        val sensors = sensorManager.getSensorList(Sensor.TYPE_ALL)
        val sensorNames = sensors.map { it.name.trim() }.sorted()
        val sensorHash = sha256Hex(sensorNames.joinToString(","))
        val buildFingerprint = Build.FINGERPRINT
        val statFs = StatFs(context.filesDir.path)
        val storageGb = statFs.totalBytes / (1024.0 * 1024.0 * 1024.0)

        // 4. Ghép chuỗi chuẩn tắc Canonical String (100% phần cứng bất biến)
        val canonicalString = "SERIAL=$serial" +
                "|MF=$manufacturer" +
                "|MD=$model" +
                "|BOARD=$board" +
                "|HW=$hardware" +
                "|ABI=$supportedAbis" +
                "|DISP=$displayResolution" +
                "|RAM=${totalRamGb}GB" +
                "|SALT=$salt"

        // 5. Băm SHA-256
        val digest = MessageDigest.getInstance("SHA-256")
        val sha256Bytes = digest.digest(canonicalString.toByteArray(Charsets.UTF_8))
        val fullSha256Hex = sha256Bytes.joinToString("") { "%02X".format(it) }

        // 6. Lấy 10 bytes đầu tiên (80 bits) và mã hóa Crockford Base32 (16 ký tự)
        val rawBase32 = encodeCrockfordBase32(sha256Bytes.copyOfRange(0, 10))
        val dfCode = formatDfCode(rawBase32)

        return DeviceDetails(
            serial = serial,
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
     * Đọc Hardware Serial vật lý an toàn, tương thích Android 9-14 cho cả Newland MT90 và Zebra Technologies.
     * Áp dụng kiến trúc đa tầng:
     * - Tầng 1: Zebra OEMinfo Content Provider (Zebra TC21/TC26/TC52/TC53/TC58/MC3300 Android 10-14).
     * - Tầng 2: MediaTek NVRAM Serial (vendor.gsm.serial trên Newland MT90/N7).
     * - Tầng 3: Qualcomm SoC Hardware Serial (/sys/devices/soc0/serial_number).
     * - Tầng 4: Linux Sysfs iSerial (/sys/class/android_usb/android0/iSerial).
     * - Tầng 5: System Properties (ro.boot.serialno, ro.serialno, ro.zebra.serial, ro.symbol.serial).
     * - Tầng 6: MediaDrm Hardware UUID (Đảm bảo điện thoại thông thường không bao giờ bị trùng DF chéo máy).
     */
    fun getSafeHardwareSerial(context: Context? = null): String {
        // Tầng 1: Zebra Technologies OEMinfo Content Provider (Khuyến nghị của Zebra cho Android 10 - 14)
        if (context != null) {
            val zebraSerial = getZebraSerialFromOemInfo(context)
            if (!zebraSerial.isNullOrBlank()) {
                return zebraSerial
            }
        }

        // Tầng 2: Đọc Vendor Property MediaTek / Newland (chứa số Serial gốc NVRAM MT90)
        val vendorSerial = getSystemProperty("vendor.gsm.serial")
        if (!vendorSerial.isNullOrBlank() && vendorSerial != "unknown") {
            val cleanSerial = vendorSerial.trim().split("\\s+".toRegex())[0]
            if (cleanSerial.length >= 6) {
                return cleanSerial.uppercase(Locale.US)
            }
        }

        // Tầng 3: Đọc Qualcomm SoC Serial (Thường có trên chip Snapdragon của Zebra và PDA cao cấp)
        val qcomSerial = getQualcommSocSerial()
        if (!qcomSerial.isNullOrBlank()) {
            return qcomSerial
        }

        // Tầng 4: Đọc file node Linux Sysfs iSerial
        try {
            val iSerial = java.io.File("/sys/class/android_usb/android0/iSerial")
            if (iSerial.exists() && iSerial.canRead()) {
                val s = iSerial.readText().trim()
                if (s.isNotEmpty() && s != "unknown") {
                    return s.uppercase(Locale.US)
                }
            }
        } catch (_: Exception) { }

        // Tầng 5: Thử đọc các biến Bootloader / Zebra OEM Properties
        val propKeys = arrayOf(
            "ro.boot.serialno",
            "ro.serialno",
            "ro.zebra.serial",
            "ro.symbol.serial",
            "persist.sys.zebra.serial",
            "vendor.serialno"
        )
        for (key in propKeys) {
            val valStr = getSystemProperty(key)
            if (!valStr.isNullOrBlank() && valStr != "unknown") {
                return valStr.trim().uppercase(Locale.US)
            }
        }

        // Tầng 6: Phân vùng Doanh nghiệp bất biến (/enterprise/usr/)
        // Dành riêng cho thiết bị chuyên dụng doanh nghiệp (Zebra, Honeywell...).
        // Phân vùng /enterprise/ KHÔNG BAO GIỜ bị xóa khi thực hiện Enterprise Reset!
        val enterpriseSerial = getOrGenerateEnterpriseSerial()
        if (!enterpriseSerial.isNullOrBlank()) {
            return enterpriseSerial
        }

        // Tầng 7: Cứu cánh thông minh cho điện thoại thương mại (Pixel, Samsung...)
        // Dùng MediaDrm Device Unique ID để đảm bảo 2 máy cùng dòng KHÔNG BAO GIỜ bị trùng DF!
        val drmId = getMediaDrmId()
        if (drmId.isNotBlank() && drmId != "FALLBACK-NOWIDEVINE") {
            return "DRM-$drmId"
        }

        return "GENERIC-PDA-SERIAL"
    }

    private val ENTERPRISE_PATHS = arrayOf(
        // 1. Zebra Technologies & Datalogic
        "/enterprise/usr/persist/olm_device_serial.dat",
        "/enterprise/usr/olm_device_serial.dat",
        "/enterprise/device/settings/olm_device_serial.dat",
        "/enterprise/datalogic/olm_device_serial.dat",

        // 2. Honeywell (Enterprise Provisioner)
        "/sdcard/honeywell/persist/olm_device_serial.dat",
        "/storage/emulated/0/honeywell/persist/olm_device_serial.dat",
        "/enterprise/honeywell/persist/olm_device_serial.dat",

        // 3. Point Mobile (EmKit Staging)
        "/sdcard/PointMobile/olm_device_serial.dat",
        "/storage/emulated/0/PointMobile/olm_device_serial.dat"
    )

    private val ENTERPRISE_DIRS = arrayOf(
        // 1. Zebra & Datalogic
        "/enterprise/usr/persist",
        "/enterprise/usr",
        "/enterprise/device/settings",
        "/enterprise/datalogic",

        // 2. Honeywell
        "/sdcard/honeywell/persist",
        "/storage/emulated/0/honeywell/persist",
        "/enterprise/honeywell/persist",

        // 3. Point Mobile
        "/sdcard/PointMobile",
        "/storage/emulated/0/PointMobile"
    )

    /**
     * Đọc hoặc khởi tạo Serial bền vững trong phân vùng Doanh nghiệp (/enterprise/, Honeywell, Point Mobile).
     * Kháng 100% Enterprise Reset trên tất cả các dòng Zebra, Honeywell, Point Mobile, Datalogic.
     */
    private fun getOrGenerateEnterpriseSerial(): String? {
        // 1. Tìm đọc file serial đã tồn tại trước đó
        for (path in ENTERPRISE_PATHS) {
            try {
                val f = java.io.File(path)
                if (f.exists() && f.canRead()) {
                    val content = f.readText().trim()
                    if (content.length >= 6) {
                        Log.i("DeviceFingerprint", "Đã đọc Enterprise Serial từ $path: $content")
                        return content
                    }
                }
            } catch (e: Exception) {
                Log.w("DeviceFingerprint", "Lỗi đọc Enterprise path $path: ${e.message}")
            }
        }

        // 2. Nếu chưa có, khởi tạo token mới và lưu vào thư mục bất biến đầu tiên khả dụng
        for (dirPath in ENTERPRISE_DIRS) {
            try {
                val dir = java.io.File(dirPath)
                if (!dir.exists()) {
                    val parent = dir.parentFile
                    if (parent != null && parent.exists() && parent.isDirectory && parent.canWrite()) {
                        dir.mkdirs()
                    }
                }
                if (dir.exists() && dir.isDirectory && dir.canWrite()) {
                    val targetFile = java.io.File(dir, "olm_device_serial.dat")
                    val modelClean = Build.MODEL.trim().uppercase(Locale.US).replace("[^A-Z0-9]".toRegex(), "")
                    val drmSeed = getMediaDrmId().take(8)
                    val randSeed = UUID.randomUUID().toString().replace("-", "").uppercase(Locale.US).take(8)
                    val seed = if (drmSeed.isNotBlank() && !drmSeed.startsWith("ERR") && !drmSeed.startsWith("FALLBACK")) {
                        drmSeed + randSeed.take(4)
                    } else {
                        randSeed
                    }
                    val newSerial = "EP-$modelClean-$seed"

                    targetFile.writeText(newSerial, Charsets.UTF_8)
                    targetFile.setReadable(true, false) // Cấp quyền đọc toàn hệ thống
                    targetFile.setWritable(true, false)
                    Log.i("DeviceFingerprint", "Đã khởi tạo và lưu Enterprise Serial mới: $newSerial vào $targetFile")
                    return newSerial
                }
            } catch (e: Exception) {
                Log.w("DeviceFingerprint", "Lỗi tạo Enterprise Serial tại $dirPath: ${e.message}")
            }
        }
        return null
    }

    /**
     * Đọc Hardware Serial trên thiết bị Zebra Technologies qua OEMinfo Content Provider (Android 10 - 14).
     */
    private fun getZebraSerialFromOemInfo(context: Context): String? {
        val uris = arrayOf(
            "content://oem_info/oem.zebra.secure/build_serial",
            "content://oem_info/oem.zebra.secure/serial"
        )
        for (uriStr in uris) {
            try {
                val uri = Uri.parse(uriStr)
                val cursor = context.contentResolver.query(uri, null, null, null, null)
                Log.d("DeviceFingerprint", "Zebra OEMinfo query [$uriStr]: cursor=$cursor, count=${cursor?.count}")
                cursor?.use { c ->
                    if (c.moveToFirst()) {
                        val colNames = c.columnNames.joinToString(",")
                        Log.d("DeviceFingerprint", "Zebra OEMinfo columns: $colNames")
                        val colIdx = c.getColumnIndex("build_serial")
                        val serial = if (colIdx != -1) c.getString(colIdx) else c.getString(0)
                        Log.d("DeviceFingerprint", "Zebra OEMinfo value: $serial")
                        if (!serial.isNullOrBlank() && serial != "unknown") {
                            return serial.trim().uppercase(Locale.US)
                        }
                    }
                }
            } catch (e: Exception) {
                Log.w("DeviceFingerprint", "Không thể query Zebra OEMinfo [$uriStr]: ${e.message}")
            }
        }
        return null
    }

    /**
     * Đọc Hardware Serial của chip Qualcomm Snapdragon qua sysfs soc0.
     */
    private fun getQualcommSocSerial(): String? {
        val paths = arrayOf(
            "/sys/devices/soc0/serial_number",
            "/sys/devices/system/soc/soc0/serial_number"
        )
        for (path in paths) {
            try {
                val file = java.io.File(path)
                if (file.exists() && file.canRead()) {
                    val s = file.readText().trim()
                    if (s.isNotEmpty() && s != "0" && s != "unknown") {
                        return s.uppercase(Locale.US)
                    }
                }
            } catch (_: Exception) { }
        }
        return null
    }

    private fun getSystemProperty(key: String): String? {
        return try {
            val clazz = Class.forName("android.os.SystemProperties")
            val getMethod = clazz.getMethod("get", String::class.java)
            getMethod.invoke(null, key) as? String
        } catch (e: Exception) {
            null
        }
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

