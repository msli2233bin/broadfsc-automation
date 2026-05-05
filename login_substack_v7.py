"""
Substack Auto-Login v7 - Manual Login + Auto-Detect
Flow: Open browser -> User logs in manually -> Script detects login -> Save session
"""
import sys, os, time
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from playwright.sync_api import sync_playwright

SESSION_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".browser_sessions")
PROFILE_DIR = os.path.join(SESSION_DIR, "substack_profile")
os.makedirs(PROFILE_DIR, exist_ok=True)

# Remove lock files from previous crash
for lf_name in ["SingletonLock", "SingletonCookie", "SingletonSocket"]:
    lf = os.path.join(PROFILE_DIR, lf_name)
    if os.path.exists(lf):
        try:
            os.remove(lf)
            print(f"✅ Removed lock: {lf_name}")
        except Exception as e:
            print(f"⚠️ Could not remove {lf_name}: {e}")

EMAIL = "msli2233bin@gmail.com"

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        PROFILE_DIR,
        headless=False,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--start-maximized",
            "--foreground",
        ],
        viewport={"width": 1280, "height": 900},
    )
    page = context.pages[0] if context.pages else context.new_page()

    # Step 1: Check if already logged in
    print("=" * 60)
    print("Step 1: Checking if already logged in...")
    print("=" * 60)
    
    page.goto("https://broadcastmarketintelligence.substack.com/dashboard", timeout=30000)
    time.sleep(5)

    # Handle Cloudflare
    for _ in range(20):
        title = page.title()
        if all(x not in title for x in ["稍候", "Checking", "Just a moment", "Attention", "安全"]):
            break
        print("  ⏳ Waiting for Cloudflare...")
        time.sleep(2)

    try:
        dash_text = page.locator("body").inner_text(timeout=8000)
        is_logged_in = "Create" in dash_text and "Page not found" not in dash_text and "Discover world class culture" not in dash_text
    except Exception:
        is_logged_in = False

    if is_logged_in:
        print("\n✅ ALREADY LOGGED IN! Dashboard accessible.")
        print("Session saved at:", PROFILE_DIR)
        context.close()
        sys.exit(0)

    # Step 2: Open sign-in page, let user log in manually
    print("\n" + "=" * 60)
    print("Step 2: Please log in manually in the browser")
    print("=" * 60)
    print(f"📧 Email: {EMAIL}")
    print()
    print("Instructions:")
    print("  1. Browser will open to substack.com/sign-in")
    print("  2. Enter your email and submit")
    print("  3. Check your email for the Magic Link")
    print("  4. Click the Magic Link (or copy-paste URL into browser)")
    print("  5. After you see the Dashboard, I will auto-detect and save session")
    print()
    print("⏳ Waiting for you to complete login...")
    print("    (I will check every 5 seconds for up to 15 minutes)")
    print()

    # Open sign-in page
    page.goto("https://substack.com/sign-in", timeout=30000)
    time.sleep(3)

    # Step 3: Poll for login detection (max 15 minutes)
    print("=" * 60)
    print("Step 3: Polling for login...")
    print("=" * 60)
    
    MAX_WAIT = 15 * 60  # 15 minutes
    start_time = time.time()
    logged_in = False

    while time.time() - start_time < MAX_WAIT:
        try:
            # Check current URL - if it's not on sign-in page anymore
            current_url = page.url
            
            # Try to access dashboard to verify login
            page.goto("https://broadcastmarketintelligence.substack.com/dashboard", timeout=15000)
            time.sleep(4)
            
            try:
                check_text = page.locator("body").inner_text(timeout=5000)
                if "Create" in check_text and "Page not found" not in check_text:
                    logged_in = True
                    print("\n✅ LOGIN DETECTED! Dashboard is accessible.")
                    break
                elif "Page not found" in check_text:
                    # Try substack.com/dashboard instead
                    page.goto("https://substack.com/dashboard", timeout=15000)
                    time.sleep(3)
                    check_text2 = page.locator("body").inner_text(timeout=5000)
                    if "Create" in check_text2:
                        logged_in = True
                        print("\n✅ LOGIN DETECTED! Dashboard accessible at substack.com.")
                        break
            except Exception:
                pass
            
            # If dashboard check failed, go back to sign-in page to let user continue
            if "/sign-in" in page.url or "/email-login" in page.url or "/login" in page.url:
                pass  # User is still on login page, keep waiting
            else:
                # Navigate back to sign-in to not interfere
                pass
            
        except Exception as e:
            pass
        
        elapsed = int(time.time() - start_time)
        if elapsed % 15 < 5:  # Print every ~15 seconds
            print(f"  ⏳ Still waiting... ({elapsed}s elapsed)")
        
        time.sleep(5)

    # Step 4: Save session
    print()
    print("=" * 60)
    
    if logged_in:
        print("✅ LOGIN SUCCESSFUL!")
        print()
        print("Verifying session...")
        
        # Final verification
        page.goto("https://broadcastmarketintelligence.substack.com/dashboard", timeout=30000)
        time.sleep(5)
        
        # Take screenshot as proof
        debug_dir = os.path.join(SESSION_DIR, "debug")
        os.makedirs(debug_dir, exist_ok=True)
        page.screenshot(path=os.path.join(debug_dir, "substack_v7_logged_in.png"))
        print(f"  Screenshot saved: {debug_dir}/substack_v7_logged_in.png")
        
        try:
            final_text = page.locator("body").inner_text(timeout=5000)
            if "Create" in final_text:
                print("  ✅ Dashboard confirmed accessible!")
            else:
                print(f"  ⚠️ Dashboard text unclear: {final_text[:100]}")
        except Exception as e:
            print(f"  ⚠️ Could not verify dashboard: {e}")
        
        context.close()
        print()
        print("🎉" + "=" * 58)
        print("  SESSION SAVED! Browser profile stored at:")
        print(f"    {PROFILE_DIR}")
        print()
        print("  You can now run: python substack_poster.py")
        print("=" * 60)
    else:
        print("⏰ TIMEOUT: Login not detected after 15 minutes.")
        print()
        print("Troubleshooting:")
        print("  1. Did you click the Magic Link in your email?")
        print("  2. Did the browser redirect to the dashboard?")
        print("  3. Try running this script again.")
        print()
        context.close()
        sys.exit(1)
