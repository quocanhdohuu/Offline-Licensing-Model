import os
import sys
import json
import time
import base64
import subprocess
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
import qrcode

DEVICE_ID = "R92X41LE48X"
DF_CODE = "8H64-68F2-85K9-22M0"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.join(BASE_DIR, "tools", "license_tool")
PRIV_KEY_PATH = os.path.join(TOOLS_DIR, "ed25519_private_key.pem")

# 1. Load real Private Key
with open(PRIV_KEY_PATH, "rb") as f:
    priv_key = serialization.load_pem_private_key(f.read(), password=None)

def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')

header = {"alg": "EdDSA", "typ": "JWT"}
header_b64 = b64url_encode(json.dumps(header, separators=(',', ':')).encode('utf-8'))

def sign_payload(payload_dict, key):
    payload_b64 = b64url_encode(json.dumps(payload_dict, separators=(',', ':')).encode('utf-8'))
    message = f"{header_b64}.{payload_b64}".encode('utf-8')
    sig = key.sign(message)
    sig_b64 = b64url_encode(sig)
    return f"{header_b64}.{payload_b64}.{sig_b64}"

def save_case(name, token):
    with open(f"samsung_{name}.lic", "w", encoding="utf-8") as f:
        f.write(token)
    img = qrcode.make(token)
    img.save(f"samsung_{name}_qr.png")

now = int(time.time())

# Case 0: Valid PRO License (365 days)
p0 = {
    "iss": "TanHungHa-OLM",
    "sub": "PDA-License",
    "df": DF_CODE,
    "type": "PRO",
    "iat": now,
    "exp": now + 365 * 86400,
    "features": ["SCANNER", "INVENTORY", "DIRECT_PRINT"],
    "meta": {
        "customer": "Samsung Galaxy A05 Verified",
        "model": "SM-A055F",
        "issued_at_utc": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(now)),
        "expires_at_utc": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(now + 365 * 86400))
    }
}
token0 = sign_payload(p0, priv_key)
save_case("CASE_0_VALID", token0)

# Case 1: Tampered Payload (Modify type to ENTERPRISE & 10 years expiration without valid signature)
p1 = dict(p0)
p1["type"] = "ENTERPRISE"
p1["exp"] = now + 3650 * 86400
p1["features"] = ["SCANNER", "INVENTORY", "DIRECT_PRINT", "ADVANCED_ANALYTICS"]
p1_b64 = b64url_encode(json.dumps(p1, separators=(',', ':')).encode('utf-8'))
token1 = f"{header_b64}.{p1_b64}.{token0.split('.')[2]}" # Original signature with modified payload
save_case("CASE_1_TAMPERED", token1)

# Case 2: Device Mismatch (License belonging to Newland MT90)
p2 = dict(p0)
p2["df"] = "8ZRB-JNNA-TXYP-K7V9" # Different physical device
p2["meta"]["customer"] = "Newland MT90 License"
p2["meta"]["model"] = "NLS-MT90"
token2 = sign_payload(p2, priv_key)
save_case("CASE_2_MISMATCH", token2)

# Case 3: Fake Signature (Signed with an unauthorized third-party Ed25519 key)
fake_key = ed25519.Ed25519PrivateKey.generate()
token3 = sign_payload(p0, fake_key)
save_case("CASE_3_FAKESIG", token3)

# Case 4: Expired License (Expired 30 days ago, validly signed)
p4 = dict(p0)
p4["iat"] = now - 365 * 86400
p4["exp"] = now - 30 * 86400
p4["meta"]["issued_at_utc"] = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(p4["iat"]))
p4["meta"]["expires_at_utc"] = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(p4["exp"]))
token4 = sign_payload(p4, priv_key)
save_case("CASE_4_EXPIRED", token4)

print("Generated all 5 test cases for Samsung Galaxy A05.")

