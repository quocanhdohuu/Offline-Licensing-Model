import os
import sys
import time
import subprocess
import xml.etree.ElementTree as ET

SERIAL = "NMS211XE3405E0111"
TEST_CASES_DIR = r"tools\license_tool\test_cases_imin"
ARTIFACTS_DIR = r"C:\Users\DELL\.gemini\antigravity\brain\4e16a57e-ebae-473a-8104-40e07157e275"

cases = [
    ("CASE_0_VALID", "HỢP LỆ (GÓI PRO)"),
    ("CASE_1_TAMPERED_PAYLOAD", "CHỮ KÝ KHÔNG HỢP LỆ"),
    ("CASE_2_DEVICE_MISMATCH", "SAI THIẾT BỊ (DEVICE MISMATCH)"),
    ("CASE_3_FAKE_SIGNATURE", "CHỮ KÝ KHÔNG HỢP LỆ"),
    ("CASE_4_EXPIRED_LICENSE", "BẢN QUYỀN ĐÃ HẾT HẠN"),
]

def adb(cmd):
    full_cmd = f'adb -s {SERIAL} {cmd}'
    res = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, encoding='utf-8')
    return res.stdout.strip()

print("=" * 70)
print(f" TIẾN HÀNH KIỂM THỬ THỰC TẾ TRÊN MÁY iMin Swift2 [{SERIAL}]")
print("=" * 70)

adb("shell am start -n com.example.offlinelicensingmodel/.MainActivity")
time.sleep(1)

results = []

for case_name, expected_status in cases:
    lic_file = os.path.join(TEST_CASES_DIR, f"{case_name}.lic")
    with open(lic_file, "r", encoding="utf-8") as f:
        token = f.read().strip()
    
    # 1. Send scan broadcast to fill and trigger validation
    broadcast_cmd = f'shell am broadcast -a com.symbol.datawedge.ACTION --es com.symbol.datawedge.data_string "{token}"'
    adb(broadcast_cmd)
    time.sleep(1)

    # 2. Tap "Kích Hoạt Thủ Công" at (204, 515)
    adb("shell input tap 204 515")
    time.sleep(1)

    # 3. Scroll to top to ensure status is in viewport
    adb("shell input swipe 360 200 360 1200")
    time.sleep(0.5)

    # 4. Dump UI
    adb("shell uiautomator dump /sdcard/dump.xml")
    adb(f"pull /sdcard/dump.xml imin_{case_name}.xml")

    status_text = "UNKNOWN"
    details_text = ""
    try:
        tree = ET.parse(f"imin_{case_name}.xml")
        root = tree.getroot()
        for node in root.iter("node"):
            r_id = node.attrib.get("resource-id", "")
            if "tv_license_status" in r_id:
                status_text = node.attrib.get("text", "")
            elif "tv_license_details" in r_id:
                details_text = node.attrib.get("text", "")
    except Exception as e:
        status_text = f"XML_ERROR: {e}"

    # Screenshot
    shot_path = os.path.join(ARTIFACTS_DIR, f"imin_{case_name}.png")
    adb("shell screencap -p /sdcard/shot.png")
    adb(f"pull /sdcard/shot.png \"{shot_path}\"")

    is_pass = expected_status in status_text
    results.append({
        "case": case_name,
        "expected": expected_status,
        "actual": status_text,
        "details": details_text,
        "pass": is_pass,
        "shot": shot_path
    })

    print(f"[{'PASS' if is_pass else 'FAIL'}] {case_name}")
    print(f"   Kỳ vọng: {expected_status}")
    print(f"   Thực tế: {status_text}")
    print("-" * 70)

print("\n" + "=" * 70)
print(" TỔNG HỢP KẾT QUẢ KIỂM THỬ TRÊN MÁY iMin Swift2 (I23M01):")
print("=" * 70)
all_pass = all(r["pass"] for r in results)
for r in results:
    p_str = "[OK] PASS" if r["pass"] else "[X] FAIL"
    print(f"{p_str:10} | {r['case']:25} | {r['actual']}")

print("=" * 70)
if all_pass:
    print(">>> TẤT CẢ 5/5 KỊCH BẢN BẢO MẬT ĐỀU ĐẠT CHUẨN 100%! <<<")
else:
    print(">>> CÓ KỊCH BẢN CHƯA ĐẠT! <<<")

