import os
import json
import time
import base64
from datetime import datetime, timezone, timedelta
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
import qrcode

BASE_DIR = os.getcwd()
TOOLS_DIR = os.path.join(BASE_DIR, 'tools', 'license_tool')
PRIV_KEY_PATH = os.path.join(TOOLS_DIR, 'ed25519_private_key.pem')
BRAIN_DIR = r"C:\Users\DELL\.gemini\antigravity\brain\4e16a57e-ebae-473a-8104-40e07157e275"

with open(PRIV_KEY_PATH, 'rb') as f:
    priv_key = serialization.load_pem_private_key(f.read(), password=None)

def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')

header = {'alg': 'EdDSA', 'typ': 'JWT'}
header_b64 = b64url_encode(json.dumps(header, separators=(',', ':')).encode('utf-8'))

def sign_payload(payload_dict, key):
    payload_b64 = b64url_encode(json.dumps(payload_dict, separators=(',', ':')).encode('utf-8'))
    message = f"{header_b64}.{payload_b64}".encode('utf-8')
    sig = key.sign(message)
    sig_b64 = b64url_encode(sig)
    return f"{header_b64}.{payload_b64}.{sig_b64}"

tz_vn = timezone(timedelta(hours=7))
now_dt = datetime.now(tz_vn)
now_sec = int(now_dt.timestamp())

# Target: 7:00:00 AM on 10/11/2026 (UTC+7)
exp_dt = datetime(2026, 11, 10, 7, 0, 0, tzinfo=tz_vn)
exp_sec = int(exp_dt.timestamp())

df_code = "8ZRB-JNNA-TXYP-K7V9"

payload = {
    "iss": "TanHungHa-OLM",
    "sub": "PDA-License",
    "df": df_code,
    "type": "PRO",
    "iat": now_sec,
    "exp": exp_sec,
    "features": ["SCANNER", "INVENTORY", "DIRECT_PRINT"],
    "meta": {
        "customer": "Tan Hung Ha - Test Offline Expiry 7AM Tomorrow",
        "model": "NLS-MT90",
        "issued_at_utc": now_dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "expires_at_utc": exp_dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "expires_at_vn": exp_dt.strftime("%d/%m/%Y %H:%M:%S (GMT+7)")
    }
}

token = sign_payload(payload, priv_key)

# Save files
lic_filename = "mt90_license_expires_tomorrow_7am.lic"
qr_filename = "mt90_license_expires_tomorrow_7am_qr.png"

with open(lic_filename, "w", encoding="utf-8") as f:
    f.write(token)

with open(os.path.join(BRAIN_DIR, lic_filename), "w", encoding="utf-8") as f:
    f.write(token)

qr = qrcode.QRCode(box_size=8, border=2)
qr.add_data(token)
qr.make(fit=True)
img = qr.make_image(fill_color="black", back_color="white")
img.save(qr_filename)
img.save(os.path.join(BRAIN_DIR, qr_filename))

print("=== LICENSE GENERATED SUCCESSFULLY ===")
print("DF Code       :", df_code)
print("Issued (VN)   :", now_dt.strftime("%d/%m/%Y %H:%M:%S (GMT+7)"))
print("Expires (VN)  :", exp_dt.strftime("%d/%m/%Y %H:%M:%S (GMT+7)"))
print("IAT Epoch     :", now_sec)
print("EXP Epoch     :", exp_sec)
print("Remaining Sec :", exp_sec - now_sec)
print("Remaining Hrs :", (exp_sec - now_sec) / 3600)
print("Token Length  :", len(token))
print("QR Saved To   :", qr_filename)
print("Token         :\n", token)

