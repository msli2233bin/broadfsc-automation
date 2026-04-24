"""Quick debug script to inspect Medium and Substack editor pages."""
import os
import sys
import time
import json

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


def debug_page(page, name, step):
    """Save URL, title, screenshot, and HTML content for debugging."""
    print(f"  [{name}] Step {step} URL: {page.url}")
    print(f"  [{name}] Step {step} Title: {page.title()}")
    page.screenshot(path=os.path.join(DEBUG_DIR, f"{name}_step{step}.png"))
    # Save first 5000 chars of HTML
    html = page.content()
    with open(os.path.join(DEBUG_DIR, f"{name}_step{step}.html"), "w", encoding="utf-8") as f:
        f.write(html[:5000])
    print(f"  [{name}] Step {step} HTML length: {len(html)}")


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=300)
    context = browser.new_context(
        viewport={"width": 1280, "height": 900},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    )

    # Load Medium session
    medium_session = os.path.join(SESSION_DIR, "medium_session.json")
    if os.path.exists(medium_session):
        context.add_cookies(json.loads(open(medium_session, "r").read()))
        print("Loaded Medium session")

    # --- MEDIUM ---
    print("\n=== MEDIUM DEBUG ===")
    page = context.new_page()
    
    print("  Navigating to medium.com/new-story...")
    page.goto("https://medium.com/new-story", timeout=60000)
    time.sleep(3)
    debug_page(page, "medium", 1)

    # Wait longer and try again
    print("  Waiting 10 seconds for editor to load...")
    time.sleep(10)
    debug_page(page, "medium", 2)

    # Try finding contenteditable elements
    editables = page.locator('[contenteditable="true"]')
    print(f"  contenteditable elements found: {editables.count()}")
    
    # Try all editable elements
    all_editables = page.locator('[contenteditable]')
    print(f"  All contenteditable elements: {all_editables.count()}")

    # Try textareas
    textareas = page.locator('textarea')
    print(f"  textarea elements: {textareas.count()}")

    # Try inputs
    inputs = page.locator('input')
    print(f"  input elements: {inputs.count()}")

    # Check page for any iframe
    iframes = page.frames
    print(f"  Frames: {len(iframes)}")
    for i, frame in enumerate(iframes):
        print(f"    Frame {i}: {frame.url}")
        try:
            frame_editables = frame.locator('[contenteditable="true"]')
            print(f"    Frame {i} contenteditable: {frame_editables.count()}")
        except Exception:
            pass

    # --- SUBSTACK ---
    print("\n=== SUBSTACK DEBUG ===")
    
    # Load Substack session  
    substack_session = os.path.join(SESSION_DIR, "substack_session.json")
    if os.path.exists(substack_session):
        try:
            context.add_cookies(json.loads(open(substack_session, "r").read()))
            print("Loaded Substack session")
        except Exception:
            pass

    page2 = context.new_page()
    
    print("  Navigating to broadcasts.substack.com/drafts/new...")
    page2.goto("https://broadcasts.substack.com/drafts/new", timeout=60000)
    time.sleep(3)
    debug_page(page2, "substack", 1)

    # Wait longer
    print("  Waiting 10 seconds for editor to load...")
    time.sleep(10)
    debug_page(page2, "substack", 2)

    # Try finding contenteditable elements
    editables2 = page2.locator('[contenteditable="true"]')
    print(f"  contenteditable elements found: {editables2.count()}")

    all_editables2 = page2.locator('[contenteditable]')
    print(f"  All contenteditable elements: {all_editables2.count()}")

    textareas2 = page2.locator('textarea')
    print(f"  textarea elements: {textareas2.count()}")

    inputs2 = page2.locator('input')
    print(f"  input elements: {inputs2.count()}")

    iframes2 = page2.frames
    print(f"  Frames: {len(iframes2)}")
    for i, frame in enumerate(iframes2):
        print(f"    Frame {i}: {frame.url}")
        try:
            frame_editables = frame.locator('[contenteditable="true"]')
            print(f"    Frame {i} contenteditable: {frame_editables.count()}")
        except Exception:
            pass

    print("\nDebug complete. Check .browser_sessions/debug/ for screenshots and HTML.")
    input("Press Enter to close browser...")
    browser.close()
