"""
Substack Editor Inspector - 检查编辑器页面的实际UI元素
用于调试发布按钮问题
"""
import os
import sys
import time

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright

SUBSTACK_EMAIL = os.environ.get("SUBSTACK_EMAIL", "")
SUBSTACK_PASSWORD = os.environ.get("SUBSTACK_PASSWORD", "")
PUB_URL = "https://broadcastmarketintelligence.substack.com"

def inspect_editor():
    """检查Substack编辑器页面的UI元素"""
    print("=" * 60)
    print("Substack Editor Inspector")
    print("=" * 60)
    
    with sync_playwright() as p:
        # 使用持久化上下文
        session_dir = ".browser_sessions/substack_profile"
        os.makedirs(session_dir, exist_ok=True)
        
        browser = p.chromium.launch_persistent_context(
            session_dir,
            headless=False,  # 非headless模式，方便观察
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = browser.new_page()
        
        try:
            # 1. 检查登录状态
            print("\n[1] 检查登录状态...")
            page.goto(f"{PUB_URL}/dashboard", timeout=15000)
            time.sleep(3)
            
            if "/dashboard" in page.url or "/publish/posts" in page.url:
                print("  ✅ 已登录")
            else:
                print("  ⚠️ 未登录，尝试登录...")
                # 登录流程
                page.goto("https://substack.com/sign-in", timeout=15000)
                time.sleep(2)
                
                # 输入邮箱
                email_input = page.locator('input[type="email"]').first
                if email_input.is_visible():
                    email_input.fill(SUBSTACK_EMAIL)
                    page.locator('button[type="submit"]').first.click()
                    time.sleep(3)
                    
                    # 输入密码
                    pwd_input = page.locator('input[type="password"]').first
                    if pwd_input.is_visible():
                        pwd_input.fill(SUBSTACK_PASSWORD)
                        page.locator('button[type="submit"]').first.click()
                        time.sleep(5)
            
            # 2. 进入编辑器
            print("\n[2] 进入编辑器...")
            page.goto("https://substack.com/write", timeout=15000)
            time.sleep(5)
            
            # 等待页面加载
            print(f"  当前URL: {page.url}")
            page.screenshot(path="substack_inspector_editor.png")
            print("  截图已保存: substack_inspector_editor.png")
            
            # 3. 填充测试内容
            print("\n[3] 填充测试内容...")
            
            # 标题
            title_input = page.locator('input[placeholder*="title"], input[placeholder*="Title"]').first
            if title_input.is_visible():
                title_input.fill("Test Title - Inspector")
                print("  ✅ 标题已填充")
            
            # 内容
            content_area = page.locator('[contenteditable="true"]').first
            if content_area.is_visible():
                content_area.fill("This is test content for inspector.")
                print("  ✅ 内容已填充")
            
            time.sleep(2)
            
            # 4. 检查所有按钮
            print("\n[4] 检查页面上的所有按钮...")
            print("-" * 60)
            
            buttons = page.locator('button').all()
            print(f"  找到 {len(buttons)} 个 button 元素:")
            
            for i, btn in enumerate(buttons[:20]):  # 只显示前20个
                try:
                    text = btn.inner_text().strip()[:50] if btn.is_visible() else "(hidden)"
                    aria = btn.get_attribute('aria-label') or ""
                    data_testid = btn.get_attribute('data-testid') or ""
                    print(f"    [{i}] Text: '{text}' | aria-label: '{aria}' | data-testid: '{data_testid}'")
                except Exception as e:
                    print(f"    [{i}] Error: {e}")
            
            # 5. 检查 role="button" 的元素
            print("\n[5] 检查 role='button' 的元素...")
            print("-" * 60)
            
            role_buttons = page.locator('[role="button"]').all()
            print(f"  找到 {len(role_buttons)} 个 role='button' 元素:")
            
            for i, btn in enumerate(role_buttons[:15]):
                try:
                    text = btn.inner_text().strip()[:50] if btn.is_visible() else "(hidden)"
                    aria = btn.get_attribute('aria-label') or ""
                    print(f"    [{i}] Text: '{text}' | aria-label: '{aria}'")
                except Exception as e:
                    print(f"    [{i}] Error: {e}")
            
            # 6. 检查特定发布相关按钮
            print("\n[6] 检查发布相关按钮...")
            print("-" * 60)
            
            keywords = ["Publish", "Continue", "Post", "Send", "Draft", "Save"]
            for kw in keywords:
                try:
                    # button
                    btns = page.locator(f'button:has-text("{kw}")').all()
                    for btn in btns:
                        if btn.is_visible():
                            text = btn.inner_text().strip()
                            print(f"  ✅ button:has-text('{kw}') -> '{text}'")
                    
                    # role=button
                    role_btns = page.locator(f'[role="button"]:has-text("{kw}")').all()
                    for btn in role_btns:
                        if btn.is_visible():
                            text = btn.inner_text().strip()
                            print(f"  ✅ [role='button']:has-text('{kw}') -> '{text}'")
                except Exception as e:
                    print(f"  ❌ Error checking '{kw}': {e}")
            
            # 7. 检查右上角区域
            print("\n[7] 检查右上角区域...")
            print("-" * 60)
            
            # 获取页面HTML右上部分
            html = page.content()
            # 查找包含 "Publish" 或 "Continue" 的附近HTML
            import re
            matches = re.findall(r'.{0,100}Publish.{0,100}', html, re.IGNORECASE)
            for i, m in enumerate(matches[:5]):
                print(f"  Match {i}: {m[:100]}...")
            
            print("\n" + "=" * 60)
            print("检查完成。请查看截图和上述输出。")
            print("=" * 60)
            
            # 保持浏览器打开，方便手动检查
            print("\n浏览器保持打开状态，请手动检查后关闭...")
            input("按 Enter 键关闭浏览器...")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            page.screenshot(path="substack_inspector_error.png")
            
        finally:
            browser.close()

if __name__ == "__main__":
    inspect_editor()
