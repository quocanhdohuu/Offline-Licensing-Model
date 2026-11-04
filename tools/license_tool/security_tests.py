#!/usr/bin/env python3
"""
Tân Hưng Hà - Offline Licensing Model (OLM)
Module: Bộ Kịch Bản Kiểm Thử Bảo Mật (Security Test Suite - IT1 đến IT5)

Tự động sinh các mẫu Token tấn công để kiểm thử 4 lớp phòng thủ trên ứng dụng PDA:
1. TC1: Giả mạo dữ liệu (Sửa hạn dùng/gói license nhưng giữ nguyên chữ ký số Ed25519)
2. TC2: Dùng chéo máy (DF Mismatch - License hợp lệ nhưng cấp cho máy khác)
3. TC3: Ký bằng Private Key giả mạo (Fake Authority)
4. TC4: Bản quyền quá hạn (Expired Token)
5. TC5: Bản quyền tương lai chưa đến hạn (Not yet valid)
"""

import os
import sys
import json
import base64
from datetime import datetime, timezone, timedelta
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')

def b64url_decode(s: str) -> bytes:
    rem = len(s) % 4
    if rem > 0:
        s += '=' * (4 - rem)
    return base64.urlsafe_b64decode(s)

def run_security_test_suite(
    real_df: str = "MN73-006Q-5G96-S3E8",
    private_key_path: str = "ed25519_private_key.pem",
    public_key_path: str = "ed25519_public_key.pem",
    out_dir: str = "test_cases"
):
    os.makedirs(out_dir, exist_ok=True)

    with open(private_key_path, "rb") as f:
        real_pri_key = serialization.load_pem_private_key(f.read(), password=None)
    with open(public_key_path, "rb") as f:
        real_pub_key = serialization.load_pem_public_key(f.read())

    now_ts = int(datetime.now(timezone.utc).timestamp())
    header = {"alg": "EdDSA", "typ": "JWT"}
    header_b64 = b64url_encode(json.dumps(header, separators=(',', ':')).encode('utf-8'))

    print("=" * 75)
    print(" BẮT ĐẦU SINH BỘ TEST CASES BẢO MẬT CHO OLM (TÂN HƯNG HÀ)")
    print(f" Thiết bị MT90 mục tiêu: [{real_df}]")
    print("=" * 75)

    test_tokens = {}

    # -------------------------------------------------------------
    # CASE 0: License CHUẨN (Hợp lệ 100%)
    # -------------------------------------------------------------
    payload_valid = {
        "iss": "TanHungHa-OLM", "sub": "PDA-License", "df": real_df,
        "type": "PRO", "iat": now_ts, "exp": now_ts + 365 * 86400,
        "features": ["SCANNER", "INVENTORY", "DIRECT_PRINT"]
    }
    p_b64 = b64url_encode(json.dumps(payload_valid, separators=(',', ':')).encode('utf-8'))
    sig = real_pri_key.sign(f"{header_b64}.{p_b64}".encode('utf-8'))
    valid_token = f"{header_b64}.{p_b64}.{b64url_encode(sig)}"
    test_tokens["CASE_0_VALID"] = valid_token
    print("[+] Sinh CASE 0: License HỢP LỆ (PRO 365 ngày)")

    # -------------------------------------------------------------
    # CASE 1: Giả mạo dữ liệu Payload (Sửa hạn đến 2035 nhưng giữ chữ ký cũ)
    # -------------------------------------------------------------
    payload_tampered = dict(payload_valid)
    payload_tampered["exp"] = now_ts + 10 * 365 * 86400 # 10 năm
    payload_tampered["type"] = "ENTERPRISE"
    p_tampered_b64 = b64url_encode(json.dumps(payload_tampered, separators=(',', ':')).encode('utf-8'))
    # Giữ nguyên chữ ký của payload cũ
    tampered_token = f"{header_b64}.{p_tampered_b64}.{b64url_encode(sig)}"
    test_tokens["CASE_1_TAMPERED_DATA"] = tampered_token
    print("[!] Sinh CASE 1: Giả mạo hạn dùng 10 năm (Kỳ vọng: INVALID_SIGNATURE)")

    # -------------------------------------------------------------
    # CASE 2: Dùng chéo máy (DF Mismatch - License hợp lệ của máy khác)
    # -------------------------------------------------------------
    fake_df = "9A2B-X7Y8-AT6Y-4F2E"
    payload_mismatch = dict(payload_valid)
    payload_mismatch["df"] = fake_df
    p_mismatch_b64 = b64url_encode(json.dumps(payload_mismatch, separators=(',', ':')).encode('utf-8'))
    sig_mismatch = real_pri_key.sign(f"{header_b64}.{p_mismatch_b64}".encode('utf-8'))
    mismatch_token = f"{header_b64}.{p_mismatch_b64}.{b64url_encode(sig_mismatch)}"
    test_tokens["CASE_2_DEVICE_MISMATCH"] = mismatch_token
    print(f"[!] Sinh CASE 2: Dùng chéo máy (DF: {fake_df}) (Kỳ vọng: DEVICE_MISMATCH)")

    # -------------------------------------------------------------
    # CASE 3: Ký bằng Private Key giả mạo (Fake Private Key)
    # -------------------------------------------------------------
    fake_pri_key = ed25519.Ed25519PrivateKey.generate()
    fake_sig = fake_pri_key.sign(f"{header_b64}.{p_b64}".encode('utf-8'))
    fake_key_token = f"{header_b64}.{p_b64}.{b64url_encode(fake_sig)}"
    test_tokens["CASE_3_FAKE_KEY"] = fake_key_token
    print("[!] Sinh CASE 3: Ký bằng Private Key tự chế (Kỳ vọng: INVALID_SIGNATURE)")

    # -------------------------------------------------------------
    # CASE 4: Bản quyền đã quá hạn (Expired Token)
    # -------------------------------------------------------------
    payload_expired = dict(payload_valid)
    payload_expired["iat"] = now_ts - 400 * 86400
    payload_expired["exp"] = now_ts - 30 * 86400 # Hết hạn 30 ngày trước
    p_expired_b64 = b64url_encode(json.dumps(payload_expired, separators=(',', ':')).encode('utf-8'))
    sig_expired = real_pri_key.sign(f"{header_b64}.{p_expired_b64}".encode('utf-8'))
    expired_token = f"{header_b64}.{p_expired_b64}.{b64url_encode(sig_expired)}"
    test_tokens["CASE_4_EXPIRED"] = expired_token
    print("[!] Sinh CASE 4: Bản quyền đã hết hạn (Kỳ vọng: EXPIRED)")

    # Lưu toàn bộ test cases ra file json
    summary_path = os.path.join(out_dir, "test_cases_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(test_tokens, f, indent=2)

    for case_name, token in test_tokens.items():
        case_file = os.path.join(out_dir, f"{case_name}.lic")
        with open(case_file, "w", encoding="utf-8") as f:
            f.write(token)

    print("-" * 75)
    print(f"[OK] Đã xuất toàn bộ file kiểm thử vào thư mục: {out_dir}/")
    print("=" * 75)

if __name__ == "__main__":
    run_security_test_suite()

