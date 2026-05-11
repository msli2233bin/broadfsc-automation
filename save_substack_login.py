#!/usr/bin/env python3
"""
Save Substack login state for GitHub Actions automation.
Run this once to login and save cookies.
Will auto-save after 90 seconds.
"""

from playwright.sync_api import sync_playwright
import os
import time

def main():
    print("=" * 60)
    print("Substack Login State Saver")
    print("=" * 60)
    print("\nThis will open a browser window.")
    print("Please login to Substack manually within 90 seconds.")
    print("Cookies will be saved automatically after 90 seconds.\n")

    # Create browser_sessions directory
    os.makedirs('.browser_sessions', exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print("Opening Substack login page...")
        page.goto('https://broadcastmarketintelligence.substack.com/publish')

        print("\n" + "=" * 60)
        print("WAITING 90 SECONDS FOR YOU TO LOGIN...")
        print("After successful login, cookies will be saved automatically.")
        print("=" * 60)

        # Wait 90 seconds for manual login
        for i in range(90, 0, -1):
            print(f"Time remaining: {i} seconds...", end='\r')
            time.sleep(1)

        print("\n\nSaving cookies now...")

        # Save cookies
        context.storage_state(path='.browser_sessions/substack_state.json')
        print("✅ Cookies saved to .browser_sessions/substack_state.json")

        browser.close()

    print("\n" + "=" * 60)
    print("Done! You can now commit this file to Git:")
    print("  git add .browser_sessions/")
    print("  git commit -m 'Save Substack login state'")
    print("  git push origin main")
    print("=" * 60)

if __name__ == "__main__":
    main()
