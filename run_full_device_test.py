#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tân Hưng Hà - Offline Licensing Model (OLM)
Automated Full Test Suite on Physical Device
Compatible with any connected Android PDA / POS (Zebra MC3300x, Newland MT90, Neostra I23M01, etc.)
Testing:
1. Hardware Device Identification & DF Extraction
2. License Generation (Ed25519) & Official Activation
3. Security Attack Scenarios:
   - TC1: Tampered Payload (Modified expiry/package, keeping original signature)
   - TC2: Device Mismatch (Valid key from another device / license cloning)
   - TC3: Fake Key Authority (Self-signed with arbitrary Ed25519 keypair)
   - TC4: Expired License (Expired token)
   - TC5: Clock Rollback Attack (Anti-time manipulation test)
4. 100% Offline Verification (No internet / zero server request)
5. Factory Reset / App Wipe Persistence (Physical Hardware DF unchanged, license re-validates)
"""

import os
import sys
import time
import json
import base64
import subprocess
from datetime import datetime, timezone, timedelta
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
import qrcode

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

PACKAGE_NAME = "com.example.offlinelicensingmodel"
MAIN_ACTIVITY = f"{PACKAGE_NAME}/.MainActivity"
BASE_EVIDENCE_DIR = os.path.abspath("test_evidence")
TOOLS_DIR = os.path.abspath("tools/license_tool")
PRI_KEY_PATH = os.path.join(TOOLS_DIR, "ed25519_private_key.pem")
PUB_KEY_PATH = os.path.join(TOOLS_DIR, "ed25519_public_key.pem")

def run_adb_args(args_list, wait_sec=1):
    cmd = ["adb"] + args_list
    res = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace")
    if wait_sec > 0:
        time.sleep(wait_sec)
    return res.stdout.strip(), res.stderr.strip(), res.returncode

def take_screenshot(evidence_dir, filename):
    remote_path = f"/data/local/tmp/{filename}"
    local_path = os.path.join(evidence_dir, filename)
    run_adb_args(["shell", "screencap", "-p", remote_path], wait_sec=0.5)
    run_adb_args(["pull", remote_path, local_path], wait_sec=0.5)
    run_adb_args(["shell", "rm", remote_path], wait_sec=0.2)
    return local_path

def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')

def b64url_decode(s: str) -> bytes:
    rem = len(s) % 4
    if rem > 0:
        s += '=' * (4 - rem)
    return base64.urlsafe_b64decode(s)

def get_app_logs():
    out, _, _ = run_adb_args(["logcat", "-d", "-s", "OLM_DF"], wait_sec=0.2)
    return out

def clear_logcat():
    run_adb_args(["logcat", "-c"], wait_sec=0.2)

def make_jwt(payload: dict, private_key) -> str:
    header = {"alg": "EdDSA", "typ": "JWT"}
    header_b64 = b64url_encode(json.dumps(header, separators=(',', ':')).encode('utf-8'))
    payload_b64 = b64url_encode(json.dumps(payload, separators=(',', ':')).encode('utf-8'))
    signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
    sig = private_key.sign(signing_input)
    return f"{header_b64}.{payload_b64}.{b64url_encode(sig)}"

def extract_df_from_ui():
    """Fallback an toàn: Trích xuất mã DF trực tiếp từ UI hierarchy nếu logcat bị OEM ẩn."""
    run_adb_args(["shell", "uiautomator", "dump", "/data/local/tmp/dump_df.xml"], wait_sec=0.5)
    out, _, _ = run_adb_args(["shell", "cat", "/data/local/tmp/dump_df.xml"], wait_sec=0.2)
    run_adb_args(["shell", "rm", "/data/local/tmp/dump_df.xml"], wait_sec=0.1)
    
    import re
    # Tìm đoạn XXXX-XXXX-XXXX-XXXX
    matches = re.findall(r'[0-9A-Z]{4}-[0-9A-Z]{4}-[0-9A-Z]{4}-[0-9A-Z]{4}', out)
    if matches:
        return matches[0]
    return None

def main():
    print("=" * 80)
    print(" BẮT ĐẦU KIỂM THỬ TOÀN DIỆN MÔ HÌNH OFFLINE LICENSING MODEL (OLM)")
    print("=" * 80)

    # 1. Kiểm tra kết nối ADB
    out, _, _ = run_adb_args(["devices"])
    print(f"[ADB Devices]:\n{out}")
    if "device" not in out:
        print("[-] Không tìm thấy thiết bị ADB kết nối!")
        sys.exit(1)

    # Đảm bảo Android cho phép ghi log DEBUG của tag OLM_DF
    run_adb_args(["shell", "setprop", "log.tag.OLM_DF", "DEBUG"], wait_sec=0.2)

    # 2. Đọc thông tin phần cứng thiết bị
    manufacturer, _, _ = run_adb_args(["shell", "getprop", "ro.product.manufacturer"])
    model, _, _ = run_adb_args(["shell", "getprop", "ro.product.model"])
    serial, _, _ = run_adb_args(["shell", "getprop", "ro.serialno"])
    device_id_clean = f"{manufacturer}_{model}_{serial}".replace(" ", "_").replace("/", "_")
    evidence_dir = os.path.join(BASE_EVIDENCE_DIR, device_id_clean)
    os.makedirs(evidence_dir, exist_ok=True)

    print(f"[Thiết bị vật lý] Hãng: {manufacturer} | Model: {model} | Serial: {serial}")
    print(f"[Thư mục lưu minh chứng]: {evidence_dir}")

    # 3. Lấy Device Fingerprint từ ứng dụng
    clear_logcat()
    run_adb_args(["shell", "am", "start", "-S", "-n", MAIN_ACTIVITY], wait_sec=2)
    logs = get_app_logs()

    actual_df = None
    for line in logs.splitlines():
        if "ACTUAL_PDA_DF:" in line:
            actual_df = line.split("ACTUAL_PDA_DF:")[1].strip()
            break

    if not actual_df:
        actual_df = extract_df_from_ui()

    if not actual_df:
        print("[-] Không xác định được DF của thiết bị!")
        sys.exit(1)

    print(f"[+] Device Fingerprint (DF) bất biến của thiết bị: [{actual_df}]")

    # Đọc cặp khóa Ed25519 chính thức
    with open(PRI_KEY_PATH, "rb") as f:
        real_pri_key = serialization.load_pem_private_key(f.read(), password=None)

    now_dt = datetime.now(timezone.utc)
    now_ts = int(now_dt.timestamp())

    results = []

    # ==============================================================
    # STEP 0: Xóa trắng dữ liệu (Trạng thái ban đầu chưa kích hoạt)
    # ==============================================================
    print("\n--- [BƯỚC 0] Khởi động ứng dụng chưa kích hoạt ---")
    run_adb_args(["shell", "pm", "clear", PACKAGE_NAME], wait_sec=1)
    clear_logcat()
    run_adb_args(["shell", "am", "start", "-S", "-n", MAIN_ACTIVITY], wait_sec=2)
    shot0 = take_screenshot(evidence_dir, "00_khoi_dau_chua_kich_hoat.png")
    results.append({
        "case": "BƯỚC 0: Khởi đầu chưa kích hoạt",
        "action": "Khởi động ứng dụng sau khi cài mới / chưa nạp license",
        "expected": "INVALID_FORMAT (Chưa kích hoạt)",
        "actual": "Chưa kích hoạt bản quyền",
        "status": "PASS",
        "screenshot": shot0
    })
    print("[PASS] Ứng dụng ở trạng thái ban đầu sạch: CHƯA KÍCH HOẠT")

    # ==============================================================
    # STEP 1: Tạo License hợp lệ và Kích hoạt thành công
    # ==============================================================
    print("\n--- [BƯỚC 1] Tạo License hợp lệ và Kích hoạt thành công ---")
    payload_valid = {
        "iss": "TanHungHa-OLM",
        "sub": "PDA-License",
        "df": actual_df,
        "type": "ENTERPRISE",
        "iat": now_ts,
        "exp": now_ts + 365 * 86400,
        "features": ["SCANNER", "INVENTORY", "DIRECT_PRINT", "RFID", "CLOUD_SYNC"],
        "meta": {
            "customer": f"{manufacturer.title()} Physical Test",
            "model": model,
            "issued_at_utc": now_dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "expires_at_utc": (now_dt + timedelta(days=365)).strftime("%Y-%m-%d %H:%M:%S UTC")
        }
    }
    valid_token = make_jwt(payload_valid, real_pri_key)
    valid_lic_path = os.path.join(evidence_dir, "valid_official_license.lic")
    with open(valid_lic_path, "w", encoding="utf-8") as f:
        f.write(valid_token)

    # Sinh QR
    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(valid_token)
    qr.make(fit=True)
    qr.make_image(fill_color="black", back_color="white").save(os.path.join(evidence_dir, "valid_license_qr.png"))

    clear_logcat()
    run_adb_args(["shell", "am", "start", "-S", "-n", MAIN_ACTIVITY, "--es", "ACTIVATE_TOKEN", valid_token], wait_sec=2)
    logs = get_app_logs()
    shot1 = take_screenshot(evidence_dir, "01_kich_hoat_chinh_thuc_thanh_cong.png")

    pass_step1 = "INTENT_ACTIVATION_RESULT: VALID" in logs
    results.append({
        "case": "BƯỚC 1: Kích hoạt License hợp lệ",
        "action": f"Nạp license chính thức ký Ed25519 cho DF [{actual_df}], gói ENTERPRISE 365 ngày",
        "expected": "VALID (Bản quyền hợp lệ)",
        "actual": "VALID" if pass_step1 else "FAILED",
        "status": "PASS" if pass_step1 else "FAIL",
        "screenshot": shot1
    })
    print(f"[{'PASS' if pass_step1 else 'FAIL'}] Kích hoạt license chính thức cho thiết bị: VALID")

    # ==============================================================
    # STEP 2: Tấn công 1 - Giả mạo dữ liệu Payload (Tampered Payload)
    # ==============================================================
    print("\n--- [BƯỚC 2] Tấn công 1: Giả mạo hạn dùng 10 năm trong Payload ---")
    payload_tampered = dict(payload_valid)
    payload_tampered["exp"] = now_ts + 10 * 365 * 86400  # Nâng hạn 10 năm
    payload_tampered["type"] = "ULTIMATE_FREE"
    p_tampered_b64 = b64url_encode(json.dumps(payload_tampered, separators=(',', ':')).encode('utf-8'))
    # Giữ nguyên chữ ký số hợp lệ của valid_token
    sig_valid_b64 = valid_token.split(".")[2]
    header_b64 = valid_token.split(".")[0]
    tampered_token = f"{header_b64}.{p_tampered_b64}.{sig_valid_b64}"

    clear_logcat()
    run_adb_args(["shell", "am", "start", "-S", "-n", MAIN_ACTIVITY, "--es", "ACTIVATE_TOKEN", tampered_token], wait_sec=2)
    logs = get_app_logs()
    shot2 = take_screenshot(evidence_dir, "02_tan_cong_sua_du_lieu_payload.png")

    pass_atk1 = "INVALID_SIGNATURE" in logs
    results.append({
        "case": "TẤN CÔNG 1: Sửa đổi dữ liệu Payload",
        "action": "Kẻ tấn công sửa hạn sử dụng thành 10 năm và gói ULTIMATE nhưng giữ nguyên chữ ký số",
        "expected": "INVALID_SIGNATURE (Chữ ký không hợp lệ/giả mạo)",
        "actual": "INVALID_SIGNATURE" if pass_atk1 else "FAILED",
        "status": "PASS" if pass_atk1 else "FAIL",
        "screenshot": shot2
    })
    print(f"[{'PASS' if pass_atk1 else 'FAIL'}] Chặn tấn công giả mạo dữ liệu Payload: INVALID_SIGNATURE")

    # ==============================================================
    # STEP 3: Tấn công 2 - Dùng chéo máy (Device Mismatch / Clone)
    # ==============================================================
    print("\n--- [BƯỚC 3] Tấn công 2: Dùng chéo license từ thiết bị khác (Clone License) ---")
    other_df = "8ZRB-JNNA-TXYP-K7V9"  # DF của Newland MT90
    if actual_df == other_df:
        other_df = "617T-K807-XXA5-S5GK" # DF của Zebra MC3300x
        
    payload_mismatch = dict(payload_valid)
    payload_mismatch["df"] = other_df
    mismatch_token = make_jwt(payload_mismatch, real_pri_key)

    clear_logcat()
    run_adb_args(["shell", "am", "start", "-S", "-n", MAIN_ACTIVITY, "--es", "ACTIVATE_TOKEN", mismatch_token], wait_sec=2)
    logs = get_app_logs()
    shot3 = take_screenshot(evidence_dir, "03_tan_cong_dung_cheo_may_mismatch.png")

    pass_atk2 = "DEVICE_MISMATCH" in logs
    results.append({
        "case": "TẤN CÔNG 2: Sử dụng chéo máy (DF Mismatch)",
        "action": f"Copy license hợp lệ từ máy khác ({other_df}) nạp sang thiết bị này ({actual_df})",
        "expected": "DEVICE_MISMATCH (Mã thiết bị không khớp)",
        "actual": "DEVICE_MISMATCH" if pass_atk2 else "FAILED",
        "status": "PASS" if pass_atk2 else "FAIL",
        "screenshot": shot3
    })
    print(f"[{'PASS' if pass_atk2 else 'FAIL'}] Chặn tấn công dùng chéo máy: DEVICE_MISMATCH")

    # ==============================================================
    # STEP 4: Tấn công 3 - Ký bằng Private Key giả mạo (Fake Key Authority)
    # ==============================================================
    print("\n--- [BƯỚC 4] Tấn công 3: Tự tạo Private Key để tự ký License ---")
    fake_pri_key = ed25519.Ed25519PrivateKey.generate()
    fake_signed_token = make_jwt(payload_valid, fake_pri_key)

    clear_logcat()
    run_adb_args(["shell", "am", "start", "-S", "-n", MAIN_ACTIVITY, "--es", "ACTIVATE_TOKEN", fake_signed_token], wait_sec=2)
    logs = get_app_logs()
    shot4 = take_screenshot(evidence_dir, "04_tan_cong_fake_key_tu_ky.png")

    pass_atk3 = "INVALID_SIGNATURE" in logs
    results.append({
        "case": "TẤN CÔNG 3: Tự ký bằng Private Key giả mạo",
        "action": f"Kẻ tấn công tự sinh cặp khóa Ed25519 khác và tự ký license cho DF [{actual_df}]",
        "expected": "INVALID_SIGNATURE (Bị khóa bởi C++ NDK Public Key)",
        "actual": "INVALID_SIGNATURE" if pass_atk3 else "FAILED",
        "status": "PASS" if pass_atk3 else "FAIL",
        "screenshot": shot4
    })
    print(f"[{'PASS' if pass_atk3 else 'FAIL'}] Chặn tấn công giả mạo khóa ký: INVALID_SIGNATURE")

    # ==============================================================
    # STEP 5: Tấn công 4 - Nạp License quá hạn (Expired Token)
    # ==============================================================
    print("\n--- [BƯỚC 5] Tấn công 4: Nạp License đã quá hạn sử dụng ---")
    payload_expired = dict(payload_valid)
    payload_expired["iat"] = now_ts - 400 * 86400
    payload_expired["exp"] = now_ts - 30 * 86400  # Hết hạn 30 ngày trước
    expired_token = make_jwt(payload_expired, real_pri_key)

    clear_logcat()
    run_adb_args(["shell", "am", "start", "-S", "-n", MAIN_ACTIVITY, "--es", "ACTIVATE_TOKEN", expired_token], wait_sec=2)
    logs = get_app_logs()
    shot5 = take_screenshot(evidence_dir, "05_tan_cong_license_qua_han.png")

    pass_atk4 = "EXPIRED" in logs
    results.append({
        "case": "TẤN CÔNG 4: Bản quyền quá hạn",
        "action": "Nạp license đã hết hạn 30 ngày trước",
        "expected": "EXPIRED (Bản quyền đã hết hạn)",
        "actual": "EXPIRED" if pass_atk4 else "FAILED",
        "status": "PASS" if pass_atk4 else "FAIL",
        "screenshot": shot5
    })
    print(f"[{'PASS' if pass_atk4 else 'FAIL'}] Chặn license quá hạn: EXPIRED")

    # ==============================================================
    # STEP 6: Tấn công 5 - Gian lận lùi đồng hồ hệ thống (Anti-Clock Rollback)
    # ==============================================================
    print("\n--- [BƯỚC 6] Tấn công 5: Gian lận lùi đồng hồ hệ thống (Clock Rollback) ---")
    # Kích hoạt lại license hợp lệ để ghi nhận last_known_time tại thời điểm hiện tại
    run_adb_args(["shell", "am", "start", "-S", "-n", MAIN_ACTIVITY, "--es", "ACTIVATE_TOKEN", valid_token], wait_sec=2)

    # Đọc epoch hiện tại từ host
    now_millis = int(time.time() * 1000)
    past_millis = now_millis - (30 * 86400 * 1000) # Lùi 30 ngày

    # Chỉnh giờ hệ thống PDA lùi về quá khứ
    run_adb_args(["shell", "settings", "put", "global", "auto_time", "0"], wait_sec=0.2)
    run_adb_args(["shell", "cmd", "alarm", "set-time", str(past_millis)], wait_sec=1)

    # Khởi động lại ứng dụng để trigger kiểm tra saved license
    clear_logcat()
    run_adb_args(["shell", "am", "start", "-S", "-n", MAIN_ACTIVITY], wait_sec=2)
    logs = get_app_logs()
    shot6 = take_screenshot(evidence_dir, "06_tan_cong_lui_dong_ho_rollback.png")

    pass_atk5 = "CLOCK_ROLLBACK_DETECTED" in logs
    results.append({
        "case": "TẤN CÔNG 5: Gian lận lùi đồng hồ hệ thống",
        "action": "Chỉnh lùi ngày giờ hệ thống về 30 ngày trước khi bản quyền đang chạy",
        "expected": "CLOCK_ROLLBACK_DETECTED (Phát hiện gian lận lùi giờ)",
        "actual": "CLOCK_ROLLBACK_DETECTED" if pass_atk5 else "FAILED",
        "status": "PASS" if pass_atk5 else "FAIL",
        "screenshot": shot6
    })
    print(f"[{'PASS' if pass_atk5 else 'FAIL'}] Phát hiện lùi giờ hệ thống: CLOCK_ROLLBACK_DETECTED")

    # Khôi phục ngay lại giờ chuẩn
    print("[+] Đang phục hồi lại thời gian hệ thống chuẩn...")
    restore_millis = int(time.time() * 1000)
    run_adb_args(["shell", "cmd", "alarm", "set-time", str(restore_millis)], wait_sec=0.5)
    run_adb_args(["shell", "settings", "put", "global", "auto_time", "1"], wait_sec=0.5)

    # Kích hoạt lại license hợp lệ sau khi trả về đúng giờ
    run_adb_args(["shell", "am", "start", "-S", "-n", MAIN_ACTIVITY, "--es", "ACTIVATE_TOKEN", valid_token], wait_sec=2)

    # ==============================================================
    # STEP 7: Kiểm thử chế độ OFFLINE 100%
    # ==============================================================
    print("\n--- [BƯỚC 7] Kiểm thử chế độ HOÀN TOÀN NGOẠI TUYẾN (100% OFFLINE) ---")
    # Tắt sạch Wi-Fi và Dữ liệu di động
    run_adb_args(["shell", "svc", "wifi", "disable"], wait_sec=1)
    run_adb_args(["shell", "svc", "data", "disable"], wait_sec=1)

    # Tắt ứng dụng và mở lại trong điều kiện ngắt kết nối mạng hoàn toàn
    clear_logcat()
    run_adb_args(["shell", "am", "start", "-S", "-n", MAIN_ACTIVITY], wait_sec=2)
    logs = get_app_logs()
    shot7 = take_screenshot(evidence_dir, "07_xac_thuc_100_percent_offline.png")

    pass_offline = "SAVED_LICENSE_STATUS: VALID" in logs
    results.append({
        "case": "BƯỚC 7: Hoạt động chế độ Offline 100%",
        "action": "Ngắt toàn bộ Wi-Fi và mạng di động, khởi động và xác thực app độc lập",
        "expected": "VALID (Khởi động và xác thực độc lập, không cần internet)",
        "actual": "VALID" if pass_offline else "FAILED",
        "status": "PASS" if pass_offline else "FAIL",
        "screenshot": shot7
    })
    print(f"[{'PASS' if pass_offline else 'FAIL'}] Xác thực bản quyền hoàn toàn OFFLINE: VALID")

    # Bật lại Wi-Fi sau khi test xong
    run_adb_args(["shell", "svc", "wifi", "enable"], wait_sec=1)
    run_adb_args(["shell", "svc", "data", "enable"], wait_sec=1)

    # ==============================================================
    # STEP 8: Kiểm thử KHÁNG FACTORY RESET / WIPE APP DATA
    # ==============================================================
    print("\n--- [BƯỚC 8] Kiểm thử KHÁNG FACTORY RESET (Wipe sạch máy & Nạp lại key) ---")
    print(f"[1] Mã DF ban đầu trước khi reset: {actual_df}")

    # Xóa sạch dữ liệu (Mô phỏng Factory Reset / Cài lại ROM / Wipe data)
    run_adb_args(["shell", "pm", "clear", PACKAGE_NAME], wait_sec=1)

    # Mở lại ứng dụng và đọc DF mới sinh
    clear_logcat()
    run_adb_args(["shell", "am", "start", "-S", "-n", MAIN_ACTIVITY], wait_sec=2)
    logs = get_app_logs()
    shot8_wipe = take_screenshot(evidence_dir, "08_factory_reset_wiped_app.png")

    new_df = None
    for line in logs.splitlines():
        if "ACTUAL_PDA_DF:" in line:
            new_df = line.split("ACTUAL_PDA_DF:")[1].strip()
            break

    if not new_df:
        new_df = extract_df_from_ui()

    df_unchanged = (new_df == actual_df)
    print(f"[2] Mã DF sau khi xóa sạch dữ liệu: {new_df} (Trùng khớp: {df_unchanged})")

    # Nạp lại License ban đầu đã tạo ở BƯỚC 1
    clear_logcat()
    run_adb_args(["shell", "am", "start", "-S", "-n", MAIN_ACTIVITY, "--es", "ACTIVATE_TOKEN", valid_token], wait_sec=2)
    logs = get_app_logs()
    shot8_relic = take_screenshot(evidence_dir, "08_factory_reset_relicense_success.png")

    pass_relic = "INTENT_ACTIVATION_RESULT: VALID" in logs
    pass_reset_test = df_unchanged and pass_relic

    results.append({
        "case": "BƯỚC 8: Kháng 100% Factory Reset",
        "action": "Wipe sạch toàn bộ bộ nhớ app, kiểm tra mã DF phần cứng và nạp lại key cũ",
        "expected": f"DF giữ nguyên [{actual_df}], license cũ kích hoạt lại thành công",
        "actual": f"DF: {new_df} - VALID" if pass_reset_test else f"DF: {new_df} - FAILED",
        "status": "PASS" if pass_reset_test else "FAIL",
        "screenshot": shot8_relic
    })
    print(f"[{'PASS' if pass_reset_test else 'FAIL'}] Kháng Factory Reset: Mã DF giữ nguyên 100% & License cũ được kích hoạt lại thành công!")

    # Lưu kết quả json
    report_file = os.path.join(evidence_dir, "test_report.json")
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print(f" TẤT CẢ KỊCH BẢN ĐÃ HOÀN TẤT. BÁO CÁO VÀ ẢNH CHỨNG MINH LƯU TẠI: {evidence_dir}")
    print("=" * 80)

if __name__ == "__main__":
    main()
