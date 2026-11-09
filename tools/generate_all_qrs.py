import os
import sys
import json
import time
import base64
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
import qrcode

BASE_DIR = os.getcwd()
TOOLS_DIR = os.path.join(BASE_DIR, 'tools', 'license_tool')
PRIV_KEY_PATH = os.path.join(TOOLS_DIR, 'ed25519_private_key.pem')

with open(PRIV_KEY_PATH, 'rb') as f:
    priv_key = serialization.load_pem_private_key(f.read(), password=None)

fake_key = ed25519.Ed25519PrivateKey.generate()

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

now = int(time.time())

devices = {
    'newland_mt90': {
        'name': 'Newland NLS-MT90',
        'model': 'NLS-MT90',
        'df': '8ZRB-JNNA-TXYP-K7V9',
        'mismatch_df': 'SRQ6-EWGX-DHEH-6ZKD'
    },
    'zebra_mc3300x': {
        'name': 'Zebra MC3300x',
        'model': 'MC3300x',
        'df': 'SRQ6-EWGX-DHEH-6ZKD',
        'mismatch_df': '8ZRB-JNNA-TXYP-K7V9'
    },
    'samsung_a05': {
        'name': 'Samsung Galaxy A05',
        'model': 'SM-A055F',
        'df': '8H64-68F2-85K9-22M0',
        'mismatch_df': '8ZRB-JNNA-TXYP-K7V9'
    },
    'imin_swift2': {
        'name': 'iMin Swift2',
        'model': 'I23M01',
        'df': 'MGA7-J9R4-C14G-8VY4',
        'mismatch_df': '8H64-68F2-85K9-22M0'
    }
}

brain_dir = r"C:\Users\DELL\.gemini\antigravity\brain\4e16a57e-ebae-473a-8104-40e07157e275"

for dev_key, dev in devices.items():
    df = dev['df']
    model = dev['model']
    dev_name = dev['name']
    mismatch_df = dev['mismatch_df']

    # Case 0: Valid PRO
    p0 = {
        'iss': 'TanHungHa-OLM', 'sub': 'PDA-License', 'df': df, 'type': 'PRO',
        'iat': now, 'exp': now + 365 * 86400,
        'features': ['SCANNER', 'INVENTORY', 'DIRECT_PRINT'],
        'meta': {'customer': f'{dev_name} Official', 'model': model}
    }
    t0 = sign_payload(p0, priv_key)

    # Case 1: Tampered
    p1 = dict(p0)
    p1['type'] = 'ENTERPRISE'
    p1['exp'] = now + 3650 * 86400
    p1_b64 = b64url_encode(json.dumps(p1, separators=(',', ':')).encode('utf-8'))
    t1 = f"{header_b64}.{p1_b64}.{t0.split('.')[2]}"

    # Case 2: Mismatch
    p2 = dict(p0)
    p2['df'] = mismatch_df
    p2['meta'] = {'customer': 'Mismatched Other Device', 'model': 'OTHER'}
    t2 = sign_payload(p2, priv_key)

    # Case 3: Fake Sig
    t3 = sign_payload(p0, fake_key)

    # Case 4: Expired
    p4 = dict(p0)
    p4['iat'] = now - 365 * 86400
    p4['exp'] = now - 30 * 86400
    p4['meta'] = {'customer': f'{dev_name} Expired Demo', 'model': model}
    t4 = sign_payload(p4, priv_key)

    cases = [
        ('CASE_0_VALID', t0),
        ('CASE_1_TAMPERED', t1),
        ('CASE_2_MISMATCH', t2),
        ('CASE_3_FAKESIG', t3),
        ('CASE_4_EXPIRED', t4)
    ]
    for cname, token in cases:
        fname = f"{dev_key}_{cname}"
        with open(f"{fname}.lic", 'w', encoding='utf-8') as f:
            f.write(token)
        qr = qrcode.QRCode(box_size=6, border=2)
        qr.add_data(token)
        qr.make(fit=True)
        img = qr.make_image(fill_color='black', back_color='white')
        img.save(f"{fname}_qr.png")
        img.save(os.path.join(brain_dir, f"{fname}_qr.png"))
        with open(os.path.join(brain_dir, f"{fname}.lic"), 'w', encoding='utf-8') as f:
            f.write(token)

print("Generated all 20 QR codes for 4 devices successfully.")

