package com.example.offlinelicensingmodel

import android.os.Build
import androidx.appcompat.app.AppCompatActivity
import android.os.Bundle
import android.widget.TextView
import com.example.offlinelicensingmodel.databinding.ActivityMainBinding
import android.app.ActivityManager
import android.content.Context
import android.hardware.SensorManager
import android.os.StatFs
import android.util.DisplayMetrics
import android.media.MediaDrm
import java.util.UUID
import java.security.MessageDigest

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        binding.sampleText.text = collectDeviceInfo()
    }

    private fun collectDeviceInfo(): String {

        val info = StringBuilder()

        // 1. Thong tin Build
        info.append("MANUFACTURER: ${Build.MANUFACTURER}\n")
        info.append("MODEL: ${Build.MODEL}\n")
        info.append("FINGERPRINT: ${Build.FINGERPRINT}\n")
        info.append("BOARD: ${Build.BOARD}\n")
        info.append("HARDWARE: ${Build.HARDWARE}\n")
        info.append("CPU ABI: ${Build.SUPPORTED_ABIS.joinToString()}\n")
        info.append("ANDROID: ${Build.VERSION.RELEASE}\n")

        // 2. Thong tin man hinh
        val metrics = DisplayMetrics()
        @Suppress("DEPRECATION")
        windowManager.defaultDisplay.getRealMetrics(metrics)

        info.append("\n--- DISPLAY ---\n")
        info.append("WIDTH: ${metrics.widthPixels}\n")
        info.append("HEIGHT: ${metrics.heightPixels}\n")
        info.append("DPI: ${metrics.densityDpi}\n")

        // 3. RAM
        val activityManager =
            getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager

        val memoryInfo = ActivityManager.MemoryInfo()
        activityManager.getMemoryInfo(memoryInfo)

        val totalRam = memoryInfo.totalMem / (1024 * 1024)

        info.append("\n--- MEMORY ---\n")
        info.append("TOTAL RAM: ${totalRam} MB\n")

        // 4. Storage
        val statFs = StatFs(filesDir.path)

        val totalStorage =
            statFs.totalBytes / (1024.0 * 1024 * 1024)

        info.append("TOTAL STORAGE: %.2f GB\n".format(totalStorage))

        // 5. Sensors
        val sensorManager =
            getSystemService(Context.SENSOR_SERVICE) as SensorManager

        val sensors = sensorManager.getSensorList(
            android.hardware.Sensor.TYPE_ALL
        )

        info.append("\n--- SENSORS ---\n")
        info.append("SENSOR COUNT: ${sensors.size}\n")

        sensors.forEach {
            info.append("- ${it.name}\n")
        }
        info.append("\n--- MEDIA DRM ---\n")
        info.append("DEVICE ID: ${getMediaDrmId()}\n")

        val testSalt = "OLM_TEST_SALT_2026"

        val df = createDeviceFingerprint(
            deviceInfo = info.toString(),
            salt = testSalt
        )

        info.append("\n--- DEVICE FINGERPRINT ---\n")
        info.append("DF: $df\n")
        info.append("DF LENGTH: ${df.length}\n")
        return info.toString()
    }
    private fun getMediaDrmId(): String {

        // UUID cua Widevine DRM
        val widevineUuid = UUID.fromString(
            "edef8ba9-79d6-4ace-a3c8-27dcd51d21ed"
        )

        if (!MediaDrm.isCryptoSchemeSupported(widevineUuid)) {
            return "WIDEVINE NOT SUPPORTED"
        }

        var drm: MediaDrm? = null

        return try {
            drm = MediaDrm(widevineUuid)

            val deviceId = drm.getPropertyByteArray(
                MediaDrm.PROPERTY_DEVICE_UNIQUE_ID
            )

            deviceId.joinToString("") {
                "%02X".format(it.toInt() and 0xFF)
            }

        } catch (e: Exception) {
            "ERROR: ${e.javaClass.simpleName}: ${e.message}"
        } finally {
            drm?.release()
        }
    }
    private fun createDeviceFingerprint(
        deviceInfo: String,
        salt: String
    ): String {

        val input = "$deviceInfo|$salt"

        val digest = MessageDigest.getInstance("SHA-256")
        val hash = digest.digest(input.toByteArray(Charsets.UTF_8))

        return hash.joinToString("") {
            "%02X".format(it.toInt() and 0xFF)
        }
    }
}