#!/usr/bin/env python3
import subprocess
import time
import os
import sys
import shutil
from PIL import Image

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

def run_adb(cmd, dev=None):
    base = ["adb"]
    if dev:
        base.extend(["-s", dev])
    base.extend(cmd)
    res = subprocess.run(base, capture_output=True, text=True)
    return res.stdout.strip()

def ensure_screen_on(dev):
    out = run_adb(["shell", "dumpsys", "power"], dev)
    if "state=OFF" in out or "mWakefulness=Asleep" in out:
        print("    [!] Màn hình đang tắt, gửi lệnh bật màn hình...")
        run_adb(["shell", "input", "keyevent", "26"], dev)
        time.sleep(0.8)
    run_adb(["shell", "wm", "dismiss-keyguard"], dev)
    time.sleep(0.5)

def capture(dev, remote_path, local_path):
    ensure_screen_on(dev)
    time.sleep(1)
    run_adb(["shell", "screencap", "-p", remote_path], dev)
    run_adb(["pull", remote_path, local_path], dev)
    
    # Kiểm tra kích thước và số màu
    if os.path.exists(local_path):
        img = Image.open(local_path)
        colors = len(img.convert('RGB').getcolors(maxcolors=1000000))
        size_kb = os.path.getsize(local_path) / 1024
        print(f"    [+] Đã lưu {local_path} ({size_kb:.1f} KB, {colors} màu sắc)")

def main():
    devices_out = subprocess.run(["adb", "devices"], capture_output=True, text=True).stdout
    devices = []
    for line in devices_out.splitlines()[1:]:
        parts = line.strip().split()
        if len(parts) >= 2 and parts[1] == "device" and "emulator" not in parts[0]:
            devices.append(parts[0])

    if not devices:
        print("[-] Không tìm thấy thiết bị MT90 qua ADB!")
        return

    dev = devices[0]
    print(f"[+] Sử dụng thiết bị: {dev}")

    # Đặt thời gian sáng màn hình 10 phút
    run_adb(["shell", "settings", "put", "system", "screen_off_timeout", "600000"], dev)
    run_adb(["shell", "svc", "power", "stayon", "true"], dev)
    ensure_screen_on(dev)

    # -------------------------------------------------------------
    # ẢNH 1: Khởi đầu (Chưa kích hoạt)
    # -------------------------------------------------------------
    print("[1/4] Chụp Ảnh 1: Trạng thái ban đầu chưa kích hoạt...")
    run_adb(["shell", "pm", "clear", "com.example.offlinelicensingmodel"], dev)
    time.sleep(1.5)
    ensure_screen_on(dev)
    run_adb(["shell", "am", "start", "-n", "com.example.offlinelicensingmodel/.MainActivity"], dev)
    time.sleep(2.5)
    capture(dev, "/sdcard/demo_01.png", "demo_01_khoi_dau_chua_kich_hoat.png")

    # -------------------------------------------------------------
    # ẢNH 3: Kích hoạt thành công gói PRO (Hợp lệ)
    # -------------------------------------------------------------
    print("[2/4] Chụp Ảnh 3: Kích hoạt thành công gói PRO...")
    with open("tools/license_tool/license_real_mt90.lic", "r", encoding="utf-8") as f:
        valid_token = f.read().strip()
    ensure_screen_on(dev)
    run_adb(["shell", "am", "start", "-S", "-n", "com.example.offlinelicensingmodel/.MainActivity", "--es", "ACTIVATE_TOKEN", valid_token], dev)
    time.sleep(2.5)
    capture(dev, "/sdcard/demo_03.png", "demo_03_kich_hoat_thanh_cong.png")

    # -------------------------------------------------------------
    # ẢNH 4: Chặn License giả mạo (Invalid Signature)
    # -------------------------------------------------------------
    print("[3/4] Chụp Ảnh 4: Chặn License giả mạo...")
    with open("tools/license_tool/test_cases/CASE_1_TAMPERED_DATA.lic", "r", encoding="utf-8") as f:
        fake_token = f.read().strip()
    ensure_screen_on(dev)
    run_adb(["shell", "am", "start", "-S", "-n", "com.example.offlinelicensingmodel/.MainActivity", "--es", "ACTIVATE_TOKEN", fake_token], dev)
    time.sleep(2.5)
    capture(dev, "/sdcard/demo_04.png", "demo_04_chan_license_gia_mao.png")

    # -------------------------------------------------------------
    # ẢNH 5: Chặn dùng chéo máy (Device Mismatch)
    # -------------------------------------------------------------
    print("[4/4] Chụp Ảnh 5: Chặn dùng chéo máy...")
    with open("tools/license_tool/test_cases/CASE_2_DEVICE_MISMATCH.lic", "r", encoding="utf-8") as f:
        mismatch_token = f.read().strip()
    ensure_screen_on(dev)
    run_adb(["shell", "am", "start", "-S", "-n", "com.example.offlinelicensingmodel/.MainActivity", "--es", "ACTIVATE_TOKEN", mismatch_token], dev)
    time.sleep(2.5)
    capture(dev, "/sdcard/demo_05.png", "demo_05_chan_dung_cheo_may.png")

    # Khôi phục lại trạng thái Hợp Lệ cho máy MT90
    print("[+] Khôi phục trạng thái bản quyền Hợp Lệ cho MT90...")
    ensure_screen_on(dev)
    run_adb(["shell", "am", "start", "-S", "-n", "com.example.offlinelicensingmodel/.MainActivity", "--es", "ACTIVATE_TOKEN", valid_token], dev)

    # Sao chép vào thư mục Artifacts
    artifact_dir = r"C:\Users\DELL\.gemini\antigravity\brain\4e16a57e-ebae-473a-8104-40e07157e275"
    if os.path.exists(artifact_dir):
        for img in ["demo_01_khoi_dau_chua_kich_hoat.png", "demo_03_kich_hoat_thanh_cong.png", "demo_04_chan_license_gia_mao.png", "demo_05_chan_dung_cheo_may.png"]:
            if os.path.exists(img):
                shutil.copy2(img, os.path.join(artifact_dir, img))

    print("[OK] Hoàn tất chụp và đồng bộ toàn bộ ảnh thực tế sắc nét!")

if __name__ == "__main__":
    main()
