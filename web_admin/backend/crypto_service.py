import os
import io
import json
import base64
from datetime import datetime, timezone, timedelta
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
import qrcode

CROCKFORD_ALPHABET = set("0123456789ABCDEFGHJKMNPQRSTVWXYZ")

# Xác định đường dẫn tuyệt đối đến file Private & Public Key trong tools/license_tool
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
DEFAULT_PRIV_KEY_PATH = os.path.join(PROJECT_ROOT, "tools", "license_tool", "ed25519_private_key.pem")
DEFAULT_PUB_KEY_PATH = os.path.join(PROJECT_ROOT, "tools", "license_tool", "ed25519_public_key.pem")

def b64url_encode(data: bytes) -> str:
    """Mã hóa Base64URL không kèm padding '=' theo chuẩn JWT RFC 7515 / RFC 8037."""
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')

def b64url_decode(str_data: str) -> bytes:
    """Giải mã Base64URL với tự động bù padding '='."""
    rem = len(str_data) % 4
    if rem > 0:
        str_data += '=' * (4 - rem)
    return base64.urlsafe_b64decode(str_data)

def normalize_df(df_input: str) -> str:
    """
    Chuẩn hóa và kiểm tra mã DF:
    - Bỏ khoảng trắng và dấu gạch nối.
    - Chuyển sang chữ hoa.
    - Kiểm tra đúng 16 ký tự thuộc bảng mã Crockford Base32 (0-9, A-Z ngoại trừ I, L, O, U).
    - Trả về định dạng XXXX-XXXX-XXXX-XXXX.
    """
    if not df_input:
        raise ValueError("Mã Device Fingerprint (DF) không được để trống!")

    cleaned = df_input.strip().upper().replace("-", "").replace(" ", "")
    if len(cleaned) != 16:
        raise ValueError(f"Mã DF phải gồm đúng 16 ký tự Crockford. Độ dài nhận được: {len(cleaned)} ('{cleaned}')")
    
    for char in cleaned:
        if char not in CROCKFORD_ALPHABET:
            raise ValueError(f"Ký tự không hợp lệ trong mã DF: '{char}'. Bảng Crockford chỉ chấp nhận 0-9 và A-Z (trừ I, L, O, U).")
            
    return f"{cleaned[0:4]}-{cleaned[4:8]}-{cleaned[8:12]}-{cleaned[12:16]}"

def load_private_key(key_path: str = DEFAULT_PRIV_KEY_PATH):
    if not os.path.exists(key_path):
        raise FileNotFoundError(f"Không tìm thấy file Private Key tại: {key_path}")
    with open(key_path, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)

def load_public_key(pub_key_path: str = DEFAULT_PUB_KEY_PATH):
    if not os.path.exists(pub_key_path):
        return None
    with open(pub_key_path, "rb") as f:
        return serialization.load_pem_public_key(f.read())

def generate_license_jwt(
    df: str,
    license_type: str = "PRO",
    days_valid: int = 365,
    is_permanent: bool = False,
    customer: str = "Khách hàng Tân Hưng Hà",
    model: str = "Newland NLS-MT90",
    features: list = None,
    version: int = 1,
    priv_key_path: str = DEFAULT_PRIV_KEY_PATH,
    pub_key_path: str = DEFAULT_PUB_KEY_PATH
) -> dict:
    """
    Sinh chuỗi JWT Ed25519 (RFC 8037) và ảnh QR Code cho thiết bị PDA.
    Trả về dict: {
        'jwt_token': str,
        'norm_df': str,
        'issued_at': datetime,
        'expires_at': datetime or None,
        'qr_base64': str,
        'qr_bytes': bytes,
        'verified': bool
    }
    """
    if features is None:
        features = ["SCANNER", "INVENTORY", "DIRECT_PRINT"]

    norm_df = normalize_df(df)
    private_key = load_private_key(priv_key_path)

    now_dt = datetime.now(timezone.utc)
    iat_ts = int(now_dt.timestamp())

    if is_permanent or license_type.upper() == "PERPETUAL":
        exp_dt = None
        # Vĩnh viễn: Đặt exp năm 2099 (~4.1 tỷ timestamp) hoặc 10 năm theo logic client
        exp_ts = int((now_dt + timedelta(days=36500)).timestamp())
        is_permanent = True
    else:
        exp_dt = now_dt + timedelta(days=days_valid)
        exp_ts = int(exp_dt.timestamp())

    header = {
        "alg": "EdDSA",
        "typ": "JWT"
    }

    payload = {
        "iss": "TanHungHa-OLM",
        "sub": "PDA-License",
        "df": norm_df,
        "type": "PRO" if is_permanent else license_type.upper(),
        "iat": iat_ts,
        "exp": exp_ts,
        "features": features,
        "meta": {
            "customer": customer,
            "model": model,
            "issued_at_utc": now_dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "expires_at_utc": "VĨNH VIỄN (PERPETUAL)" if is_permanent else exp_dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "license_version": version
        }
    }

    header_json = json.dumps(header, separators=(',', ':')).encode('utf-8')
    payload_json = json.dumps(payload, separators=(',', ':')).encode('utf-8')

    header_b64 = b64url_encode(header_json)
    payload_b64 = b64url_encode(payload_json)
    signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')

    signature = private_key.sign(signing_input)
    sig_b64 = b64url_encode(signature)

    jwt_token = f"{header_b64}.{payload_b64}.{sig_b64}"

    # Tự đối soát chữ ký với Public Key
    verified = False
    pub_key = load_public_key(pub_key_path)
    if pub_key:
        try:
            pub_key.verify(signature, signing_input)
            verified = True
        except Exception:
            verified = False

    # Sinh ảnh QR Code
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=3,
    )
    qr.add_data(jwt_token)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_bytes = buffer.getvalue()
    qr_base64 = "data:image/png;base64," + base64.b64encode(qr_bytes).decode('utf-8')

    return {
        "jwt_token": jwt_token,
        "norm_df": norm_df,
        "issued_at": now_dt,
        "expires_at": exp_dt,
        "is_permanent": is_permanent,
        "qr_base64": qr_base64,
        "qr_bytes": qr_bytes,
        "verified": verified,
        "version": version
    }

