package com.example.offlinelicensingmodel

import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import android.util.Log
import java.io.File

/**
 * Lớp phòng thủ kiểm tra trạng thái Root của thiết bị (Lớp 1 trong mô hình OLM).
 *
 * Kết hợp 4 kỹ thuật phát hiện:
 * 1. Kiểm tra Build Tags (phát hiện ROM mod, test-keys).
 * 2. Quét các file nhị phân su, busybox ở tầng Java.
 * 3. Quét các package quản lý Root (Magisk, SuperSU, KernelSU).
 * 4. Kiểm tra quyền truy cập hệ thống ở tầng Native C++ qua JNI (chống Hook Java).
 */
class RootChecker(private val context: Context) {

    companion object {
        private const val TAG = "RootChecker"

        init {
            System.loadLibrary("offlinelicensingmodel")
        }

        private val KNOWN_ROOT_PATHS = arrayOf(
            "/system/bin/su",
            "/system/xbin/su",
            "/sbin/su",
            "/vendor/bin/su",
            "/data/local/su",
            "/data/local/bin/su",
            "/data/local/xbin/su",
            "/system/sd/xbin/su",
            "/su/bin/su",
            "/system/bin/.ext/.su",
            "/system/xbin/busybox"
        )

        private val KNOWN_ROOT_PACKAGES = arrayOf(
            "com.topjohnwu.magisk",
            "eu.chainfire.supersu",
            "com.noshufou.android.su",
            "com.koushikdutta.superuser",
            "me.weishu.kernelsu"
        )
    }

    /**
     * Hàm JNI Native gọi xuống C++ để kiểm tra sự tồn tại của file su.
     */
    private external fun checkNativeRoot(): Int

    data class RootStatus(
        val isRooted: Boolean,
        val details: String
    )

    /**
     * Thực hiện kiểm tra tổng thể 4 tầng phát hiện Root.
     */
    fun checkRoot(): RootStatus {
        // 1. Kiểm tra Build.TAGS
        val buildTags = Build.TAGS
        if (buildTags != null && buildTags.contains("test-keys")) {
            Log.w(TAG, "Phát hiện Root qua Build.TAGS: $buildTags")
            return RootStatus(isRooted = true, details = "Phát hiện Custom ROM (test-keys).")
        }

        // 2. Kiểm tra file su trong các thư mục hệ thống (Java layer)
        for (path in KNOWN_ROOT_PATHS) {
            if (File(path).exists()) {
                Log.w(TAG, "Phát hiện file Root nhị phân tại: $path")
                return RootStatus(isRooted = true, details = "Phát hiện file nhị phân su tại $path.")
            }
        }

        // 3. Kiểm tra các ứng dụng quản lý Root đã cài đặt
        val pm = context.packageManager
        for (pkg in KNOWN_ROOT_PACKAGES) {
            try {
                pm.getPackageInfo(pkg, 0)
                Log.w(TAG, "Phát hiện ứng dụng quản lý Root: $pkg")
                return RootStatus(isRooted = true, details = "Phát hiện ứng dụng Root ($pkg).")
            } catch (_: PackageManager.NameNotFoundException) {
                // Không tìm thấy package -> an toàn
            }
        }

        // 4. Kiểm tra bằng hàm gọi hệ thống trong Native C++ (chống Java Hooking)
        val nativeRootCode = checkNativeRoot()
        if (nativeRootCode == 1) {
            Log.w(TAG, "Phát hiện Root bằng Native C++ access check.")
            return RootStatus(isRooted = true, details = "Phát hiện file su qua tầng Native C++.")
        }

        return RootStatus(isRooted = false, details = "Thiết bị an toàn (Non-Root).")
    }
}

