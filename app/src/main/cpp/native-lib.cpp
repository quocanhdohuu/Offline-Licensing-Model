#include <jni.h>
#include <string>

extern "C" JNIEXPORT jstring JNICALL
Java_com_example_offlinelicensingmodel_MainActivity_stringFromJNI(
        JNIEnv* env,
        jobject /* this */) {
    std::string hello = "Offline Licensing Model";
    return env->NewStringUTF(hello.c_str());
}