#!/usr/bin/env python3
"""Update TELEGRAM_BOT_TOKEN GitHub Actions secret.
Usage: python3 update_github_secret.py <github_token>
"""
import sys, json, base64
import urllib.request, urllib.parse, urllib.error
from nacl.public import SealedBox, PublicKey

REPO = "msli2233bin/broadfsc-automation"
SECRET_NAME = "TELEGRAM_BOT_TOKEN"
NEW_VALUE = "8292422033:AAHrPUfSaUAcmpvQXcV4nsd-NakZH3SIwPU"

def get_public_key(token):
    url = f"https://api.github.com/repos/{REPO}/actions/secrets/public-key"
    req = urllib.request.Request(url, headers={
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    })
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def encrypt_secret(public_key_b64, secret_value):
    """Encrypt using libsodium sealed box (pynacl)."""
    pk = PublicKey(base64.b64decode(public_key_b64))
    sealed_box = SealedBox(pk)
    encrypted = sealed_box.encrypt(secret_value.encode())
    return base64.b64encode(encrypted).decode()

def put_secret(token, key_id, encrypted_value):
    url = f"https://api.github.com/repos/{REPO}/actions/secrets/{SECRET_NAME}"
    data = json.dumps({
        "encrypted_value": encrypted_value,
        "key_id": key_id
    }).encode()
    req = urllib.request.Request(url, data=data, method="PUT", headers={
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    })
    with urllib.request.urlopen(req) as r:
        return r.status

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 update_github_secret.py <github_personal_access_token>")
        print(f"\nThis updates the {SECRET_NAME} secret in {REPO}.")
        print("Generate a token at: https://github.com/settings/tokens")
        print("Token needs 'repo' scope.\n")
        print(f"Correct bot token value: {NEW_VALUE}")
        sys.exit(1)

    gh_token = sys.argv[1]
    print(f"Getting public key for {REPO}...")
    try:
        pk_info = get_public_key(gh_token)
        print(f"  key_id: {pk_info['key_id']}")
        print(f"  Encrypting secret...")
        enc = encrypt_secret(pk_info['key'], NEW_VALUE)
        print(f"  Uploading encrypted secret...")
        status = put_secret(gh_token, pk_info['key_id'], enc)
        print(f"✅  Secret updated! HTTP status: {status}")
    except urllib.error.HTTPError as e:
        print(f"❌  HTTP {e.code}: {e.read().decode()}")
        sys.exit(1)
    except Exception as e:
        print(f"❌  {e}")
        sys.exit(1)
