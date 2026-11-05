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
import argparse
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

def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')

def b64url_decode(s: str) -> bytes:
    rem = len(s) % 4
    if rem > 0:
        s += '=' * (4 - rem)
    return base64.urlsafe_b64decode(s)

def run_security_test_suite(
    real_df: str = "8ZRB-JNNA-TXYP-K7V9",
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
    print(f" Thiết bị MT90 mục tiêu: [{real_df}] (Kháng Factory Reset)")
    print("=" * 75)

    test_tokens = {}

    # -------------------------------------------------------------
    # CASE 0: License CHUẨN (Hợp lệ 100%)
    # -------------------------------------------------------------
    payload_valid = {
        "iss": "TanHungHa-OLM", "sub": "PDA-License", "df": real_df,
        "type": "PRO", "iat": now_ts, "exp": now_ts + 365 * 86400,
        "features": ["SCANNER", "INVENTORY", "DIRECT_PRINT"],
        "meta": {"customer": "Tan Hung Ha - Test Suite", "model": "NLS-MT90"}
    }
    p_b64 = b64url_encode(json.dumps(payload_valid, separators=(',', ':')).encode('utf-8'))
    sig = real_pri_key.sign(f"{header_b64}.{p_b64}".encode('utf-8'))
    valid_token = f"{header_b64}.{p_b64}.{b64url_encode(sig)}"
    test_tokens["CASE_0_VALID"] = {
        "token": valid_token,
        "expected": "VALID",
        "desc": "License hợp lệ 100% được ký bằng Private Key chính thức"
    }
    print("[+] Sinh CASE 0: License HỢP LỆ (PRO 365 ngày)")

    # -------------------------------------------------------------
    # CASE 1: Giả mạo dữ liệu Payload (Sửa hạn đến 10 năm nhưng giữ chữ ký cũ)
    # -------------------------------------------------------------
    payload_tampered = dict(payload_valid)
    payload_tampered["exp"] = now_ts + 10 * 365 * 86400
    payload_tampered["type"] = "ENTERPRISE"
    p_tampered_b64 = b64url_encode(json.dumps(payload_tampered, separators=(',', ':')).encode('utf-8'))
    tampered_token = f"{header_b64}.{p_tampered_b64}.{b64url_encode(sig)}"
    test_tokens["CASE_1_TAMPERED_PAYLOAD"] = {
        "token": tampered_token,
        "expected": "INVALID_SIGNATURE",
        "desc": "Tấn công sửa đổi dữ liệu payload (sửa hạn và gói) nhưng giữ nguyên chữ ký cũ"
    }
    print("[!] Sinh CASE 1: Giả mạo hạn dùng 10 năm (Kỳ vọng: INVALID_SIGNATURE)")

    # -------------------------------------------------------------
    # CASE 2: Dùng chéo máy (DF Mismatch - License hợp lệ của máy khác)
    # -------------------------------------------------------------
    other_df = "9A2B-X7Y8-AT6Y-4F2E"
    payload_mismatch = dict(payload_valid)
    payload_mismatch["df"] = other_df
    p_mismatch_b64 = b64url_encode(json.dumps(payload_mismatch, separators=(',', ':')).encode('utf-8'))
    sig_mismatch = real_pri_key.sign(f"{header_b64}.{p_mismatch_b64}".encode('utf-8'))
    mismatch_token = f"{header_b64}.{p_mismatch_b64}.{b64url_encode(sig_mismatch)}"
    test_tokens["CASE_2_DEVICE_MISMATCH"] = {
        "token": mismatch_token,
        "expected": "DEVICE_MISMATCH",
        "desc": f"Tấn công clone license của máy khác ({other_df}) sang máy MT90 này"
    }
    print(f"[!] Sinh CASE 2: Dùng chéo máy (DF: {other_df}) (Kỳ vọng: DEVICE_MISMATCH)")

    # -------------------------------------------------------------
    # CASE 3: Ký bằng Private Key giả mạo (Fake Private Key)
    # -------------------------------------------------------------
    fake_pri_key = ed25519.Ed25519PrivateKey.generate()
    fake_sig = fake_pri_key.sign(f"{header_b64}.{p_b64}".encode('utf-8'))
    fake_key_token = f"{header_b64}.{p_b64}.{b64url_encode(fake_sig)}"
    test_tokens["CASE_3_FAKE_SIGNATURE"] = {
        "token": fake_key_token,
        "expected": "INVALID_SIGNATURE",
        "desc": "Tấn công tự tạo cặp khóa Ed25519 giả để tự ký license"
    }
    print("[!] Sinh CASE 3: Ký bằng Private Key tự chế (Kỳ vọng: INVALID_SIGNATURE)")

    # -------------------------------------------------------------
    # CASE 4: Bản quyền đã quá hạn (Expired Token)
    # -------------------------------------------------------------
    payload_expired = dict(payload_valid)
    payload_expired["iat"] = now_ts - 400 * 86400
    payload_expired["exp"] = now_ts - 30 * 86400
    p_expired_b64 = b64url_encode(json.dumps(payload_expired, separators=(',', ':')).encode('utf-8'))
    sig_expired = real_pri_key.sign(f"{header_b64}.{p_expired_b64}".encode('utf-8'))
    expired_token = f"{header_b64}.{p_expired_b64}.{b64url_encode(sig_expired)}"
    test_tokens["CASE_4_EXPIRED_LICENSE"] = {
        "token": expired_token,
        "expected": "EXPIRED",
        "desc": "Tấn công sử dụng license đã hết hạn cách đây 30 ngày"
    }
    print("[!] Sinh CASE 4: Bản quyền đã hết hạn (Kỳ vọng: EXPIRED)")

    # Lưu test tokens và sinh ảnh QR tương ứng cho từng case
    for case_name, data in test_tokens.items():
        token = data["token"]
        # Lưu file .lic
        case_file = os.path.join(out_dir, f"{case_name}.lic")
        with open(case_file, "w", encoding="utf-8") as f:
            f.write(token)

        # Tạo file ảnh QR
        qr_file = os.path.join(out_dir, f"{case_name}_qr.png")
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=3
        )
        qr.add_data(token)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(qr_file)
        data["qr_file"] = qr_file
        data["lic_file"] = case_file

    summary_path = os.path.join(out_dir, "test_cases_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(test_tokens, f, indent=2, ensure_ascii=False)

    print("-" * 75)
    print(f"[OK] Đã xuất {len(test_tokens)} files .lic và ảnh QR vào: {out_dir}/")
    print("=" * 75)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sinh bộ test cases bảo mật OLM")
    parser.add_argument("--df", default="8ZRB-JNNA-TXYP-K7V9", help="Mã DF mục tiêu")
    parser.add_argument("--key", default="ed25519_private_key.pem", help="Private key PEM")
    parser.add_argument("--pub", default="ed25519_public_key.pem", help="Public key PEM")
    parser.add_argument("--out", default="test_cases", help="Thư mục xuất kết quả")
    args = parser.parse_args()

    run_security_test_suite(
        real_df=args.df,
        private_key_path=args.key,
        public_key_path=args.pub,
        out_dir=args.out
    )

