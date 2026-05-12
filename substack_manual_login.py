#!/usr/bin/env python3
"""
Substack Manual Login Helper v3
Opens browser, pauses for manual login, then saves cookies.
"""

import os
import time

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("[Substack] ❌ Playwright not installed. Run: pip install playwright && playwright install chromium")
    exit(1)

# Config
PUB_URL = "https://broadcastmarketintelligence.substack.com"
SESSION_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".browser_sessions")
os.makedirs(SESSION_DIR, exist_ok=True)
STATE_FILE = os.path.join(SESSION_DIR, "state.json")

def main():
    print("=" * 60)
    print("Substack Manual Login Helper v3")
    print("=" * 60)
    print()
    print("[Step 1] Opening browser for MANUAL login...")
    print(f"[Step 2] Please manually login to: {PUB_URL}")
    print("[Step 3] After login is successful, the script will save cookies")
    print()

    with sync_playwright() as p:
        # Use headed mode (show browser window)
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # Navigate to publication sign-in
        print("[Substack] Navigating to publication sign-in page...")
        page.goto(f"{PUB_URL}/publish", timeout=30000, wait_until="networkidle")
        time.sleep(5)

        print()
        print("🌐 Browser window is OPEN!")
        print("Please:")
        print("  1. Manually login (enter email + password)")
        print("  2. Make SURE you can access the publish page")
        print("  3. After successful login, press Enter in THIS terminal")
        print()

        # Use page.pause() to allow manual interaction
        print("[Substack] Pausing for manual login...")
        print("[Substack] After login is complete, close the browser window to continue...")
        print()

        # Wait for browser to be closed (user signals completion)
        print("[Substack] Waiting for you to close the browser window...")
        print("[Substack] (After login is successful, close the browser window)")

        # Monitor if browser is still running
        # When user closes browser, we'll know
        try:
            while True:
                try:
                    # Check if browser is still connected
                    page.title()  # This will fail if browser is closed
                    time.sleep(2)
                except Exception:
                    print("[Substack] Browser closed, continuing...")
                    break
        except KeyboardInterrupt:
            print("[Substack] Interrupted by user")

        print()
        print("[Substack] Saving cookies...")
        context.storage_state(path=STATE_FILE)
        print(f"[Substack] ✅ Cookies saved to: {STATE_FILE}")
        print()
        print("[Substack] ✅ Done! Future automated runs will use these cookies.")
        print(f"[Substack] You can now run: python substack_auto_post.py")

        browser.close()

if __name__ == "__main__":
    main()
