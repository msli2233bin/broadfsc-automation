#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Threads Token 交换脚本 v2 - 尝试不同方式获取长期 Token
"""

import requests
import json

# App 凭证
APP_ID = "1479983126925807"
APP_SECRET = "9857adbca8c910959a78e14d813c0e53"

def main():
    print("=" * 60)
    print("Threads Token 交换工具 v2")
    print("=" * 60)
    
    # 获取用户输入的短期 Token
    short_token = input("\nPaste fresh Access Token here and press Enter: ").strip()
    
    if not short_token:
        print("❌ Error: No token provided")
        return
    
    print(f"\n[1/3] Verifying token...")
    
    # 验证 Token
    verify_url = "https://graph.threads.net/v1.0/me"
    verify_params = {"access_token": short_token}
    
    try:
        r = requests.get(verify_url, params=verify_params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            user_id = data.get("id", "unknown")
            username = data.get("username", "unknown")
            print(f"  Status: 200 OK")
            print(f"  User ID: {user_id}")
            print(f"  Username: {username}")
            print(f"  ✅ Token is VALID!")
        else:
            print(f"  Status: {r.status_code}")
            print(f"  Response: {r.text}")
            print(f"  ❌ Token verification failed")
            return
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return
    
    print(f"\n[2/3] Exchanging for long-lived token (Method 2 - FB Graph API)...")
    
    # 方法2: 使用 FB Graph API 的 oauth/access_token 端点
    exchange_url = "https://graph.facebook.com/v18.0/oauth/access_token"
    exchange_params = {
        "grant_type": "fb_exchange_token",
        "client_id": APP_ID,
        "client_secret": APP_SECRET,
        "fb_exchange_token": short_token
    }
    
    try:
        r = requests.get(exchange_url, params=exchange_params, timeout=10)
        print(f"  Status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            long_token = data.get("access_token")
            expires_in = data.get("expires_in", "unknown")
            
            print(f"  ✅ SUCCESS! Got long-lived token")
            print(f"  Expires in: {expires_in} seconds")
            
            # 保存到文件
            print(f"\n[3/3] Saving token...")
            
            # 更新 .env 文件
            env_lines = []
            env_file = ".env"
            
            try:
                with open(env_file, "r", encoding="utf-8") as f:
                    env_lines = f.readlines()
            except FileNotFoundError:
                pass
            
            # 更新或添加 THREADS_ACCESS_TOKEN
            token_updated = False
            user_id_updated = False
            new_lines = []
            
            for line in env_lines:
                if line.startswith("THREADS_ACCESS_TOKEN="):
                    new_lines.append(f"THREADS_ACCESS_TOKEN={long_token}\n")
                    token_updated = True
                elif line.startswith("THREADS_USER_ID="):
                    new_lines.append(f"THREADS_USER_ID={user_id}\n")
                    user_id_updated = True
                else:
                    new_lines.append(line)
            
            if not token_updated:
                new_lines.append(f"THREADS_ACCESS_TOKEN={long_token}\n")
            if not user_id_updated:
                new_lines.append(f"THREADS_USER_ID={user_id}\n")
            
            with open(env_file, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
            
            print(f"  ✅ Token saved to {env_file}")
            
            # 同时保存到 token 文件
            with open("threads_token.txt", "w", encoding="utf-8") as f:
                f.write(f"THREADS_ACCESS_TOKEN={long_token}\n")
                f.write(f"THREADS_USER_ID={user_id}\n")
                f.write(f"USERNAME={username}\n")
                f.write(f"EXPIRES_IN={expires_in} seconds\n")
            
            print(f"  ✅ Token also saved to threads_token.txt")
            
            print(f"\n" + "=" * 60)
            print("🎉 Threads Token 配置完成！")
            print("=" * 60)
            print(f"\nAccess Token: {long_token[:50]}...")
            print(f"User ID: {user_id}")
            print(f"\n⚠️  注意：长期 Token 已保存，请妥善保管！")
            
        else:
            print(f"  Response: {r.text}")
            print(f"  ❌ Exchange failed")
            
            # 如果方法2也失败，直接保存短期 Token
            print(f"\n⚠️  无法获取长期 Token，将保存短期 Token（1-2小时有效）")
            print(f"\n[3/3] Saving short-lived token...")
            
            with open("threads_token_short.txt", "w", encoding="utf-8") as f:
                f.write(f"THREADS_ACCESS_TOKEN={short_token}\n")
                f.write(f"THREADS_USER_ID={user_id}\n")
                f.write(f"USERNAME={username}\n")
            
            print(f"  ✅ Short token saved to threads_token_short.txt")
            print(f"\n💡 提示：短期 Token 需要定期重新生成")
            
    except Exception as e:
        print(f"  ❌ Error: {e}")

if __name__ == "__main__":
    main()
