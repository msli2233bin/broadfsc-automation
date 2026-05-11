#!/usr/bin/env python3
"""
Extract GitHub token from Git Credential Manager and set GitHub Secrets
"""
import os
import sys
import subprocess
import json
import base64
import requests
from pathlib import Path

def extract_github_token():
    """Extract GitHub token from Git Credential Manager"""
    try:
        # Use PowerShell to get credential
        ps_script = """
        cd C:\Users\Administrator\WorkBuddy\20260414140743\broadfsc-automation
        $input = @"
protocol=https
host=github.com

"@
        $input | git credential fill
        """
        
        result = subprocess.run(
            ['powershell', '-Command', ps_script],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Parse output to find password/token
        for line in result.stdout.split('\n'):
            if line.startswith('password='):
                token = line.split('=', 1)[1].strip()
                if token:
                    return token
        
        return None
    except Exception as e:
        print(f"❌ Failed to extract token: {e}")
        return None

def get_public_key(owner, repo, token):
    """Get repository public key for encrypting secrets"""
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/public-key"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def encrypt_secret(public_key, secret_value):
    """Encrypt a secret using the repository's public key"""
    try:
        import nacl.public
        import nacl.encoding
        
        # Decode the public key
        public_key_bytes = base64.b64decode(public_key)
        
        # Create Box with public key
        box = nacl.public.Box(
            nacl.public.PrivateKey.generate(),
            nacl.public.PublicKey(public_key_bytes)
        )
        
        # Encrypt the secret
        encrypted = box.encrypt(secret_value.encode('utf-8'))
        
        # Return base64 encoded encrypted value
        return base64.b64encode(encrypted).decode('utf-8')
    except ImportError:
        print("❌ Need PyNaCl library. Install with: pip install pynacl")
        sys.exit(1)

def set_secret(owner, repo, token, secret_name, secret_value):
    """Set a GitHub secret"""
    try:
        # Get public key
        pk_data = get_public_key(owner, repo, token)
        public_key = pk_data['key']
        key_id = pk_data['key_id']
        
        # Encrypt secret
        encrypted_value = encrypt_secret(public_key, secret_value)
        
        # Set secret
        url = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/{secret_name}"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        data = {
            "encrypted_value": encrypted_value,
            "key_id": key_id
        }
        
        response = requests.put(url, headers=headers, json=data)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"❌ Failed to set {secret_name}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        return False

def main():
    print("🚀 Starting GitHub Secrets configuration...\n")
    
    # Step 1: Extract GitHub token
    print("📋 Step 1: Extracting GitHub token from credential manager...")
    token = extract_github_token()
    
    if not token:
        print("❌ Failed to extract GitHub token")
        print("   Please set GH_TOKEN environment variable manually")
        sys.exit(1)
    
    print(f"✅ Token extracted: {token[:10]}...{token[-4:]}")
    print(f"   Length: {len(token)} characters\n")
    
    # Step 2: Read .env file
    print("📋 Step 2: Reading .env file...")
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
                # Only include required secrets for Substack auto-post
                if key in ['GROQ_API_KEY', 'SUBSTACK_EMAIL', 'SUBSTACK_PASSWORD', 
                           'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHANNEL_ID']:
                    secrets[key] = value
    
    print(f"✅ Found {len(secrets)} secrets to set:")
    for name in secrets.keys():
        print(f"   - {name}")
    print()
    
    # Step 3: Set each secret
    print(f"📋 Step 3: Setting secrets for msli2233bin/broadfsc-automation...\n")
    
    success_count = 0
    for name, value in secrets.items():
        try:
            if set_secret("msli2233bin", "broadfsc-automation", token, name, value):
                print(f"✅ {name} set successfully")
                success_count += 1
            else:
                print(f"⚠️  {name} may have been set (unknown status)")
        except Exception as e:
            print(f"❌ Failed to set {name}: {e}")
    
    print(f"\n📊 Summary: {success_count}/{len(secrets)} secrets set successfully")
    
    if success_count == len(secrets):
        print("🎉 All secrets configured! GitHub Actions should work now.")
        print("\n💡 Next step: Manually trigger the workflow:")
        print("   https://github.com/msli2233bin/broadfsc-automation/actions/workflows/daily_substack.yml")
    else:
        print("⚠️  Some secrets failed to set. Check errors above.")

if __name__ == "__main__":
    main()
