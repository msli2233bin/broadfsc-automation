"""Update POSTPROXY_API_KEY in GitHub Secrets via git credential manager"""
import requests, json, base64, os, sys, subprocess
sys.stdout.reconfigure(encoding='utf-8')

git_exe = r"C:\Program Files\Git\bin\git.exe"

# Get token from git credential manager
proc = subprocess.run(
    [git_exe, "credential", "fill"],
    input="protocol=https\nhost=github.com\n\n",
    capture_output=True, text=True, encoding='utf-8'
)

token = None
for line in proc.stdout.strip().split('\n'):
    if line.startswith('password='):
        token = line.split('=', 1)[1]
        break

if not token:
    print(f'ERROR: cannot get GitHub token. stderr: {proc.stderr}')
    sys.exit(1)

print(f'Got token: {token[:8]}...')

repo = 'msli2233bin/broadfsc-automation'

# Secrets to update
secrets = {
    'POSTPROXY_API_KEY': 'f96101c20ff72e2bca9f2bd699f2dca64ca0231d0a8822b5',
}

headers = {
    'Authorization': f'token {token}',
    'Accept': 'application/vnd.github.v3+json'
}

# Get public key
r = requests.get(f'https://api.github.com/repos/{repo}/actions/secrets/public-key', headers=headers)
data = r.json()
pub_key = data['key']
key_id = data['key_id']

# Encrypt and update each secret
from nacl import public
public_key = public.PublicKey(base64.b64decode(pub_key))
sealed_box = public.SealedBox(public_key)

for secret_name, secret_value in secrets.items():
    encrypted = base64.b64encode(sealed_box.encrypt(secret_value.encode())).decode()
    payload = {'encrypted_value': encrypted, 'key_id': key_id}
    r = requests.put(f'https://api.github.com/repos/{repo}/actions/secrets/{secret_name}', headers=headers, json=payload)
    print(f'{secret_name} update: {r.status_code}')
