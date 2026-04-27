"""
Substack Auto-Login v6 - Magic Link Flow (bypass reCAPTCHA)
Flow: Open substack.com -> Click "Sign in" -> Enter email -> Click magic link button -> Wait for user to click email link
"""
import sys, os, time
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from playwright.sync_api import sync_playwright

SESSION_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".browser_sessions")
PROFILE_DIR = os.path.join(SESSION_DIR, "substack_profile")
os.makedirs(PROFILE_DIR, exist_ok=True)

# Remove lock file if exists (from previous crash)
lockfile = os.path.join(PROFILE_DIR, "SingletonLock")
for lf in [lockfile, lockfile.replace("SingletonLock", "SingletonCookie"), lockfile.replace("SingletonLock", "SingletonSocket")]:
    if os.path.exists(lf):
        try:
            os.remove(lf)
            print(f"Removed lock: {lf}")
        except Exception:
            pass

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
    
    # Bring browser to front
    try:
        page.goto("about:blank")
        time.sleep(0.5)
    except Exception:
        pass

    # Step 1: Check if already logged in via dashboard (not settings - session may be partial)
    print("Checking login status via dashboard...")
    
    # Try publication dashboard first
    page.goto("https://broadcastmarketintelligence.substack.com/dashboard", timeout=30000)
    time.sleep(5)

    # Handle Cloudflare
    for _ in range(15):
        title = page.title()
        if all(x not in title for x in ["稍候", "Checking", "Just a moment", "Attention"]):
            break
        print("  Waiting for Cloudflare...")
        time.sleep(2)

    dash_text = page.locator("body").inner_text(timeout=5000)
    is_logged_in = "Create" in dash_text and "Page not found" not in dash_text and "Discover world class culture" not in dash_text

    if not is_logged_in:
        # Try substack.com/dashboard
        page.goto("https://substack.com/dashboard", timeout=30000)
        time.sleep(5)
        dash_text = page.locator("body").inner_text(timeout=5000)
        is_logged_in = "Create" in dash_text and "Discover world class culture" not in dash_text

    if is_logged_in:
        print("\n✅ ALREADY LOGGED IN! Dashboard accessible.")
        context.close()
        print("Session saved. You can now run: python substack_poster.py")
        sys.exit(0)

    # Step 2: Not logged in - start Magic Link flow
    print("\n🔐 Not logged in. Starting Magic Link flow...")
    print(f"   Email: {EMAIL}")
    print()

    # Navigate to sign-in page
    page.goto("https://substack.com/sign-in", timeout=30000)
    time.sleep(3)

    # Click "Sign in with email" to avoid Google OAuth / reCAPTCHA
    print("Looking for 'Sign in with email' button...")
    email_signin_clicked = False
    
    # Try multiple selectors for the email sign-in option
    email_signin_selectors = [
        'a:has-text("Sign in with email")',
        'button:has-text("Sign in with email")',
        'a:has-text("Sign in with Email")',
        '[data-testid="sign-in-with-email"]',
        'a[href*="email"]',
    ]
    
    for sel in email_signin_selectors:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=3000):
                el.click()
                email_signin_clicked = True
                print(f"  ✅ Clicked: {sel}")
                time.sleep(2)
                break
        except Exception:
            continue

    if not email_signin_clicked:
        # Maybe we're already on the email input page
        print("  Direct email input page or different layout...")
        time.sleep(2)

    # Fill email address
    print("Filling email address...")
    email_filled = False
    email_selectors = [
        'input[name="email"]',
        'input[type="email"]',
        'input[placeholder*="email"]',
        'input[placeholder*="Email"]',
        'input[id="email"]',
    ]
    
    for sel in email_selectors:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=3000):
                el.click()
                time.sleep(0.3)
                el.fill("")
                page.keyboard.type(EMAIL, delay=30)
                email_filled = True
                print(f"  ✅ Email filled via: {sel}")
                break
        except Exception:
            continue

    if not email_filled:
        # Take screenshot for debug
        debug_dir = os.path.join(SESSION_DIR, "debug")
        os.makedirs(debug_dir, exist_ok=True)
        page.screenshot(path=os.path.join(debug_dir, "substack_v6_email_page.png"))
        print("  ❌ Could not find email input! Screenshot saved.")
        print("  Please fill email manually in the browser.")
        # Don't close - let user do it manually
        input("Press Enter after you've filled the email and submitted...")
        email_filled = True

    # Click "Continue" or "Send magic link" button
    print("Looking for Continue/Send button...")
    button_clicked = False
    btn_selectors = [
        'button:has-text("Continue")',
        'button:has-text("Send")',
        'button:has-text("Sign in")',
        'button[type="submit"]',
        'button:has-text("Next")',
        'input[type="submit"]',
    ]
    
    for sel in btn_selectors:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=2000):
                el.click()
                button_clicked = True
                print(f"  ✅ Clicked: {sel}")
                time.sleep(2)
                break
        except Exception:
            continue

    if not button_clicked:
        # Maybe need to press Enter
        print("  Trying Enter key...")
        page.keyboard.press("Enter")
        time.sleep(2)

    # Step 3: Wait for "Check your email" confirmation
    print("\n📧 Waiting for magic link confirmation page...")
    time.sleep(3)
    
    page_text = page.locator("body").inner_text(timeout=5000)
    if "Check your email" in page_text or "check your email" in page_text or "magic link" in page_text.lower():
        print("✅ Magic link email sent!")
        print()
        print("=" * 50)
        print("  📬 CHECK YOUR EMAIL NOW!")
        print(f"     Email: {EMAIL}")
        print("     Click the login link in the email.")
        print("=" * 50)
        print()
    else:
        print(f"  Page text: {page_text[:200]}")
        print("  If you see a different page, follow the instructions.")
        print()

    # Step 4: Poll until login is detected (max 10 minutes)
    print("Auto-detecting login... (click the email link)")
    print("⏳ Waiting up to 10 minutes...")

    for check in range(300):  # 300 * 2s = 10 minutes
        time.sleep(2)
        try:
            current_url = page.url
            # If redirected away from sign-in pages, check dashboard
            if "/sign-in" not in current_url and "/signin" not in current_url and "/email-login" not in current_url:
                # Check dashboard instead of settings (more reliable)
                page.goto("https://substack.com/dashboard", timeout=15000)
                time.sleep(3)
                check_text = page.locator("body").inner_text(timeout=3000)
                if "Create" in check_text and "Discover world class culture" not in check_text:
                    print(f"\n✅ LOGIN DETECTED after {check*2}s!")
                    break
            if check % 15 == 0 and check > 0:
                print(f"  Still waiting... ({check*2}s)")
        except Exception:
            pass
    else:
        print("\n⏰ TIMEOUT: Login not detected after 10 minutes.")
        context.close()
        sys.exit(1)

    # Step 5: Verify dashboard access
    print("\nVerifying publication access...")
    page.goto("https://broadcastmarketintelligence.substack.com/dashboard", timeout=30000)
    time.sleep(5)

    # Take screenshot
    debug_dir = os.path.join(SESSION_DIR, "debug")
    os.makedirs(debug_dir, exist_ok=True)
    page.screenshot(path=os.path.join(debug_dir, "substack_v6_dashboard.png"))

    dash_text = page.locator("body").inner_text(timeout=5000)
    if "Create" in dash_text and "Page not found" not in dash_text:
        print("✅ Publication dashboard accessible!")
    elif "Page not found" in dash_text:
        print("⚠️ Publication dashboard shows 'Page not found'")
        page.goto("https://substack.com/dashboard", timeout=30000)
        time.sleep(3)
        dash2 = page.locator("body").inner_text(timeout=5000)
        if "Create" in dash2:
            print("✅ Dashboard found on substack.com/dashboard")
    else:
        print(f"  Dashboard status unclear: {dash_text[:200]}")

    context.close()
    print("\n🎉 Session saved! You can now run: python substack_poster.py")
