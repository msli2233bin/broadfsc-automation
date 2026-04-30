#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BroadFSC - Threads Token Getter v3 (Simplified OAuth)
======================================================
最简化的 OAuth 流程获取 Threads 长期 Token。

Step 1 (自动): 生成授权链接，用户在浏览器打开并授权
Step 2 (自动): 用户复制 code，脚本自动完成:
  - code → 短期 Token
  - 短期 Token → 长期 Token (60天)
  - 验证 Token
  - 保存到 .env + threads_token.txt
  - 更新 GitHub Secrets (如有权限)

Usage:
  python get_threads_token_v3.py              # 交互模式
  python get_threads_token_v3.py <code>       # 直接传入 code
"""

import sys
import os
import time
import json
import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ============================================================
# Config
# ============================================================
APP_ID = "1479983126925807"
APP_SECRET = "9857adbca8c910959a78e14d813c0e53"
REDIRECT_URI = "https://www.broadfsc.com/"
SCOPES = "threads_basic,threads_content_publish"
API_BASE = "https://graph.threads.net/v1.0"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(SCRIPT_DIR, ".env")
TOKEN_FILE = os.path.join(SCRIPT_DIR, "threads_token.txt")


def step1_generate_auth_url():
    """Step 1: 生成 OAuth 授权链接"""
    auth_url = (
        f"https://www.threads.net/oauth/authorize"
        f"?client_id={APP_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope={SCOPES}"
        f"&response_type=code"
    )
    return auth_url


def step2_exchange_code(code):
    """Step 2: 用 authorization code 换取短期 Token"""
    print("\n[2/5] Exchanging authorization code for short-lived token...")
    url = f"{API_BASE}/access_token"
    params = {
        "client_id": APP_ID,
        "client_secret": APP_SECRET,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "code": code,
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        print(f"  HTTP {r.status_code}")
        if r.status_code != 200:
            print(f"  ❌ Error: {r.text}")
            return None, None
        data = r.json()
        short_token = data.get("access_token")
        user_id = data.get("user_id")
        print(f"  ✅ Short-lived token obtained")
        print(f"  User ID: {user_id}")
        return short_token, user_id
    except Exception as e:
        print(f"  ❌ Request error: {e}")
        return None, None


def step3_get_long_lived_token(short_token):
    """Step 3: 短期 Token → 长期 Token (60天)"""
    print("\n[3/5] Exchanging for long-lived token (60 days)...")
    url = f"{API_BASE}/access_token"
    params = {
        "grant_type": "th_exchange_token",
        "client_secret": APP_SECRET,
        "access_token": short_token,
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        print(f"  HTTP {r.status_code}")
        if r.status_code != 200:
            print(f"  ❌ Error: {r.text}")
            return None, None
        data = r.json()
        long_token = data.get("access_token")
        expires_in = data.get("expires_in", 0)
        days = int(expires_in) // 86400 if expires_in else "unknown"
        print(f"  ✅ Long-lived token obtained!")
        print(f"  Expires in: {expires_in}s (~{days} days)")
        return long_token, expires_in
    except Exception as e:
        print(f"  ❌ Request error: {e}")
        return None, None


def step4_verify_token(token):
    """Step 4: 验证 Token 有效性"""
    print("\n[4/5] Verifying token...")
    url = f"{API_BASE}/me"
    params = {"access_token": token}
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            uid = data.get("id", "unknown")
            username = data.get("username", "unknown")
            threads_profile = data.get("threads_profile_picture_url", "")
            print(f"  ✅ Token is VALID!")
            print(f"  Username: @{username}")
            print(f"  User ID: {uid}")
            return True, uid, username
        else:
            print(f"  ❌ Token invalid: {r.text}")
            return False, None, None
    except Exception as e:
        print(f"  ❌ Verification error: {e}")
        return False, None, None


def step5_save_token(token, user_id, username, expires_in):
    """Step 5: 保存 Token 到文件"""
    print("\n[5/5] Saving token...")

    # Save to threads_token.txt
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        f.write(f"# BroadFSC Threads Long-Lived Token\n")
        f.write(f"# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Expires in: {expires_in}s (~{int(expires_in)//86400} days)\n")
        f.write(f"THREADS_ACCESS_TOKEN={token}\n")
        f.write(f"THREADS_USER_ID={user_id}\n")
        f.write(f"USERNAME={username}\n")
        f.write(f"THREADS_APP_SECRET={APP_SECRET}\n")
    print(f"  ✅ Saved to {TOKEN_FILE}")

    # Update .env
    env_lines = []
    try:
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            env_lines = f.readlines()
    except FileNotFoundError:
        pass

    token_updated = False
    uid_updated = False
    secret_updated = False
    new_lines = []

    for line in env_lines:
        if line.startswith("THREADS_ACCESS_TOKEN="):
            new_lines.append(f"THREADS_ACCESS_TOKEN={token}\n")
            token_updated = True
        elif line.startswith("THREADS_USER_ID="):
            new_lines.append(f"THREADS_USER_ID={user_id}\n")
            uid_updated = True
        elif line.startswith("THREADS_APP_SECRET="):
            new_lines.append(f"THREADS_APP_SECRET={APP_SECRET}\n")
            secret_updated = True
        elif line.startswith("# THREADS_ACCESS_TOKEN will be set"):
            # Remove placeholder comment
            continue
        else:
            new_lines.append(line)

    if not token_updated:
        new_lines.append(f"THREADS_ACCESS_TOKEN={token}\n")
    if not uid_updated:
        new_lines.append(f"THREADS_USER_ID={user_id}\n")
    if not secret_updated:
        new_lines.append(f"THREADS_APP_SECRET={APP_SECRET}\n")

    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print(f"  ✅ Updated {ENV_FILE}")

    # Try to update GitHub Secrets
    try:
        import subprocess
        result = subprocess.run(
            ["gh", "secret", "set", "THREADS_ACCESS_TOKEN", "--body", token],
            capture_output=True, text=True, timeout=30, cwd=SCRIPT_DIR
        )
        if result.returncode == 0:
            print(f"  ✅ GitHub Secret THREADS_ACCESS_TOKEN updated!")
        else:
            print(f"  ⚠️ GitHub Secret update failed: {result.stderr.strip()}")
    except Exception as e:
        print(f"  ⚠️ GitHub Secret update skipped: {e}")

    return True


def main():
    print("=" * 60)
    print("BroadFSC - Threads Token Getter v3 (Simplified OAuth)")
    print("=" * 60)

    # Step 1: Generate auth URL
    auth_url = step1_generate_auth_url()

    print("\n[1/5] Open this URL in your browser (logged in as @msli637):")
    print(f"\n{'─'*60}")
    print(auth_url)
    print(f"{'─'*60}")

    print("""
📋 INSTRUCTIONS:
  1. Click the URL above (or copy to browser)
  2. Log in to Threads if needed
  3. Click "Authorize" / "授权"
  4. You'll be redirected to broadfsc.com/?code=XXXXXXXXX
  5. Copy the FULL URL from the browser address bar
  6. Paste it below (or just the code= value)
""")

    # Get code from user
    if len(sys.argv) > 1:
        user_input = sys.argv[1]
    else:
        try:
            user_input = input("Paste the redirect URL or code here: ").strip()
        except EOFError:
            print("No input received.")
            return

    if not user_input:
        print("❌ No input provided.")
        return

    # Extract code from URL or raw value
    code = user_input
    if "code=" in user_input:
        # Parse from URL
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(user_input)
        params = parse_qs(parsed.query)
        if "code" in params:
            code = params["code"][0]
        else:
            # Try fragment
            params = parse_qs(parsed.fragment)
            if "code" in params:
                code = params["code"][0]

    print(f"\n  Authorization code: {code[:20]}...{code[-10:]}")

    # Step 2: Exchange code for short-lived token
    short_token, user_id = step2_exchange_code(code)
    if not short_token:
        return

    # Step 3: Exchange for long-lived token
    long_token, expires_in = step3_get_long_lived_token(short_token)
    if not long_token:
        # Fallback: try saving short-lived token anyway
        print("\n⚠️ Long-lived token exchange failed. Trying to save short-lived token...")
        long_token = short_token
        expires_in = 3600  # ~1 hour

    # Step 4: Verify token
    valid, uid, username = step4_verify_token(long_token)
    if not valid:
        print("\n❌ Token verification failed. Something went wrong.")
        return

    if not user_id:
        user_id = uid

    # Step 5: Save token
    step5_save_token(long_token, user_id, username, expires_in)

    # Final summary
    print(f"\n{'='*60}")
    print(f"🎉 SUCCESS! Threads Token configured!")
    print(f"{'='*60}")
    print(f"  Username: @{username}")
    print(f"  User ID: {user_id}")
    print(f"  Token: {long_token[:30]}...{long_token[-10:]}")
    print(f"  Expires: ~{int(expires_in)//86400} days")
    print(f"\n  📝 Token auto-refresh has been built into threads_poster.py")
    print(f"  Run 'python threads_poster.py refresh-token' to refresh manually")


if __name__ == "__main__":
    main()
