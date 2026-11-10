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

# Target: 7:00:00 AM on 10/11/2026 (GMT+7)
exp_dt = datetime(2026, 11, 10, 7, 0, 0, tzinfo=tz_vn)
exp_sec = int(exp_dt.timestamp())

device_targets = [
    {
        "key": "newland_mt90",
        "name": "Newland NLS-MT90 (Đang cắm cáp USB)",
        "model": "NLS-MT90",
        "df": "8ZRB-JNNA-TXYP-K7V9"
    },
    {
        "key": "samsung_a05",
        "name": "Samsung Galaxy A05 (Dân dụng)",
        "model": "SM-A055F",
        "df": "8H64-68F2-85K9-22M0"
    },
    {
        "key": "zebra_mc3300x",
        "name": "Zebra MC3300x",
        "model": "MC3300x",
        "df": "SRQ6-EWGX-DHEH-6ZKD"
    }
]

for dev in device_targets:
    p = {
        "iss": "TanHungHa-OLM",
        "sub": "PDA-License",
        "df": dev["df"],
        "type": "PRO",
        "iat": now_sec,
        "exp": exp_sec,
        "features": ["SCANNER", "INVENTORY", "DIRECT_PRINT"],
        "meta": {
            "customer": f"Tan Hung Ha - Test Expiry 7AM Tomorrow ({dev['name']})",
            "model": dev["model"],
            "issued_at_vn": now_dt.strftime("%d/%m/%Y %H:%M:%S (GMT+7)"),
            "expires_at_vn": exp_dt.strftime("%d/%m/%Y %H:%M:%S (GMT+7)")
        }
    }
    t = sign_payload(p, priv_key)
    base_name = f"{dev['key']}_expires_7am_tomorrow"
    
    with open(f"{base_name}.lic", "w", encoding="utf-8") as f:
        f.write(t)
    with open(os.path.join(BRAIN_DIR, f"{base_name}.lic"), "w", encoding="utf-8") as f:
        f.write(t)
        
    qr = qrcode.QRCode(box_size=7, border=2)
    qr.add_data(t)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(f"{base_name}_qr.png")
    img.save(os.path.join(BRAIN_DIR, f"{base_name}_qr.png"))

print("All expiry test licenses generated successfully!")

