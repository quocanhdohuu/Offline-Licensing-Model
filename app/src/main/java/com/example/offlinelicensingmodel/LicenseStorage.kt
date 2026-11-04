package com.example.offlinelicensingmodel

import android.content.Context
import android.content.SharedPreferences
import android.util.Log
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

/**
 * Quản lý lưu trữ bản quyền và mốc thời gian an toàn bằng EncryptedSharedPreferences (Hardware Keystore AES-256 GCM).
 */
class LicenseStorage(context: Context) {

    companion object {
        private const val TAG = "LicenseStorage"
        private const val PREF_FILE_NAME = "olm_secure_license_prefs"

        private const val KEY_ACTIVE_TOKEN = "active_jwt_token"
        private const val KEY_LAST_KNOWN_TIME = "last_known_time_sec"
        private const val KEY_ACTIVATED_AT = "activated_at_sec"
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
     */
    fun saveLicense(token: String) {
        val nowSec = System.currentTimeMillis() / 1000
        prefs.edit()
            .putString(KEY_ACTIVE_TOKEN, token.trim())
            .putLong(KEY_ACTIVATED_AT, nowSec)
            .apply()
    }

    /**
     * Lấy chuỗi Token bản quyền đang lưu.
     */
    fun getSavedLicense(): String? {
        return prefs.getString(KEY_ACTIVE_TOKEN, null)
    }

    /**
     * Xóa sạch thông tin bản quyền (Reset).
     */
    fun clearLicense() {
        prefs.edit()
            .remove(KEY_ACTIVE_TOKEN)
            .remove(KEY_ACTIVATED_AT)
            .apply()
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
