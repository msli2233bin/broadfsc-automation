#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Threads OAuth Token 获取工具
通过启动本地 HTTP 服务器接收 OAuth 回调，自动完成 Token 交换流程

使用方法：
1. 运行此脚本
2. 在浏览器打开脚本输出的授权链接
3. 授权后自动回调本地服务器，脚本自动完成 Token 交换
"""

import sys
import json
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# App 凭证
APP_ID = "1479983126925807"
APP_SECRET = "9857adbca8c910959a78e14d813c0e53"
REDIRECT_URI = "https://www.broadfsc.com/"
SCOPES = "threads_basic,threads_content_publish"
PORT = 8888

# 全局变量存储结果
result_token = {"long_lived": None, "user_id": None, "username": None}


class OAuthHandler(BaseHTTPRequestHandler):
    """处理 OAuth 回调的 HTTP Handler"""
    
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        
        if "code" in params:
            code = params["code"][0]
            print(f"\n[OK] Got authorization code!")
            
            # Step 2: 用 code 换取短期 Token
            print(f"[2/4] Exchanging code for short-lived token...")
            token_url = "https://graph.threads.net/v1.0/access_token"
            token_params = {
                "client_id": APP_ID,
                "client_secret": APP_SECRET,
                "grant_type": "authorization_code",
                "redirect_uri": REDIRECT_URI,
                "code": code,
            }
            
            try:
                r = requests.get(token_url, params=token_params, timeout=15)
                print(f"  Status: {r.status_code}")
                
                if r.status_code == 200:
                    data = r.json()
                    short_token = data.get("access_token")
                    user_id = data.get("user_id")
                    print(f"  Short-lived token: {short_token[:30]}...")
                    print(f"  User ID: {user_id}")
                    
                    # Step 3: 换取长期 Token
                    print(f"\n[3/4] Exchanging for long-lived token (60 days)...")
                    exchange_url = "https://graph.threads.net/v1.0/access_token"
                    exchange_params = {
                        "grant_type": "th_exchange_token",
                        "client_secret": APP_SECRET,
                        "access_token": short_token,
                    }
                    
                    r2 = requests.get(exchange_url, params=exchange_params, timeout=15)
                    print(f"  Status: {r2.status_code}")
                    
                    if r2.status_code == 200:
                        data2 = r2.json()
                        long_token = data2.get("access_token")
                        expires_in = data2.get("expires_in", "unknown")
                        print(f"  Long-lived token: {long_token[:30]}...")
                        print(f"  Expires in: {expires_in} seconds")
                        
                        # Step 4: 获取用户信息
                        print(f"\n[4/4] Getting user info...")
                        me_url = "https://graph.threads.net/v1.0/me"
                        me_params = {"access_token": long_token}
                        r3 = requests.get(me_url, params=me_params, timeout=10)
                        
                        if r3.status_code == 200:
                            me_data = r3.json()
                            username = me_data.get("username", "unknown")
                            uid = me_data.get("id", user_id)
                            print(f"  Username: @{username}")
                            print(f"  User ID: {uid}")
                        else:
                            uid = user_id
                            username = "unknown"
                        
                        # 保存结果
                        result_token["long_lived"] = long_token
                        result_token["user_id"] = uid
                        result_token["username"] = username
                        
                        # 保存到文件
                        with open("threads_token.txt", "w", encoding="utf-8") as f:
                            f.write(f"THREADS_ACCESS_TOKEN={long_token}\n")
                            f.write(f"THREADS_USER_ID={uid}\n")
                            f.write(f"USERNAME={username}\n")
                            f.write(f"EXPIRES_IN={expires_in} seconds\n")
                        
                        # 也更新 .env
                        self.update_env(long_token, uid)
                        
                        success_html = f"""
                        <html><body style="font-family:sans-serif;text-align:center;padding:50px">
                        <h1 style="color:green">Token 获取成功!</h1>
                        <p>Username: @{username}</p>
                        <p>User ID: {uid}</p>
                        <p>Token 有效期: {expires_in} 秒 (约 {int(expires_in)//86400} 天)</p>
                        <p>已保存到 threads_token.txt 和 .env</p>
                        <p>可以关闭此页面</p>
                        </body></html>
                        """
                        
                        self.send_response(200)
                        self.send_header("Content-type", "text/html; charset=utf-8")
                        self.end_headers()
                        self.wfile.write(success_html.encode("utf-8"))
                        
                        print(f"\n{'='*60}")
                        print(f"SUCCESS! Threads Token configured!")
                        print(f"{'='*60}")
                        print(f"Access Token: {long_token[:50]}...")
                        print(f"User ID: {uid}")
                        print(f"Saved to: threads_token.txt + .env")
                        
                        # 停止服务器
                        threading.Thread(target=self.server.shutdown, daemon=True).start()
                        return
                    
                    else:
                        print(f"  Exchange failed: {r2.text}")
                        error_html = f"<html><body><h1>Exchange Failed</h1><pre>{r2.text}</pre></body></html>"
                        self.send_response(200)
                        self.send_header("Content-type", "text/html; charset=utf-8")
                        self.end_headers()
                        self.wfile.write(error_html.encode("utf-8"))
                        threading.Thread(target=self.server.shutdown, daemon=True).start()
                        return
                else:
                    print(f"  Code exchange failed: {r.text}")
                    error_html = f"<html><body><h1>Code Exchange Failed</h1><pre>{r.text}</pre></body></html>"
                    self.send_response(200)
                    self.send_header("Content-type", "text/html; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(error_html.encode("utf-8"))
                    threading.Thread(target=self.server.shutdown, daemon=True).start()
                    return
                    
            except Exception as e:
                print(f"  Error: {e}")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(f"Error: {e}".encode())
                threading.Thread(target=self.server.shutdown, daemon=True).start()
                return
        
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"No code parameter found")
    
    def update_env(self, token, user_id):
        """更新 .env 文件"""
        env_lines = []
        try:
            with open(".env", "r", encoding="utf-8") as f:
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
            else:
                new_lines.append(line)
        
        if not token_updated:
            new_lines.append(f"THREADS_ACCESS_TOKEN={token}\n")
        if not uid_updated:
            new_lines.append(f"THREADS_USER_ID={user_id}\n")
        if not secret_updated:
            new_lines.append(f"THREADS_APP_SECRET={APP_SECRET}\n")
        
        with open(".env", "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        
        print(f"  .env updated!")


def main():
    print("=" * 60)
    print("Threads OAuth Token Tool")
    print("=" * 60)
    
    # 构建授权 URL
    auth_url = (
        f"https://www.threads.net/oauth/authorize"
        f"?client_id={APP_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope={SCOPES}"
        f"&response_type=code"
    )
    
    print(f"\n[1/4] Open this URL in your browser (logged in as @msli637):")
    print(f"\n{auth_url}\n")
    
    print("After authorization, you'll be redirected to broadfsc.com/?code=XXXXX")
    print("Copy the 'code' parameter from the URL, then paste it below:")
    print()
    
    # 方式1: 手动输入 code
    code = input("Paste the authorization code here: ").strip()
    
    if not code:
        print("No code provided, exiting.")
        return
    
    # 换取短期 Token
    print(f"\n[2/4] Exchanging code for short-lived token...")
    token_url = "https://graph.threads.net/v1.0/access_token"
    token_params = {
        "client_id": APP_ID,
        "client_secret": APP_SECRET,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "code": code,
    }
    
    try:
        r = requests.get(token_url, params=token_params, timeout=15)
        print(f"  Status: {r.status_code}")
        print(f"  Response: {r.text[:200]}")
        
        if r.status_code != 200:
            print("  Code exchange failed!")
            return
        
        data = r.json()
        short_token = data.get("access_token")
        user_id = data.get("user_id")
        print(f"  Short-lived token: {short_token[:30]}...")
        print(f"  User ID: {user_id}")
        
        # 换取长期 Token
        print(f"\n[3/4] Exchanging for long-lived token (60 days)...")
        exchange_url = "https://graph.threads.net/v1.0/access_token"
        exchange_params = {
            "grant_type": "th_exchange_token",
            "client_secret": APP_SECRET,
            "access_token": short_token,
        }
        
        r2 = requests.get(exchange_url, params=exchange_params, timeout=15)
        print(f"  Status: {r2.status_code}")
        print(f"  Response: {r2.text[:200]}")
        
        if r2.status_code == 200:
            data2 = r2.json()
            long_token = data2.get("access_token")
            expires_in = data2.get("expires_in", "unknown")
            print(f"  Long-lived token: {long_token[:30]}...")
            print(f"  Expires in: {expires_in} seconds")
            
            # 获取用户信息
            print(f"\n[4/4] Getting user info...")
            me_url = "https://graph.threads.net/v1.0/me"
            me_params = {"access_token": long_token}
            r3 = requests.get(me_url, params=me_params, timeout=10)
            
            username = "unknown"
            uid = user_id
            if r3.status_code == 200:
                me_data = r3.json()
                username = me_data.get("username", "unknown")
                uid = me_data.get("id", user_id)
                print(f"  Username: @{username}")
                print(f"  User ID: {uid}")
            
            # 保存
            with open("threads_token.txt", "w", encoding="utf-8") as f:
                f.write(f"THREADS_ACCESS_TOKEN={long_token}\n")
                f.write(f"THREADS_USER_ID={uid}\n")
                f.write(f"USERNAME={username}\n")
                f.write(f"EXPIRES_IN={expires_in} seconds\n")
            
            print(f"\n{'='*60}")
            print(f"SUCCESS! Long-lived Threads Token acquired!")
            print(f"{'='*60}")
            print(f"Access Token: {long_token[:50]}...")
            print(f"User ID: {uid}")
            print(f"Expires: ~{int(expires_in)//86400} days")
            print(f"Saved to: threads_token.txt")
        else:
            print("  Long-lived token exchange failed!")
            print(f"  Error: {r2.text}")
            
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
