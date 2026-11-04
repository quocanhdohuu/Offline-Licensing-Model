#include <jni.h>
#include <string>
#include <unistd.h>
#include <android/log.h>
#include "public_key.h"
#include "ed25519.h"

#define TAG "OLM_NativeCrypto"
#define LOGD(...) __android_log_print(ANDROID_LOG_DEBUG, TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, TAG, __VA_ARGS__)

extern "C" {

/**
 * Xác thực chữ ký số Ed25519 hoàn toàn Offline trong tầng Native C++.
 *
 * @param env JNI Environment
 * @param thiz Đối tượng LicenseValidator
 * @param jSigningInput Mảng bytes UTF-8 của chuỗi "header_b64.payload_b64"
 * @param jSignature Mảng 64 bytes chữ ký số
 *
 * @return  0: Chữ ký hợp lệ (VERIFIED_OK)
 *         -1: Chữ ký không hợp lệ (INVALID_SIGNATURE)
 *         -2: Định dạng hoặc kích thước dữ liệu sai (INVALID_FORMAT)
 */
JNIEXPORT jint JNICALL
Java_com_example_offlinelicensingmodel_LicenseValidator_verifyNativeSignature(
        JNIEnv* env,
        jobject /* thiz */,
        jbyteArray jSigningInput,
        jbyteArray jSignature) {

    if (jSigningInput == nullptr || jSignature == nullptr) {
        LOGE("verifyNativeSignature: Null input parameters");
        return -2;
    }

    jsize sigLen = env->GetArrayLength(jSignature);
    if (sigLen != 64) {
        LOGE("verifyNativeSignature: Invalid signature length: %d (expected 64)", sigLen);
        return -2;
    }

    jsize inputLen = env->GetArrayLength(jSigningInput);
    if (inputLen <= 0) {
        LOGE("verifyNativeSignature: Empty signing input");
        return -2;
    }

    jbyte* sigBytes = env->GetByteArrayElements(jSignature, nullptr);
    jbyte* inputBytes = env->GetByteArrayElements(jSigningInput, nullptr);

    if (sigBytes == nullptr || inputBytes == nullptr) {
        if (sigBytes) env->ReleaseByteArrayElements(jSignature, sigBytes, JNI_ABORT);
        if (inputBytes) env->ReleaseByteArrayElements(jSigningInput, inputBytes, JNI_ABORT);
        return -2;
    }

    // 1. Khôi phục Public Key tạm thời trong RAM bằng phép toán XOR
    uint8_t pubkey[32];
    olm_get_public_key(pubkey);

    // 2. Thực hiện giải thuật xác thực Ed25519
    int verifyResult = ed25519_verify(
            reinterpret_cast<const unsigned char*>(sigBytes),
            reinterpret_cast<const unsigned char*>(inputBytes),
            static_cast<size_t>(inputLen),
            pubkey
    );

    // 3. Xóa sạch vùng nhớ RAM chứa Public Key ngay lập tức (Zeroize) để chống dump memory
    olm_clean_key_memory(pubkey);

    // 4. Giải phóng tài nguyên JNI
    env->ReleaseByteArrayElements(jSignature, sigBytes, JNI_ABORT);
    env->ReleaseByteArrayElements(jSigningInput, inputBytes, JNI_ABORT);

    if (verifyResult == 1) {
        LOGD("verifyNativeSignature: Ed25519 Signature VALID");
        return 0; // VERIFIED_OK
    } else {
        LOGE("verifyNativeSignature: Ed25519 Signature INVALID");
        return -1; // INVALID_SIGNATURE
    }
}

/**
 * Kiểm tra các dấu hiệu Root bằng hàm hệ thống cấp thấp (Low-level Native C).
 * Chống các kỹ thuật bypass / Hooking ở tầng Java.
 *
 * @return 1 nếu phát hiện nhị phân su, 0 nếu thiết bị an toàn.
 */
JNIEXPORT jint JNICALL
Java_com_example_offlinelicensingmodel_RootChecker_checkNativeRoot(
        JNIEnv* /* env */,
        jobject /* thiz */) {

    const char* su_paths[] = {
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
            nullptr
    };

    for (int i = 0; su_paths[i] != nullptr; ++i) {
        if (access(su_paths[i], F_OK) == 0) {
            LOGE("checkNativeRoot: DETECTED SU AT %s", su_paths[i]);
            return 1; // Phát hiện Root
        }
    }

    return 0; // An toàn
}

} // extern "C"
