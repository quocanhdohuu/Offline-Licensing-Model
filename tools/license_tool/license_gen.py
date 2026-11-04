#!/usr/bin/env python3
"""
Tân Hưng Hà - Offline Licensing Model (OLM)
Module: Sinh License JWT (EdDSA / Ed25519) & Mã QR Code Cho Thiết Bị PDA

Chức năng:
1. Nhận mã Device Fingerprint (16 ký tự Crockford Base32: XXXX-XXXX-XXXX-XXXX).
2. Tạo Header & Payload chuẩn JWT RFC 8037 (EdDSA).
3. Ký số bằng Private Key Ed25519 của Tân Hưng Hà.
4. Tự kiểm chứng tính hợp lệ của chữ ký bằng Public Key trước khi xuất file.
5. Xuất file token (.lic) và hình ảnh mã QR Code (.png).
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

CROCKFORD_ALPHABET = set("0123456789ABCDEFGHJKMNPQRSTVWXYZ")

def b64url_encode(data: bytes) -> str:
    """Mã hóa Base64URL không kèm padding '=' theo chuẩn JWT RFC 7515."""
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')

def b64url_decode(str_data: str) -> bytes:
    """Giải mã Base64URL với tự động bù padding '='."""
    rem = len(str_data) % 4
    if rem > 0:
        str_data += '=' * (4 - rem)
    return base64.urlsafe_b64decode(str_data)

def normalize_df(df_input: str) -> str:
    """Chuẩn hóa và kiểm tra mã DF (loại bỏ khoảng trắng, gạch nối, kiểm tra ký tự Crockford)."""
    cleaned = df_input.strip().upper().replace("-", "").replace(" ", "")
    if len(cleaned) != 16:
        raise ValueError(f"Mã DF phải gồm đúng 16 ký tự Crockford Base32. Độ dài nhận được: {len(cleaned)} ('{cleaned}')")
    for char in cleaned:
        if char not in CROCKFORD_ALPHABET:
            raise ValueError(f"Ký tự không hợp lệ trong mã DF: '{char}'. Bảng Crockford chỉ chấp nhận 0-9 và A-Z (trừ I, L, O, U).")
    # Định dạng lại dạng XXXX-XXXX-XXXX-XXXX
    return f"{cleaned[0:4]}-{cleaned[4:8]}-{cleaned[8:12]}-{cleaned[12:16]}"

def create_license(
    df: str,
    license_type: str = "PRO",
    days_valid: int = 365,
    expiry_date_str: str = None,
    features: list = None,
    customer: str = "Tân Hưng Hà Demo",
    model: str = "NLS-MT90",
    private_key_path: str = "ed25519_private_key.pem",
    public_key_path: str = "ed25519_public_key.pem",
    output_prefix: str = None
):
    if features is None:
        features = ["SCANNER", "INVENTORY", "DIRECT_PRINT"]

    norm_df = normalize_df(df)
    
    # 1. Đọc Private Key
    if not os.path.exists(private_key_path):
        raise FileNotFoundError(f"Không tìm thấy Private Key tại: {private_key_path}. Vui lòng chạy keygen.py trước.")
    
    with open(private_key_path, "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)

    # 2. Xử lý thời gian Issue & Expiry
    now_dt = datetime.now(timezone.utc)
    iat_ts = int(now_dt.timestamp())

    if expiry_date_str:
        exp_dt = datetime.strptime(expiry_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        exp_ts = int(exp_dt.timestamp())
    else:
        exp_dt = now_dt + timedelta(days=days_valid)
        exp_ts = int(exp_dt.timestamp())

    if exp_ts <= iat_ts:
        raise ValueError("Ngày hết hạn phải lớn hơn ngày cấp bản quyền!")

    # 3. Tạo Header & Payload
    header = {
        "alg": "EdDSA",
        "typ": "JWT"
    }

    payload = {
        "iss": "TanHungHa-OLM",
        "sub": "PDA-License",
        "df": norm_df,
        "type": license_type.upper(),
        "iat": iat_ts,
        "exp": exp_ts,
        "features": features,
        "meta": {
            "customer": customer,
            "model": model,
            "issued_at_utc": now_dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "expires_at_utc": exp_dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        }
    }

    # 4. Ký số bằng Ed25519
    header_json = json.dumps(header, separators=(',', ':')).encode('utf-8')
    payload_json = json.dumps(payload, separators=(',', ':')).encode('utf-8')

    header_b64 = b64url_encode(header_json)
    payload_b64 = b64url_encode(payload_json)
    signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')

    signature = private_key.sign(signing_input)
    sig_b64 = b64url_encode(signature)

    jwt_token = f"{header_b64}.{payload_b64}.{sig_b64}"

    # 5. Tự kiểm chứng chữ ký (Self-Verification) bằng Public Key nếu có
    if os.path.exists(public_key_path):
        with open(public_key_path, "rb") as f:
            public_key = serialization.load_pem_public_key(f.read())
        try:
            public_key.verify(signature, signing_input)
            verify_status = "ĐÃ KIỂM CHỨNG HỢP LỆ (VERIFIED OK)"
        except Exception as e:
            raise RuntimeError(f"Lỗi kiểm chứng chữ ký nội bộ: {e}")
    else:
        verify_status = "BỎ QUA (Không tìm thấy public key PEM để đối soát)"

    # 6. Xuất file .lic và QR Code
    if not output_prefix:
        output_prefix = f"license_{norm_df.replace('-', '')}"

    lic_file = f"{output_prefix}.lic"
    with open(lic_file, "w", encoding="utf-8") as f:
        f.write(jwt_token)

    qr_file = f"{output_prefix}_qr.png"
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=3,
    )
    qr.add_data(jwt_token)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(qr_file)

    # In kết quả
    print("=" * 70)
    print(" KHỞI TẠO LICENSE BẢN QUYỀN THÀNH CÔNG (TÂN HƯNG HÀ OLM)")
    print("=" * 70)
    print(f"[+] Thiết bị (DF)       : {norm_df}")
    print(f"[+] Gói bản quyền       : {license_type.upper()}")
    print(f"[+] Ngày phát hành      : {now_dt.strftime('%d/%m/%Y %H:%M:%S UTC')}")
    print(f"[+] Hạn sử dụng         : {exp_dt.strftime('%d/%m/%Y %H:%M:%S UTC')} ({days_valid} ngày)")
    print(f"[+] Tính năng mở khóa   : {', '.join(features)}")
    print(f"[+] Trạng thái chữ ký   : {verify_status}")
    print(f"[+] File License        : {lic_file}")
    print(f"[+] File QR Code        : {qr_file}")
    print("-" * 70)
    print("TOKEN LICENSE (JWT):")
    print(jwt_token)
    print("=" * 70)

    return jwt_token, lic_file, qr_file

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sinh License OLM chuẩn JWT Ed25519 cho PDA")
    parser.add_argument("--df", required=True, help="Mã Device Fingerprint 16 ký tự (VD: 9A2B-X7Y8-AT6Y-4F2E)")
    parser.add_argument("--type", default="PRO", choices=["TRIAL", "PRO", "ENTERPRISE"], help="Gói license")
    parser.add_argument("--days", type=int, default=365, help="Số ngày sử dụng kể từ hôm nay (mặc định: 365)")
    parser.add_argument("--exp", default=None, help="Ngày hết hạn cụ thể dạng YYYY-MM-DD")
    parser.add_argument("--customer", default="Khách hàng Tân Hưng Hà", help="Tên khách hàng")
    parser.add_argument("--model", default="NLS-MT90", help="Tên model máy")
    parser.add_argument("--key", default="ed25519_private_key.pem", help="Đường dẫn file Private Key PEM")
    parser.add_argument("--pub", default="ed25519_public_key.pem", help="Đường dẫn file Public Key PEM")
    parser.add_argument("--out", default=None, help="Tên tiền tố file xuất ra")

    args = parser.parse_args()

    try:
        create_license(
            df=args.df,
            license_type=args.type,
            days_valid=args.days,
            expiry_date_str=args.exp,
            customer=args.customer,
            model=args.model,
            private_key_path=args.key,
            public_key_path=args.pub,
            output_prefix=args.out
        )
    except Exception as err:
        print(f"[-] LỖI: {err}", file=sys.stderr)
        sys.exit(1)
