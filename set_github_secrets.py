#!/usr/bin/env python3
"""
Set GitHub Secrets using GitHub API
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
    return response.status_code == 201 or response.status_code == 204

def main():
    # Get GitHub token from environment
    token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    if not token:
        print("❌ GH_TOKEN or GITHUB_TOKEN environment variable not set")
        sys.exit(1)
    
    # Repository info
    owner = "msli2233bin"
    repo = "broadfsc-automation"
    
    # Read .env file
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
                # Only include required secrets
                if key in ['GROQ_API_KEY', 'SUBSTACK_EMAIL', 'SUBSTACK_PASSWORD', 
                           'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHANNEL_ID']:
                    secrets[key] = value
    
    print(f"📋 Found {len(secrets)} secrets to set:")
    for name in secrets.keys():
        print(f"  - {name}")
    
    print(f"\n🚀 Setting secrets for {owner}/{repo}...\n")
    
    # Set each secret
    success_count = 0
    for name, value in secrets.items():
        try:
            if set_secret(owner, repo, token, name, value):
                print(f"✅ {name} set successfully")
                success_count += 1
            else:
                print(f"⚠️  {name} may have been set (status: {response.status_code})")
        except Exception as e:
            print(f"❌ Failed to set {name}: {e}")
    
    print(f"\n📊 Summary: {success_count}/{len(secrets)} secrets set successfully")
    
    if success_count == len(secrets):
        print("🎉 All secrets configured! GitHub Actions should work now.")
    else:
        print("⚠️  Some secrets failed to set. Check errors above.")

if __name__ == "__main__":
    main()
