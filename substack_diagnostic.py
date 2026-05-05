"""
Substack Diagnostics: Print all buttons/links on the editor page.
Run this AFTER manually logging in to Substack.
"""
import sys, os, time, json
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from playwright.sync_api import sync_playwright

SESSION_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".browser_sessions")
PROFILE_DIR = os.path.join(SESSION_DIR, "substack_profile")

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        PROFILE_DIR,
        headless=False,
        args=["--disable-blink-features=AutomationControlled"],
        viewport={"width": 1280, "height": 900},
    )
    page = context.pages[0] if context.pages else context.new_page()

    print("Navigating to Substack editor...")
    page.goto("https://substack.com/write", timeout=30000)
    time.sleep(8)

    print("\n" + "="*60)
    print("PAGE INFO:")
    print(f"  URL: {page.url}")
    print(f"  Title: {page.title()}")
    print("="*60)

    # Check for Cloudflare
    for _ in range(10):
        t = page.title()
        if all(x not in t for x in ["Checking", "Just a moment", "Attention", "稍候"]):
            break
        print("  Waiting for Cloudflare...")
        time.sleep(2)

    print("\n[1] All BUTTONS on page:")
    btns = page.evaluate("""() => {
        const buttons = document.querySelectorAll('button, [role="button"], a.btn, a.button');
        return Array.from(buttons).map((b, i) => {
            return {
                index: i,
                tag: b.tagName,
                text: (b.innerText || b.textContent || '').trim().substring(0, 80),
                id: b.id || '',
                cls: b.className || '',
                ariaLabel: b.getAttribute('aria-label') || '',
                dataTestId: b.getAttribute('data-testid') || '',
                visible: b.offsetParent !== null,
            };
        }).filter(b => b.text || b.id || b.ariaLabel);
    }""")
    
    for b in btns:
        print(f"  [{b['index']}] <{b['tag']}> text='{b['text']}' visible={b['visible']}")
        if b['ariaLabel']:
            print(f"       aria-label='{b['ariaLabel']}'")
        if b['dataTestId']:
            print(f"       data-testid='{b['dataTestId']}'")
        if b['id']:
            print(f"       id='{b['id']}'")

    print(f"\n[2] Title input fields:")
    title_fields = page.evaluate("""() => {
        const inputs = document.querySelectorAll('input[placeholder*="title" i], input[placeholder*="Title"], [contenteditable="true"]');
        return Array.from(inputs).map((el, i) => {
            return {
                tag: el.tagName,
                placeholder: el.getAttribute('placeholder') || '',
                ariaLabel: el.getAttribute('aria-label') || '',
                cls: el.className || '',
                text: (el.innerText || el.textContent || el.value || '').substring(0, 60),
            };
        });
    }""")
    for f in title_fields:
        print(f"  <{f['tag']}> placeholder='{f['placeholder']}' aria-label='{f['ariaLabel']}'")
        print(f"    class='{f['cls'][:60]}' text='{f['text']}'")

    print(f"\n[3] All INPUTs with 'title' in placeholder/aria-label:")
    inputs = page.evaluate("""() => {
        const inputs = document.querySelectorAll('input');
        return Array.from(inputs).map(inp => {
            return {
                placeholder: inp.placeholder || '',
                ariaLabel: inp.getAttribute('aria-label') || '',
                value: (inp.value || '').substring(0, 40),
                cls: inp.className || '',
            };
        }).filter(inp => (inp.placeholder || '').toLowerCase().includes('title') || (inp.ariaLabel || '').toLowerCase().includes('title'));
    }""")
    for inp in inputs:
        print(f"  placeholder='{inp['placeholder']}' aria-label='{inp['ariaLabel']}' value='{inp['value']}'")

    print(f"\n[4] ProseMirror editor present: {page.locator('.ProseMirror').count()} instance(s)")
    
    print(f"\n[5] Screenshot saved to debug directory...")
    debug_dir = os.path.join(SESSION_DIR, "debug")
    os.makedirs(debug_dir, exist_ok=True)
    page.screenshot(path=os.path.join(debug_dir, "substack_editor_diagnostic.png"), full_page=True)
    print(f"  Screenshot: {debug_dir}/substack_editor_diagnostic.png")

    print("\n" + "="*60)
    print("DIAGNOSTIC COMPLETE")
    print("="*60)
    print("\nKeep this browser open. Now manually click the PUBLISH button,")
    print("then press Enter in THIS terminal to capture the next page state...")
    input("\nPress Enter after you've clicked Publish (or after the dialog appears)...")

    # After user clicked publish, capture the dialog
    print("\n[6] Buttons AFTER clicking Publish:")
    time.sleep(2)
    btns2 = page.evaluate("""() => {
        const buttons = document.querySelectorAll('button, [role="button"]');
        return Array.from(buttons).map((b, i) => {
            return {
                index: i,
                text: (b.innerText || b.textContent || '').trim().substring(0, 80),
                ariaLabel: b.getAttribute('aria-label') || '',
                dataTestId: b.getAttribute('data-testid') || '',
                visible: b.offsetParent !== null,
            };
        }).filter(b => b.text);
    }""")
    
    for b in btns2:
        print(f"  [{b['index']}] text='{b['text']}' visible={b['visible']}")
        if b['ariaLabel']:
            print(f"       aria-label='{b['ariaLabel']}'")
        if b['dataTestId']:
            print(f"       data-testid='{b['dataTestId']}'")

    page.screenshot(path=os.path.join(debug_dir, "substack_after_publish_click.png"), full_page=True)
    print(f"\n  Screenshot: {debug_dir}/substack_after_publish_click.png")
    
    print("\nNow click 'Send to everyone now' manually, then press Enter...")
    input("Press Enter after you've published the post...")
    
    print(f"\n[7] Final URL: {page.url}")
    page.screenshot(path=os.path.join(debug_dir, "substack_after_publish.png"))
    print(f"  Screenshot: {debug_dir}/substack_after_publish.png")

    context.close()
    print("\nDone. Check the debug screenshots and button info above.")
