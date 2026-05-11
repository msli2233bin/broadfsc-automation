#!/usr/bin/env python3
"""
Fixed version: Set GitHub Secrets using correct encryption
"""
import os
import sys
import json
import base64
import requests
from pathlib import Path

def get_public_key(owner, repo, token):
    """Get repository public key for encrypting secrets"""
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/public-key"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to get public key: {response.status_code}")
        print(f"   Response: {response.text}")
        sys.exit(1)
    return response.json()

def encrypt_secret(public_key_b64, secret_value):
    """Encrypt a secret using GitHub's required format"""
    try:
        import nacl.public
        import nacl.encoding
        
        # Decode the public key from base64
        public_key_bytes = base64.b64decode(public_key_b64)
        
        # Create PublicKey object
        public_key = nacl.public.PublicKey(public_key_bytes)
        
        # Create a Box with a random private key and the public key
        # GitHub's API expects: sealed box (just recipient's public key)
        sealed_box = nacl.public.SealedBox(public_key)
        
        # Encrypt the secret
        encrypted = sealed_box.encrypt(secret_value.encode('utf-8'))
        
        # Return base64 encoded encrypted value
        return base64.b64encode(encrypted).decode('utf-8')
    except ImportError:
        print("❌ Need PyNaCl library. Install with: pip install pynacl")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Encryption error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def set_secret(owner, repo, token, secret_name, secret_value, public_key_data):
    """Set a GitHub secret"""
    try:
        # Encrypt secret
        encrypted_value = encrypt_secret(public_key_data['key'], secret_value)
        
        # Set secret
        url = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/{secret_name}"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        data = {
            "encrypted_value": encrypted_value,
            "key_id": public_key_data['key_id']
        }
        
        print(f"   📤 Sending PUT request to {secret_name}...")
        response = requests.put(url, headers=headers, json=data)
        
        if response.status_code in [201, 204]:
            return True
        else:
            print(f"   ❌ Failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False

def main():
    print("🚀 Starting GitHub Secrets configuration...\n")
    
    # Step 1: Get GitHub token
    print("📋 Step 1: Getting GitHub token...")
    token = os.environ.get('GH_TOKEN')
    
    if not token:
        print("❌ GH_TOKEN environment variable not set")
        print("   Trying to extract from git credential...")
        import subprocess
        result = subprocess.run(
            ['git', 'credential', 'fill'],
            input='protocol=https\nhost=github.com\n\n',
            capture_output=True,
            text=True,
            timeout=10
        )
        for line in result.stdout.split('\n'):
            if line.startswith('password='):
                token = line.split('=', 1)[1].strip()
                break
    
    if not token:
        print("❌ Failed to get GitHub token")
        sys.exit(1)
    
    print(f"✅ Token found: {token[:10]}...{token[-4:]}")
    print(f"   Length: {len(token)} characters\n")
    
    # Step 2: Test token validity
    print("📋 Step 2: Testing token validity...")
    test_url = "https://api.github.com/user"
    test_response = requests.get(test_url, headers={"Authorization": f"token {token}"})
    
    if test_response.status_code != 200:
        print(f"❌ Token test failed: {test_response.status_code}")
        print(f"   Response: {test_response.text}")
        sys.exit(1)
    
    user_data = test_response.json()
    print(f"✅ Token valid! Authenticated as: {user_data.get('login')}")
    print(f"   Scopes: {test_response.headers.get('X-OAuth-Scopes', 'N/A')}\n")
    
    # Step 3: Read .env file
    print("📋 Step 3: Reading .env file...")
    env_file = Path(__file__).parent / '.env'
    if not env_file.exists():
        print(f"❌ .env file not found at {env_file}")
        sys.exit(1)
    
    # Parse .env file
    secrets = {}
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, _, value = line.partition('=')
                if key in ['GROQ_API_KEY', 'SUBSTACK_EMAIL', 'SUBSTACK_PASSWORD', 
                           'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHANNEL_ID']:
                    secrets[key] = value
    
    print(f"✅ Found {len(secrets)} secrets to set:")
    for name in secrets.keys():
        print(f"   - {name}")
    print()
    
    # Step 4: Get public key (once for all secrets)
    print("📋 Step 4: Getting repository public key...")
    try:
        pk_data = get_public_key("msli2233bin", "broadfsc-automation", token)
        print(f"✅ Public key ID: {pk_data['key_id']}")
        print(f"   Key (first 20 chars): {pk_data['key'][:20]}...\n")
    except Exception as e:
        print(f"❌ Failed to get public key: {e}")
        sys.exit(1)
    
    # Step 5: Set each secret
    print(f"📋 Step 5: Setting secrets for msli2233bin/broadfsc-automation...\n")
    
    success_count = 0
    for name, value in secrets.items():
        print(f"🔧 Setting {name}...")
        try:
            if set_secret("msli2233bin", "broadfsc-automation", token, name, value, pk_data):
                print(f"✅ {name} set successfully\n")
                success_count += 1
            else:
                print(f"❌ {name} failed\n")
        except Exception as e:
            print(f"❌ {name} exception: {e}\n")
    
    print(f"📊 Summary: {success_count}/{len(secrets)} secrets set successfully")
    
    if success_count == len(secrets):
        print("🎉 All secrets configured! GitHub Actions should work now.")
        print("\n💡 Next step: Trigger the workflow manually:")
        print("   https://github.com/msli2233bin/broadfsc-automation/actions/workflows/daily_substack.yml")
    else:
        print("⚠️  Some secrets failed to set. Check errors above.")

if __name__ == "__main__":
    main()
