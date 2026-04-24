"""
First-time login script for Medium and Substack.
Run this ONCE manually to log in and save browser state.
After this, medium_substack_poster.py will use the saved state automatically.

Usage:
  python first_login.py

You will see browser windows open. Complete the login process manually.
The script will save the state when you're done.
"""
import os
import sys
import time

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright

SESSION_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".browser_sessions")
DEBUG_DIR = os.path.join(SESSION_DIR, "debug")
os.makedirs(DEBUG_DIR, exist_ok=True)

MEDIUM_EMAIL = os.environ.get("MEDIUM_EMAIL", "msli2233bin@gmail.com")
MEDIUM_PASSWORD = os.environ.get("MEDIUM_PASSWORD", "Lin2233509.")
SUBSTACK_EMAIL = os.environ.get("SUBSTACK_EMAIL", "msli2233bin@gmail.com")
SUBSTACK_PASSWORD = os.environ.get("SUBSTACK_PASSWORD", "Lin2233509.")


def medium_login():
    """Open Medium login page and wait for user to complete login manually."""
    from playwright.sync_api import sync_playwright

    user_data_dir = os.path.join(SESSION_DIR, "medium_profile")
    os.makedirs(user_data_dir, exist_ok=True)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            viewport={"width": 1280, "height": 900},
        )

        page = context.new_page()

        print("\n" + "=" * 60)
        print("MEDIUM LOGIN")
        print("=" * 60)
        print(f"Email: {MEDIUM_EMAIL or '(not set — enter manually)'}")
        print(f"Password: {'***' if MEDIUM_PASSWORD else '(not set — enter manually)'}")
        print()
        print("A browser window will open to Medium's login page.")
        print("Please log in manually (Google, email, or any method).")
        print("The script will detect when you're logged in.")
        print("=" * 60)

        page.goto("https://medium.com/m/signin", timeout=60000)
        time.sleep(3)

        # Try auto-fill if credentials are available
        if MEDIUM_EMAIL:
            try:
                print("Trying to find email input...")
                # Medium login flow varies — try different approaches
                # 1. Look for Google sign-in button
                google_btn = page.locator('button:has-text("Google"), a:has-text("Google")').first
                if google_btn.is_visible(timeout=3000):
                    print("Found Google sign-in button. Clicking...")
                    google_btn.click()
                    time.sleep(3)
                    # Google OAuth
                    try:
                        email_input = page.locator('input[type="email"], input[name="identifier"]').first
                        if email_input.is_visible(timeout=5000):
                            email_input.fill(MEDIUM_EMAIL)
                            time.sleep(0.5)
                            page.locator('button:has-text("Next"), #identifierNext').first.click()
                            time.sleep(3)
                            if MEDIUM_PASSWORD:
                                pwd_input = page.locator('input[type="password"], input[name="password"]').first
                                pwd_input.fill(MEDIUM_PASSWORD)
                                time.sleep(0.5)
                                page.locator('button:has-text("Next"), #passwordNext').first.click()
                                time.sleep(5)
                    except Exception as e:
                        print(f"Auto-fill encountered issue: {e}")
                        print("Please complete login manually.")
            except Exception:
                pass

        # Wait for user to complete login
        print("\nWaiting for you to complete login...")
        print("Once you see your Medium dashboard/editor, login is complete.")
        print()

        for i in range(120):  # 4 minutes max
            time.sleep(2)
            current_url = page.url
            title = page.title()

            # Check if logged in (URL changed away from signin page)
            if "medium.com" in current_url and "signin" not in current_url and "login" not in current_url:
                # Verify by trying to access new-story
                page.goto("https://medium.com/new-story", timeout=30000)
                time.sleep(5)
                title = page.title()

                if "稍候" not in title and "Checking" not in title:
                    # Check for editor elements
                    editables = page.locator('[contenteditable="true"]')
                    if editables.count() > 0:
                        print(f"\n✅ Medium login SUCCESS! (Editor loaded)")
                        page.screenshot(path=os.path.join(DEBUG_DIR, "medium_login_success.png"))
                        context.close()
                        return True

            if i % 15 == 0 and i > 0:
                print(f"  Still waiting... ({i*2}s) Current URL: {current_url}")

        print("\n⚠️ Medium login timed out. You can try again.")
        page.screenshot(path=os.path.join(DEBUG_DIR, "medium_login_timeout.png"))
        context.close()
        return False


def substack_login():
    """Open Substack login page and wait for user to complete login manually."""
    from playwright.sync_api import sync_playwright

    user_data_dir = os.path.join(SESSION_DIR, "substack_profile")
    os.makedirs(user_data_dir, exist_ok=True)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            viewport={"width": 1280, "height": 900},
        )

        page = context.new_page()

        print("\n" + "=" * 60)
        print("SUBSTACK LOGIN")
        print("=" * 60)
        print(f"Email: {SUBSTACK_EMAIL or '(not set — enter manually)'}")
        print(f"Password: {'***' if SUBSTACK_PASSWORD else '(not set — enter manually)'}")
        print()
        print("A browser window will open to Substack's login page.")
        print("Please log in manually (Google, email, or any method).")
        print("The script will detect when you're logged in.")
        print("=" * 60)

        page.goto("https://substack.com/sign-in", timeout=60000)
        time.sleep(3)

        # Try auto-fill if credentials are available
        if SUBSTACK_EMAIL:
            try:
                print("Trying to find sign-in option...")
                # Try Google sign-in
                google_btn = page.locator('button:has-text("Google"), a:has-text("Google")').first
                if google_btn.is_visible(timeout=3000):
                    print("Found Google sign-in button. Clicking...")
                    google_btn.click()
                    time.sleep(3)
                    try:
                        email_input = page.locator('input[type="email"], input[name="identifier"]').first
                        if email_input.is_visible(timeout=5000):
                            email_input.fill(SUBSTACK_EMAIL)
                            time.sleep(0.5)
                            page.locator('button:has-text("Next"), #identifierNext').first.click()
                            time.sleep(3)
                            if SUBSTACK_PASSWORD:
                                pwd_input = page.locator('input[type="password"], input[name="password"]').first
                                pwd_input.fill(SUBSTACK_PASSWORD)
                                time.sleep(0.5)
                                page.locator('button:has-text("Next"), #passwordNext').first.click()
                                time.sleep(5)
                    except Exception as e:
                        print(f"Auto-fill encountered issue: {e}")
                        print("Please complete login manually.")
            except Exception:
                pass

        # Wait for user to complete login
        print("\nWaiting for you to complete login...")
        print("Once you see your Substack Dashboard, login is complete.")
        print()

        for i in range(120):  # 4 minutes max
            time.sleep(2)
            current_url = page.url

            # Check if logged in
            if "substack.com" in current_url and "sign-in" not in current_url and "login" not in current_url:
                # Try to access dashboard
                page.goto("https://broadcasts.substack.com/dashboard", timeout=30000)
                time.sleep(5)

                title = page.title()
                if "Not Found" not in title and "Sign in" not in title:
                    # Try to find new post button or editor
                    new_post = page.locator('a:has-text("New post"), button:has-text("New post"), a:has-text("Write")')
                    if new_post.count() > 0:
                        print(f"\n✅ Substack login SUCCESS! (Dashboard loaded)")
                        page.screenshot(path=os.path.join(DEBUG_DIR, "substack_login_success.png"))
                        context.close()
                        return True

            if i % 15 == 0 and i > 0:
                print(f"  Still waiting... ({i*2}s) Current URL: {current_url}")

        print("\n⚠️ Substack login timed out. You can try again.")
        page.screenshot(path=os.path.join(DEBUG_DIR, "substack_login_timeout.png"))
        context.close()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("BroadFSC — First-Time Login Setup")
    print("=" * 60)
    print()
    print("This script will open browser windows for Medium and Substack.")
    print("Complete the login process in each window.")
    print("The saved state will be used for automatic posting later.")
    print()

    # Medium
    medium_ok = medium_login()

    # Substack
    substack_ok = substack_login()

    print("\n" + "=" * 60)
    print("SETUP SUMMARY")
    print("=" * 60)
    print(f"  Medium:   {'✅ Logged in' if medium_ok else '❌ Failed'}")
    print(f"  Substack: {'✅ Logged in' if substack_ok else '❌ Failed'}")
    print()

    if medium_ok and substack_ok:
        print("🎉 All set! You can now run medium_substack_poster.py for automatic posting.")
    else:
        print("⚠️ Some logins failed. Run this script again to retry.")
