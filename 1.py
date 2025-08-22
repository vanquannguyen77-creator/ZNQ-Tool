#!/usr/bin/env python3
import os, sys, io, zipfile, urllib.request
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import scrypt

# ===== CONFIG =====
USE_LOCAL = False
PAYLOAD_URL = "https://github.com/vanquannguyen77-creator/ZNQ-Tool/releases/download/latest/payload.enc"
LOCAL_PATH = "/sdcard/Download/payload.enc"
SCRYPT_N, SCRYPT_R, SCRYPT_P = 16384, 8, 1
ENTRY_FALLBACK = "znq-rejoin.py"
# ==================

MAGIC = b'ENC1'

def fetch_bytes():
    if USE_LOCAL:
        with open(LOCAL_PATH, "rb") as f:
            return f.read()
    with urllib.request.urlopen(PAYLOAD_URL, timeout=30) as r:
        return r.read()

def kdf(passphrase: str, salt: bytes) -> bytes:
    return scrypt(passphrase.encode("utf-8"), salt, key_len=32, N=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P)

def decrypt(blob: bytes, key: bytes) -> bytes:
    assert blob[:4] == MAGIC, "Bad payload (MAGIC mismatch)"
    salt = blob[4:20]
    nonce = blob[20:32]
    ct_tag = blob[32:]
    ct, tag = ct_tag[:-16], ct_tag[-16:]
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    return cipher.decrypt_and_verify(ct, tag)

def run_zip(zip_bytes: bytes):
    zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    name = ENTRY_FALLBACK
    for n in zf.namelist():
        if n.endswith(".py"):
            name = n
            break
    src = zf.read(name).decode("utf-8", errors="replace")
    code = compile(src, name, "exec")
    g = {"__name__": "__main__"}
    exec(code, g, g)

def main():
    print("== Bootstrap ==")
    key = input("Nhập KEY của bạn: ").strip()
    if not key:
        print("KEY rỗng."); sys.exit(2)
    blob = fetch_bytes()
    salt = blob[4:20]
    dkey = kdf(key, salt)
    payload = decrypt(blob, dkey)
    run_zip(payload)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Lỗi:", e)
        sys.exit(1)
