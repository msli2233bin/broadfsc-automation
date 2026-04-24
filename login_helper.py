"""
Interactive login helper — opens browser and WAITS for you.
Run: python login_helper.py
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


def login_medium():
    user_data_dir = os.path.join(SESSION_DIR, "medium_profile")
    os.makedirs(user_data_dir, exist_ok=True)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir, headless=False,
            viewport={"width": 1280, "height": 900},
        )
        page = context.new_page()

        print("\n" + "=" * 60)
        print("STEP 1: Medium Login")
        print("=" * 60)
        print("Browser window opened. Please:")
        print("1. Log in to Medium (Google or email)")
        print("2. Navigate to https://medium.com/new-story")
        print("3. Confirm you can see the editor")
        print("4. Come back here and press Enter")
        print("=" * 60)

        page.goto("https://medium.com/m/signin", timeout=60000)

        # Wait for user to press Enter
        input("\n>>> Press Enter when you've logged in and see the Medium editor <<<")

        # Save screenshot
        page.screenshot(path=os.path.join(DEBUG_DIR, "medium_manual_login.png"))
        print(f"Current URL: {page.url}")
        print(f"Page title: {page.title()}")

        context.close()
        print("✅ Medium session saved!")
        return True


def login_substack():
    user_data_dir = os.path.join(SESSION_DIR, "substack_profile")
    os.makedirs(user_data_dir, exist_ok=True)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir, headless=False,
            viewport={"width": 1280, "height": 900},
        )
        page = context.new_page()

        print("\n" + "=" * 60)
        print("STEP 2: Substack Login")
        print("=" * 60)
        print("Browser window opened. Please:")
        print("1. Log in to Substack (Google or email)")
        print("2. Navigate to your Substack Dashboard")
        print("3. Confirm you can see the dashboard")
        print("4. Come back here and press Enter")
        print("=" * 60)

        page.goto("https://substack.com/sign-in", timeout=60000)

        # Wait for user to press Enter
        input("\n>>> Press Enter when you've logged in and see the Substack dashboard <<<")

        # Save screenshot
        page.screenshot(path=os.path.join(DEBUG_DIR, "substack_manual_login.png"))
        print(f"Current URL: {page.url}")
        print(f"Page title: {page.title()}")

        context.close()
        print("✅ Substack session saved!")
        return True


if __name__ == "__main__":
    print("=" * 60)
    print("BroadFSC — Interactive Login Helper")
    print("=" * 60)
    print()
    print("This script opens browser windows for you to log in manually.")
    print("After logging in, the session is saved for automatic posting.")
    print()

    medium_ok = login_medium()
    substack_ok = login_substack()

    print("\n" + "=" * 60)
    print("DONE!")
    print(f"  Medium:   {'✅' if medium_ok else '❌'}")
    print(f"  Substack: {'✅' if substack_ok else '❌'}")
    if medium_ok and substack_ok:
        print("\nYou can now run: python medium_substack_poster.py")
    print("=" * 60)
