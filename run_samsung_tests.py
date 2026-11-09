import subprocess
import time
import re

DEVICE = "R92X41LE48X"

def run_adb(cmd):
    full_cmd = ["adb", "-s", DEVICE] + cmd
    return subprocess.run(full_cmd, capture_output=True, text=True)

cases = [
    ("CASE_0_VALID", "Kích hoạt license hợp lệ Ed25519 cho DF 8H64-68F2-85K9-22M0"),
    ("CASE_1_TAMPERED", "Tấn công sửa đổi Payload (Gói Enterprise 10 năm)"),
    ("CASE_2_MISMATCH", "Tấn công dùng chéo máy (Nạp mã của Newland MT90)"),
    ("CASE_3_FAKESIG", "Tấn công ký bằng khóa giả (Fake Private Key)"),
    ("CASE_4_EXPIRED", "Bản quyền đã hết hạn sử dụng 30 ngày trước")
]

results = []

for case_name, description in cases:
    with open(f"samsung_{case_name}.lic", "r", encoding="utf-8") as f:
        token = f.read().strip()

    # Clear logcat
    run_adb(["logcat", "-c"])

    # Force stop app
    run_adb(["shell", "am", "force-stop", "com.example.offlinelicensingmodel"])

    # Launch app with ACTIVATE_TOKEN extra
    run_adb(["shell", "am", "start", "-n", "com.example.offlinelicensingmodel/.MainActivity", "--es", "ACTIVATE_TOKEN", token])
    time.sleep(1.5)

    # Capture logcat
    log = run_adb(["logcat", "-d", "-s", "OLM_DF:V"]).stdout

    # Parse result
    status_match = re.search(r"INTENT_ACTIVATION_RESULT:\s*([A-Z_]+)\s*-\s*(.+)", log)
    if status_match:
        status_code = status_match.group(1)
        message = status_match.group(2)
    else:
        status_code = "UNKNOWN"
        message = log.strip()

    # Take screenshot for proof
    shot_name = f"samsung_{case_name}.png"
    run_adb(["shell", "screencap", "-p", f"/sdcard/{shot_name}"])
    run_adb(["pull", f"/sdcard/{shot_name}", f"C:\\Users\\DELL\\.gemini\\antigravity\\brain\\4e16a57e-ebae-473a-8104-40e07157e275\\{shot_name}"])

    results.append({
        "case": case_name,
        "description": description,
        "status_code": status_code,
        "message": message
    })
    print(f"[{case_name}] -> Status: {status_code} | Msg: {message}")

# Also test pm clear (simulated app data clear)
print("\n--- Testing pm clear (App Data Clear) ---")
run_adb(["shell", "pm", "clear", "com.example.offlinelicensingmodel"])
run_adb(["logcat", "-c"])
run_adb(["shell", "monkey", "-p", "com.example.offlinelicensingmodel", "-c", "android.intent.category.LAUNCHER", "1"])
time.sleep(1.5)
log_after_clear = run_adb(["logcat", "-d", "-s", "OLM_DF:V"]).stdout
df_match = re.search(r"ACTUAL_PDA_DF:\s*([A-Z0-9-]+)", log_after_clear)
df_after_clear = df_match.group(1) if df_match else "UNKNOWN"

# Re-activate with Case 0 to prove re-activatability
run_adb(["shell", "am", "force-stop", "com.example.offlinelicensingmodel"])
with open("samsung_CASE_0_VALID.lic", "r", encoding="utf-8") as f:
    token0 = f.read().strip()
run_adb(["shell", "am", "start", "-n", "com.example.offlinelicensingmodel/.MainActivity", "--es", "ACTIVATE_TOKEN", token0])
time.sleep(1.5)

shot_reset = "samsung_factory_reset_success.png"
run_adb(["shell", "screencap", "-p", f"/sdcard/{shot_reset}"])
run_adb(["pull", f"/sdcard/{shot_reset}", f"C:\\Users\\DELL\\.gemini\\antigravity\\brain\\4e16a57e-ebae-473a-8104-40e07157e275\\{shot_reset}"])

print(f"DF after pm clear: {df_after_clear} (Expected: 8H64-68F2-85K9-22M0)")

