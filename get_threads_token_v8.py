#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BroadFSC - Threads Token Getter v8
====================================
新策略：半自动模式 + 智能重定向拦截

核心改进：
1. 不再自动填密码（避免 FB 检测自动化）
2. 打开浏览器让用户手动完成 FB 登录
3. 用 page.route() 拦截 OAuth 重定向，直接从 URL 提取 code
4. 用户登录后，脚本自动完成剩余 OAuth 流程
5. 支持 headless=False 交互模式

Usage:
    python get_threads_token_v8.py [--auto]  # --auto 尝试全自动（可能被检测）
    python get_threads_token_v8.py            # 半自动（手动登录FB，自动完成OAuth）
"""

import sys
import os
import time
import re
import json
import requests
from urllib.parse import urlparse, parse_qs

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# ============================================================
# Config
# ============================================================
FB_EMAIL = "msli2233bin@gmail.com"
FB_PASSWORD = "Lin2233509."

APP_ID = "1479983126925807"
APP_SECRET = "9857adbca8c910959a78e14d813c0e53"
API_BASE = "https://graph.threads.net/v1.0"
REDIRECT_URI = "https://www.broadfsc.com/different"

SESSION_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".browser_sessions")
PROFILE_DIR = os.path.join(SESSION_DIR, "meta_threads_profile_v8")
TOKEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "threads_token.txt")
ENV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")

AUTO_MODE = "--auto" in sys.argv

os.makedirs(PROFILE_DIR, exist_ok=True)

# Remove lock files
for lock_name in ["SingletonLock", "SingletonCookie", "SingletonSocket"]:
    lf = os.path.join(PROFILE_DIR, lock_name)
    if os.path.exists(lf):
        try:
            os.remove(lf)
        except Exception:
            pass


def exchange_code_for_token(code):
    """用 authorization code 换取 access_token"""
    print(f"\n{'='*50}")
    print(f"Exchanging authorization code for token...")
    print(f"  Code: {code[:30]}...")
    
    # Threads Graph API
    try:
        r = requests.get(f"{API_BASE}/oauth/access_token", params={
            "client_id": APP_ID,
            "client_secret": APP_SECRET,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
            "code": code,
        }, timeout=30)
        print(f"  Threads API: HTTP {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            token = data.get("access_token")
            if token:
                print(f"  ✅ Got short-lived token! Length: {len(token)}")
                return token
        print(f"  Response: {r.text[:200]}")
    except Exception as e:
        print(f"  Error: {e}")
    
    return None


def try_exchange_to_long_lived(token):
    """尝试换长期 Token"""
    print(f"\n{'='*50}")
    print("Exchanging for long-lived token...")
    
    # A: th_exchange_token (Threads 专用)
    print("\n  [A] th_exchange_token...")
    try:
        r = requests.get(f"{API_BASE}/access_token", params={
            "grant_type": "th_exchange_token",
            "client_secret": APP_SECRET,
            "access_token": token,
        }, timeout=30)
        if r.status_code == 200:
            data = r.json()
            new_token = data.get("access_token")
            expires_in = data.get("expires_in", 0)
            days = int(expires_in) // 86400 if expires_in else 0
            print(f"  ✅ Long-lived token (~{days} days)")
            return new_token, "long_lived", f"~{days} days"
        print(f"  ❌ HTTP {r.status_code}: {r.text[:150]}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # B: fb_exchange_token
    print("\n  [B] fb_exchange_token via FB Graph...")
    try:
        r = requests.get("https://graph.facebook.com/v21.0/oauth/access_token", params={
            "grant_type": "fb_exchange_token",
            "client_id": APP_ID,
            "client_secret": APP_SECRET,
            "fb_exchange_token": token,
        }, timeout=30)
        if r.status_code == 200:
            data = r.json()
            new_token = data.get("access_token")
            if new_token and new_token != token:
                vr = requests.get(f"{API_BASE}/me", params={"access_token": new_token}, timeout=10)
                if vr.status_code == 200:
                    print(f"  ✅ Long-lived via FB Graph!")
                    return new_token, "long_lived", "via fb_exchange_token"
        print(f"  ❌ HTTP {r.status_code}: {r.text[:150]}")
    except Exception as e:
        print(f"  ❌ Error (likely network): {e}")
    
    # C: Debug token
    print("\n  [C] Debug token info...")
    try:
        r = requests.get(f"{API_BASE}/debug_token", params={
            "input_token": token,
            "access_token": f"{APP_ID}|{APP_SECRET}",
        }, timeout=15)
        if r.status_code == 200:
            data = r.json().get("data", {})
            expires_at = data.get("expires_at", 0)
            is_valid = data.get("is_valid", False)
            scopes = data.get("scopes", [])
            print(f"     is_valid={is_valid}, scopes={scopes}")
            if expires_at == 0:
                return token, "long_lived", "Never expires (app_token?)"
            remaining = expires_at - int(time.time())
            days_left = remaining // 86400
            if days_left > 7:
                return token, "long_lived", f"~{days_left} days left"
        else:
            print(f"  ❌ HTTP {r.status_code}: {r.text[:150]}")
    except Exception:
        pass
    
    # D: Direct verify
    print("\n  [D] Direct verification...")
    try:
        r = requests.get(f"{API_BASE}/me", params={"access_token": token}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            print(f"  ✅ Token works! @{data.get('username')} (ID: {data.get('id')})")
            return token, "valid", "Works (expiry unknown)"
    except Exception:
        pass
    
    return token, "unknown", "Status unclear"


def save_token(token, token_type, expires_info):
    """保存 Token"""
    username, user_id = "unknown", "35426966120283926"
    try:
        r = requests.get(f"{API_BASE}/me", params={"access_token": token}, timeout=10)
        if r.status_code == 200:
            d = r.json()
            user_id = d.get("id", user_id)
            username = d.get("username", username)
    except Exception:
        pass
    print(f"  User: @{username} (ID: {user_id})")
    
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        f.write(f"# BroadFSC Threads Token\n")
        f.write(f"# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Type: {token_type}\n")
        f.write(f"# Expires: {expires_info}\n")
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
    
    updated = {"token": False, "uid": False, "secret": False}
    new_lines = []
    for line in env_lines:
        if line.startswith("THREADS_ACCESS_TOKEN="):
            new_lines.append(f"THREADS_ACCESS_TOKEN={token}\n")
            updated["token"] = True
        elif line.startswith("THREADS_USER_ID="):
            new_lines.append(f"THREADS_USER_ID={user_id}\n")
            updated["uid"] = True
        elif line.startswith("THREADS_APP_SECRET="):
            new_lines.append(f"THREADS_APP_SECRET={APP_SECRET}\n")
            updated["secret"] = True
        elif line.startswith("# THREADS_ACCESS_TOKEN will be set"):
            continue
        else:
            new_lines.append(line)
    
    if not updated["token"]:
        new_lines.append(f"THREADS_ACCESS_TOKEN={token}\n")
    if not updated["uid"]:
        new_lines.append(f"THREADS_USER_ID={user_id}\n")
    if not updated["secret"]:
        new_lines.append(f"THREADS_APP_SECRET={APP_SECRET}\n")
    
    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print(f"  ✅ Updated {ENV_FILE}")


def test_post(token):
    """测试发帖"""
    try:
        r = requests.get(f"{API_BASE}/me", params={"access_token": token}, timeout=10)
        user_id = r.json().get("id") if r.status_code == 200 else "35426966120283926"
        
        r = requests.post(f"{API_BASE}/{user_id}/threads", params={
            "media_type": "TEXT",
            "text": "🔧 BroadFSC automation test - please ignore",
            "access_token": token,
        }, timeout=15)
        
        if r.status_code == 200:
            cid = r.json().get("id")
            r2 = requests.post(f"{API_BASE}/{user_id}/threads_publish", params={
                "creation_id": cid,
                "access_token": token,
            }, timeout=15)
            if r2.status_code == 200:
                print(f"  ✅ TEST POST PUBLISHED!")
                return True
            print(f"  ❌ Publish failed: {r2.text[:150]}")
        else:
            print(f"  ❌ Container failed: {r.text[:150]}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    return False


def main():
    print("=" * 60)
    print("BroadFSC - Threads Token Getter v8")
    print("=" * 60)
    mode_str = "AUTO" if AUTO_MODE else "SEMI-AUTO (manual FB login)"
    print(f"Mode: {mode_str}")
    print(f"Strategy: OAuth code flow with redirect interception")
    
    token = None
    captured_code = None
    
    with sync_playwright() as p:
        # 启动浏览器 - 加强反检测
        context = p.chromium.launch_persistent_context(
            PROFILE_DIR,
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-features=IsolateOrigins,site-per-process",
                "--disable-site-isolation-trials",
                "--start-maximized",
                "--foreground",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-infobars",
                "--window-size=1280,900",
            ],
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            locale="en-US",
            timezone_id="America/New_York",
        )
        
        # 反自动化检测：覆盖 navigator.webdriver
        for page in context.pages:
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                window.chrome = {runtime: {}};
            """)
        
        page = context.pages[0] if context.pages else context.new_page()
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            window.chrome = {runtime: {}};
        """)
        
        try:
            # ================================================
            # Step 1: Facebook 登录
            # ================================================
            print(f"\n{'='*50}")
            print("Step 1: Facebook Login")
            print(f"{'='*50}")
            
            page.goto("https://www.facebook.com/", wait_until='domcontentloaded', timeout=60000)
            time.sleep(3)
            
            current_url = page.url
            print(f"  Current URL: {current_url[:80]}")
            
            if "login" in current_url.lower():
                if AUTO_MODE:
                    # 自动填密码模式
                    print("  [AUTO] Filling credentials...")
                    time.sleep(1)
                    
                    # 随机鼠标移动模拟人类
                    import random
                    for _ in range(3):
                        page.mouse.move(random.randint(100, 800), random.randint(100, 500))
                        time.sleep(0.3)
                    
                    # 填写邮箱
                    email_filled = False
                    for sel in ['input[name="email"]', 'input[type="email"]', 'input[type="text"]']:
                        try:
                            elem = page.query_selector(sel)
                            if elem and elem.is_visible():
                                elem.click()
                                time.sleep(0.5)
                                page.keyboard.type(FB_EMAIL, delay=random.randint(50, 120))
                                email_filled = True
                                print(f"  ✅ Email typed via {sel}")
                                break
                        except Exception:
                            continue
                    
                    time.sleep(random.uniform(0.5, 1.5))
                    
                    # 填写密码
                    pass_filled = False
                    for sel in ['input[name="pass"]', 'input[type="password"]']:
                        try:
                            elem = page.query_selector(sel)
                            if elem and elem.is_visible():
                                elem.click()
                                time.sleep(0.3)
                                page.keyboard.type(FB_PASSWORD, delay=random.randint(50, 120))
                                pass_filled = True
                                print(f"  ✅ Password typed via {sel}")
                                break
                        except Exception:
                            continue
                    
                    time.sleep(random.uniform(0.8, 2.0))
                    
                    # 点击登录
                    for sel in ['button[name="login"]', 'button[type="submit"]', 'label[id="loginbutton"]']:
                        try:
                            elem = page.query_selector(sel)
                            if elem and elem.is_visible():
                                elem.click()
                                print(f"  ✅ Clicked login via {sel}")
                                break
                        except Exception:
                            continue
                    else:
                        page.keyboard.press('Enter')
                        print("  Pressed Enter")
                    
                    time.sleep(8)
                    
                else:
                    # 半自动模式 - 等待用户手动登录
                    print("\n  ⚠️  SEMI-AUTO MODE")
                    print("  ═════════════════════════════════════════════")
                    print("  Please log in to Facebook manually in the browser window.")
                    print("  After logging in, the script will continue automatically.")
                    print("  ═════════════════════════════════════════════\n")
                    
                    # 等待用户完成登录（最多 5 分钟）
                    for i in range(60):
                        time.sleep(5)
                        current_url = page.url
                        # 检查是否已经不在登录页了
                        if "login" not in current_url.lower():
                            print(f"  ✅ Login detected! URL: {current_url[:80]}")
                            break
                        if i % 6 == 0 and i > 0:
                            print(f"  Still waiting for login... ({i*5}s)")
                    else:
                        print("  ❌ Login timeout (5 min)")
                        return
                
                # 处理登录后弹窗
                time.sleep(3)
                for text in ['Save Browser', '保存浏览器', 'Not Now', '以后再说', 'Done', '完成', 'OK']:
                    try:
                        btn = page.query_selector(f'button:has-text("{text}")')
                        if btn and btn.is_visible():
                            btn.click()
                            print(f"  Dismissed: {text}")
                            time.sleep(1)
                    except Exception:
                        continue
            else:
                print("  ✅ Already logged in to Facebook!")
            
            # ================================================
            # Step 2: OAuth 授权 - 用 route() 拦截重定向
            # ================================================
            print(f"\n{'='*50}")
            print("Step 2: OAuth Authorization")
            print(f"{'='*50}")
            
            # 构造 OAuth URL
            oauth_url = (
                f"https://www.facebook.com/v21.0/dialog/oauth?"
                f"client_id={APP_ID}&"
                f"redirect_uri={REDIRECT_URI}&"
                f"scope=threads_basic,threads_content_publish&"
                f"response_type=code"
            )
            
            print(f"  OAuth URL: {oauth_url[:100]}...")
            
            # 设置重定向拦截
            # 当 OAuth 授权成功后，FB 会重定向到 redirect_uri?code=xxx
            # 我们用 route() 拦截这个请求，提取 code，不需要 redirect_uri 真正可访问
            
            def handle_redirect(route):
                nonlocal captured_code
                url = route.request.url
                print(f"\n  🔗 Intercepted redirect: {url[:120]}")
                
                if "broadfsc.com" in url and "code=" in url:
                    parsed = urlparse(url)
                    params = parse_qs(parsed.query)
                    code = params.get("code", [None])[0]
                    if code:
                        captured_code = code
                        print(f"  ✅ CAPTURED CODE: {code[:30]}...")
                        # 返回一个简单响应，阻止浏览器真正访问 redirect_uri
                        route.fulfill(
                            status=200,
                            content_type="text/html",
                            body="<html><body><h1>OAuth Success! You can close this tab.</h1></body></html>"
                        )
                        return
                
                if "error" in url:
                    parsed = urlparse(url)
                    params = parse_qs(parsed.query)
                    error = params.get("error", [""])[0]
                    error_desc = params.get("error_description", [""])[0]
                    print(f"  ❌ OAuth error: {error} - {error_desc}")
                    route.fulfill(
                        status=200,
                        content_type="text/html",
                        body=f"<html><body><h1>OAuth Error: {error}</h1><p>{error_desc}</p></body></html>"
                    )
                    return
                
                # 其他请求正常通过
                route.continue_()
            
            # 注册拦截规则 - 拦截到 broadfsc.com 的请求
            context.route("**/broadfsc.com/**", handle_redirect)
            
            # 导航到 OAuth URL
            print("  Navigating to OAuth dialog...")
            page.goto(oauth_url, wait_until='domcontentloaded', timeout=60000)
            time.sleep(5)
            
            current_url = page.url
            print(f"  Current URL: {current_url[:120]}")
            
            # 检查是否已经拿到了 code
            if captured_code:
                print("  ✅ Code captured from redirect!")
                token = exchange_code_for_token(captured_code)
            
            # 如果没有自动捕获，检查当前页面状态
            elif "broadfsc.com" in current_url and "code=" in current_url:
                parsed = urlparse(current_url)
                params = parse_qs(parsed.query)
                code = params.get("code", [None])[0]
                if code:
                    print(f"  ✅ Found code in URL: {code[:30]}...")
                    token = exchange_code_for_token(code)
            
            elif "dialog/oauth" in current_url or "connect" in current_url.lower():
                # 在 OAuth 授权页面 - 需要用户点击授权
                print("\n  On OAuth dialog page - looking for authorize button...")
                
                # 截图
                try:
                    page.screenshot(path="debug_v8_oauth.png")
                    print("  Screenshot saved: debug_v8_oauth.png")
                except Exception:
                    pass
                
                # 列出所有可见按钮
                try:
                    buttons = page.evaluate('''() => {
                        return Array.from(document.querySelectorAll('button, input[type="submit"], div[role="button"], a[role="button"]'))
                            .filter(e => e.offsetParent !== null)
                            .map(e => ({text: (e.innerText || e.value || '').trim().substring(0, 60), tag: e.tagName, name: e.name, type: e.type}));
                    }''')
                    print(f"  Visible buttons: {json.dumps(buttons[:20], ensure_ascii=False)}")
                except Exception:
                    pass
                
                # 尝试自动点击授权按钮
                authorized = False
                for text in ['Continue as', '继续', 'Continue', 'Allow', 'OK', '确认', '授权', 'Accept']:
                    try:
                        btn = page.query_selector(f'button:has-text("{text}"), div[role="button"]:has-text("{text}")')
                        if btn and btn.is_visible():
                            print(f"  Clicking: {text}")
                            btn.click()
                            authorized = True
                            time.sleep(5)
                            break
                    except Exception:
                        continue
                
                # 尝试 name=__CONFIRM__
                if not authorized:
                    for sel in ['button[name="__CONFIRM__"]', 'input[name="__CONFIRM__"]', 
                                'button[name="grant_clicked"]', 'button[name="__ACCEPT__"]']:
                        try:
                            elem = page.query_selector(sel)
                            if elem and elem.is_visible():
                                elem.click()
                                print(f"  Clicked: {sel}")
                                authorized = True
                                time.sleep(5)
                                break
                        except Exception:
                            continue
                
                if not authorized:
                    if AUTO_MODE:
                        page.keyboard.press('Enter')
                        print("  Pressed Enter (fallback)")
                        time.sleep(5)
                    else:
                        print("\n  ⚠️  Could not auto-authorize.")
                        print("  Please click the authorize/continue button in the browser window.")
                        # 等待用户点击
                        for i in range(30):
                            time.sleep(2)
                            if captured_code:
                                break
                            current_url = page.url
                            if "broadfsc.com" in current_url and "code=" in current_url:
                                parsed = urlparse(current_url)
                                params = parse_qs(parsed.query)
                                code = params.get("code", [None])[0]
                                if code:
                                    captured_code = code
                                break
                
                # 检查是否捕获到 code
                if captured_code:
                    print("  ✅ Code captured!")
                    token = exchange_code_for_token(captured_code)
                else:
                    current_url = page.url
                    print(f"  Current URL after authorize: {current_url[:120]}")
                    if "broadfsc.com" in current_url and "code=" in current_url:
                        parsed = urlparse(current_url)
                        params = parse_qs(parsed.query)
                        code = params.get("code", [None])[0]
                        if code:
                            token = exchange_code_for_token(code)
                    elif "error" in current_url:
                        parsed = urlparse(current_url)
                        params = parse_qs(parsed.query)
                        error = params.get("error", [""])[0]
                        error_desc = params.get("error_description", [""])[0]
                        print(f"  ❌ OAuth error: {error} - {error_desc}")
            
            elif "login.php" in current_url:
                print("\n  ⚠️  FB requires re-login for OAuth (session expired).")
                if AUTO_MODE:
                    print("  [AUTO] Re-filling credentials...")
                    import random
                    for sel_e, cred in [('input[name="email"]', FB_EMAIL), ('input[name="pass"]', FB_PASSWORD)]:
                        try:
                            elem = page.query_selector(sel_e)
                            if elem and elem.is_visible():
                                elem.click()
                                time.sleep(0.3)
                                page.keyboard.type(cred, delay=random.randint(50, 120))
                                print(f"  Typed into {sel_e}")
                        except Exception:
                            continue
                    time.sleep(1)
                    page.keyboard.press('Enter')
                    time.sleep(8)
                    
                    # 检查是否拿到了 code
                    if captured_code:
                        token = exchange_code_for_token(captured_code)
                    else:
                        current_url = page.url
                        if "broadfsc.com" in current_url and "code=" in current_url:
                            parsed = urlparse(current_url)
                            params = parse_qs(parsed.query)
                            code = params.get("code", [None])[0]
                            if code:
                                token = exchange_code_for_token(code)
                else:
                    print("  Please log in again in the browser window.")
                    for i in range(60):
                        time.sleep(5)
                        if captured_code:
                            break
                        current_url = page.url
                        if "broadfsc.com" in current_url and "code=" in current_url:
                            parsed = urlparse(current_url)
                            params = parse_qs(parsed.query)
                            code = params.get("code", [None])[0]
                            if code:
                                captured_code = code
                            break
                        if "login" not in current_url.lower():
                            # 登录成功，可能在 OAuth 对话页
                            time.sleep(3)
                            # 重新检查
                            current_url = page.url
                            print(f"  After re-login: {current_url[:80]}")
                            break
                    
                    if captured_code:
                        token = exchange_code_for_token(captured_code)
            
            else:
                print(f"  ⚠️ Unexpected page: {current_url[:100]}")
                try:
                    page.screenshot(path="debug_v8_unexpected.png")
                except Exception:
                    pass
                try:
                    body = page.inner_text('body')[:500]
                    print(f"  Body: {body[:300]}")
                except Exception:
                    pass
            
            # ================================================
            # Step 3: 如果还是没拿到 token，检查已有 token
            # ================================================
            if not token:
                print(f"\n{'='*50}")
                print("Step 3: Checking existing token...")
                
                # 检查 .env 和 threads_token.txt
                for tf in [TOKEN_FILE, ENV_FILE]:
                    try:
                        with open(tf, "r", encoding="utf-8") as f:
                            for line in f:
                                if line.startswith("THREADS_ACCESS_TOKEN="):
                                    old_token = line.strip().split("=", 1)[1]
                                    if old_token and len(old_token) > 50:
                                        vr = requests.get(f"{API_BASE}/me", params={"access_token": old_token}, timeout=10)
                                        if vr.status_code == 200:
                                            print(f"  ✅ Existing token still works from {tf}!")
                                            token = old_token
                                            break
                    except Exception:
                        pass
                if token:
                    print("  Using existing valid token.")
        
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # 取消路由拦截
            try:
                context.unroute("**/broadfsc.com/**")
            except Exception:
                pass
            print("\n🔒 Closing browser in 5s...")
            time.sleep(5)
            try:
                context.close()
            except Exception:
                pass
    
    # ================================================
    # 后处理
    # ================================================
    if not token:
        print("\n❌ No token obtained. Possible reasons:")
        print("  1. FB detected automation and blocked login")
        print("  2. OAuth redirect was not captured")
        print("  3. FB requires 2FA / security verification")
        print("\n  Suggestions:")
        print("  - Run without --auto flag for manual login")
        print("  - Check debug_v8_*.png screenshots")
        print("  - Try from a different IP/network")
        return
    
    # Exchange to long-lived
    final_token, token_type, expires_info = try_exchange_to_long_lived(token)
    
    # Save + test
    save_token(final_token, token_type, expires_info)
    
    print(f"\n{'='*60}")
    print("🎉 Thread Token Result")
    print(f"{'='*60}")
    print(f"  Token: {final_token[:30]}...{final_token[-10:]}")
    print(f"  Type: {token_type}")
    print(f"  Expires: {expires_info}")
    
    # Test posting
    print(f"\n{'='*50}")
    print("Testing post...")
    test_post(final_token)


if __name__ == "__main__":
    main()
