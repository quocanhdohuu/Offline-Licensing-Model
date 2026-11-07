package com.example.offlinelicensingmodel

import android.content.Context
import android.content.SharedPreferences
import android.util.Log
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import java.io.File

/**
 * Quản lý lưu trữ bản quyền và mốc thời gian an toàn bằng EncryptedSharedPreferences (Hardware Keystore AES-256 GCM)
 * kết hợp cơ chế sao lưu phục hồi tự động qua phân vùng /enterprise/ để kháng 100% Enterprise Reset.
 */
class LicenseStorage(context: Context) {

    companion object {
        private const val TAG = "LicenseStorage"
        private const val PREF_FILE_NAME = "olm_secure_license_prefs"

        private const val KEY_ACTIVE_TOKEN = "active_jwt_token"
        private const val KEY_LAST_KNOWN_TIME = "last_known_time_sec"
        private const val KEY_ACTIVATED_AT = "activated_at_sec"

        private val ENTERPRISE_BACKUP_PATHS = arrayOf(
            // 1. Zebra Technologies & Datalogic
            "/enterprise/usr/persist/olm_active_license.jwt",
            "/enterprise/usr/olm_active_license.jwt",
            "/enterprise/device/settings/olm_active_license.jwt",
            "/enterprise/datalogic/olm_active_license.jwt",

            // 2. Honeywell (Enterprise Provisioner)
            "/sdcard/honeywell/persist/olm_active_license.jwt",
            "/storage/emulated/0/honeywell/persist/olm_active_license.jwt",
            "/enterprise/honeywell/persist/olm_active_license.jwt",

            // 3. Point Mobile (EmKit Staging)
            "/sdcard/PointMobile/olm_active_license.jwt",
            "/storage/emulated/0/PointMobile/olm_active_license.jwt"
        )
    }

    private val prefs: SharedPreferences = createEncryptedPreferences(context)

    private fun createEncryptedPreferences(context: Context): SharedPreferences {
        return try {
            val masterKey = MasterKey.Builder(context)
                .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
                .build()

            EncryptedSharedPreferences.create(
                context,
                PREF_FILE_NAME,
                masterKey,
                EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
                EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
            )
        } catch (e: Exception) {
            Log.e(TAG, "Lỗi khởi tạo EncryptedSharedPreferences, fallback SharedPreferences nội bộ: ${e.message}")
            context.getSharedPreferences(PREF_FILE_NAME + "_fallback", Context.MODE_PRIVATE)
        }
    }

    /**
     * Lưu chuỗi Token bản quyền JWT đã được kích hoạt.
     * Đồng thời tự động sao lưu vào phân vùng /enterprise/ để kháng Enterprise Reset.
     */
    fun saveLicense(token: String) {
        val cleanToken = token.trim()
        val nowSec = System.currentTimeMillis() / 1000
        prefs.edit()
            .putString(KEY_ACTIVE_TOKEN, cleanToken)
            .putLong(KEY_ACTIVATED_AT, nowSec)
            .apply()

        backupToEnterprisePartition(cleanToken)
    }

    /**
     * Lấy chuỗi Token bản quyền đang lưu.
     * Tự động phục hồi từ phân vùng /enterprise/ nếu app vừa bị xóa data hoặc máy vừa bị Enterprise Reset.
     */
    fun getSavedLicense(): String? {
        val memoryToken = prefs.getString(KEY_ACTIVE_TOKEN, null)
        if (!memoryToken.isNullOrBlank()) {
            return memoryToken
        }

        // Nếu SharedPreferences trống (sau khi reset máy), tự động tìm bản sao lưu trong /enterprise/
        val backupToken = restoreFromEnterprisePartition()
        if (!backupToken.isNullOrBlank()) {
            Log.i(TAG, "Đã tự động khôi phục License Token từ phân vùng /enterprise!")
            val nowSec = System.currentTimeMillis() / 1000
            prefs.edit()
                .putString(KEY_ACTIVE_TOKEN, backupToken)
                .putLong(KEY_ACTIVATED_AT, nowSec)
                .apply()
            return backupToken
        }

        return null
    }

    /**
     * Xóa sạch thông tin bản quyền (Reset).
     */
    fun clearLicense() {
        prefs.edit()
            .remove(KEY_ACTIVE_TOKEN)
            .remove(KEY_ACTIVATED_AT)
            .apply()

        clearEnterpriseBackup()
    }

    /**
     * Ghi bản sao lưu Token vào phân vùng /enterprise/.
     */
    private fun backupToEnterprisePartition(token: String) {
        for (path in ENTERPRISE_BACKUP_PATHS) {
            try {
                val file = File(path)
                val parent = file.parentFile
                if (parent != null) {
                    if (!parent.exists()) {
                        val grandParent = parent.parentFile
                        if (grandParent != null && grandParent.exists() && grandParent.isDirectory && grandParent.canWrite()) {
                            parent.mkdirs()
                        }
                    }
                    if (parent.exists() && parent.canWrite()) {
                        file.writeText(token, Charsets.UTF_8)
                        file.setReadable(true, false)
                        file.setWritable(true, false)
                        Log.i(TAG, "Đã sao lưu License Token an toàn vào phân vùng /enterprise: $path")
                        return
                    }
                }
            } catch (e: Exception) {
                Log.w(TAG, "Không thể sao lưu license vào $path: ${e.message}")
            }
        }
    }

    /**
     * Khôi phục Token từ phân vùng /enterprise/.
     */
    private fun restoreFromEnterprisePartition(): String? {
        for (path in ENTERPRISE_BACKUP_PATHS) {
            try {
                val file = File(path)
                if (file.exists() && file.canRead()) {
                    val token = file.readText().trim()
                    if (token.isNotEmpty()) {
                        return token
                    }
                }
            } catch (e: Exception) {
                Log.w(TAG, "Không thể đọc sao lưu license từ $path: ${e.message}")
            }
        }
        return null
    }

    /**
     * Xóa file sao lưu trong phân vùng /enterprise/ khi người dùng chủ động bấm 'Xóa Bản Quyền'.
     */
    private fun clearEnterpriseBackup() {
        for (path in ENTERPRISE_BACKUP_PATHS) {
            try {
                val file = File(path)
                if (file.exists()) {
                    file.delete()
                    Log.i(TAG, "Đã xóa file sao lưu license $path")
                }
            } catch (e: Exception) {
                Log.w(TAG, "Lỗi xóa file sao lưu license $path: ${e.message}")
            }
        }
    }

    /**
     * Lấy mốc thời gian sử dụng gần nhất (Epoch seconds).
     */
    fun getLastKnownTime(): Long {
        return prefs.getLong(KEY_LAST_KNOWN_TIME, 0L)
    }

    /**
     * Cập nhật mốc thời gian sử dụng gần nhất (Epoch seconds).
     */
    fun updateLastKnownTime(timeSec: Long) {
        val currentLast = getLastKnownTime()
        if (timeSec > currentLast) {
            prefs.edit().putLong(KEY_LAST_KNOWN_TIME, timeSec).apply()
        }
    }
}
