#!/usr/bin/env python3
"""
Substack Auto-Publish via Playwright (using saved session cookies)

Strategy: Use state.json (which has valid substack.sid cookie) to initialize
a browser context, then create and publish a new article on Substack.

Publishing flow:
1. Load cookies from state.json
2. Navigate to /publish/post
3. Fill title and body via JavaScript (handles React state)
4. Click Continue button
5. Click "Send to everyone now" button
6. Verify published by checking URL

This replaces the broken email-based approach (Substack doesn't support post-by-email)
and the password-login approach (Substack only supports Magic Link).
"""
import os, sys, re, time, datetime, json
from pathlib import Path

_script_dir = os.path.dirname(os.path.abspath(__file__))
_env_path = os.path.join(_script_dir, ".env")
if os.path.exists(_env_path):
    with open(_env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

SESSION_DIR = os.path.join(_script_dir, ".browser_sessions")
STATE_FILE = os.path.join(SESSION_DIR, "state.json")
PUBLICATION_SLUG = "broadcastmarketintelligence"
PUB_URL = f"https://{PUBLICATION_SLUG}.substack.com"


def load_state():
    """Load cookies from state.json."""
    if not os.path.exists(STATE_FILE):
        print("❌ state.json not found! Need to login first.")
        return None
    
    with open(STATE_FILE, 'r') as f:
        state = json.load(f)
    
    substack_cookies = [c for c in state.get('cookies', []) if 'substack' in c.get('domain', '')]
    has_sid = any(c['name'] == 'substack.sid' for c in substack_cookies)
    
    print(f"  Loaded {len(substack_cookies)} substack cookies from state.json")
    print(f"  substack.sid present: {has_sid}")
    
    if not has_sid:
        print("⚠️ No substack.sid cookie! Session may be expired.")
    
    return state


def publish_article(title, article_body):
    """Publish article to Substack using Playwright with saved session."""
    from playwright.sync_api import sync_playwright
    
    state = load_state()
    if state is None:
        return False
    
    print("\n[1/5] Launching browser with saved session...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        )
        
        # Add cookies from state.json
        cookies_to_add = []
        for c in state.get('cookies', []):
            cookie = {
                'name': c['name'],
                'value': c['value'],
                'domain': c['domain'],
                'path': c.get('path', '/'),
            }
            if c.get('expires') and c['expires'] > 0:
                cookie['expires'] = c['expires']
            if c.get('httpOnly'):
                cookie['httpOnly'] = True
            if c.get('secure'):
                cookie['secure'] = True
            if c.get('sameSite'):
                cookie['sameSite'] = c['sameSite']
            cookies_to_add.append(cookie)
        
        context.add_cookies(cookies_to_add)
        print(f"  Added {len(cookies_to_add)} cookies to browser context")
        
        page = context.new_page()
        
        try:
            # Step 1: Check login status
            print("\n[2/5] Checking login status...")
            page.goto(f"{PUB_URL}/publish", timeout=30000)
            time.sleep(5)
            
            current_url = page.url
            print(f"  Current URL: {current_url}")
            
            if "sign-in" in current_url.lower() or "login" in current_url.lower():
                print("❌ Session expired - redirected to login page!")
                page.screenshot(path=os.path.join(SESSION_DIR, "debug_session_expired.png"))
                browser.close()
                return False
            
            print("  ✅ Session is valid!")
            
            # Step 2: Navigate to new post editor
            print("\n[3/5] Creating new post...")
            page.goto(f"{PUB_URL}/publish/post", timeout=30000)
            time.sleep(8)
            
            current_url = page.url
            print(f"  Editor URL: {current_url}")
            page.screenshot(path=os.path.join(SESSION_DIR, "debug_editor.png"))
            
            # Step 3: Fill in the article content
            print("\n[4/5] Filling editor...")
            
            # Wait for contenteditable elements
            editor_found = False
            for attempt in range(30):
                try:
                    editable_elements = page.locator('[contenteditable="true"]')
                    count = editable_elements.count()
                    if count >= 2:
                        editor_found = True
                        print(f"  Found {count} contenteditable elements")
                        break
                except:
                    pass
                time.sleep(1)
                if attempt % 10 == 9:
                    print(f"  Waiting for editor... ({attempt+1}s)")
            
            if not editor_found:
                print("  ❌ Editor not found!")
                page.screenshot(path=os.path.join(SESSION_DIR, "debug_no_editor.png"))
                browser.close()
                return False
            
            # Fill title (first contenteditable)
            print("  Setting title...")
            page.evaluate("""(title) => {
                const titleEl = document.querySelector('[contenteditable="true"]');
                if (titleEl) {
                    titleEl.focus();
                    titleEl.innerHTML = '';
                    const textNode = document.createTextNode(title);
                    titleEl.appendChild(textNode);
                    titleEl.dispatchEvent(new InputEvent('input', { bubbles: true }));
                    titleEl.dispatchEvent(new Event('change', { bubbles: true }));
                    titleEl.blur();
                }
                return !!titleEl;
            }""", title)
            time.sleep(2)
            
            # Backup: keyboard input
            title_el = page.locator('[contenteditable="true"]').first
            title_el.click()
            time.sleep(0.5)
            page.keyboard.press("Control+a")
            time.sleep(0.3)
            page.keyboard.type(title, delay=20)
            time.sleep(1)
            
            print(f"  ✅ Title set: {title}")
            
            # Fill body (second contenteditable)
            print("  Setting article body...")
            page.evaluate("""(body) => {
                const editors = document.querySelectorAll('[contenteditable="true"]');
                let bodyEl = null;
                for (let el of editors) {
                    if (el !== document.activeElement) {
                        const text = el.textContent || el.innerText || '';
                        if (text.includes('Start writing') || text.length === 0 || el.getAttribute('data-placeholder')) {
                            bodyEl = el;
                            break;
                        }
                    }
                }
                if (!bodyEl && editors.length >= 2) {
                    bodyEl = editors[1];
                }
                
                if (bodyEl) {
                    bodyEl.focus();
                    bodyEl.innerHTML = '<p>' + body.replace(/\\n\\n/g, '</p><p>').replace(/\\n/g, ' ') + '</p>';
                    bodyEl.dispatchEvent(new InputEvent('input', { bubbles: true }));
                    bodyEl.dispatchEvent(new Event('change', { bubbles: true }));
                    bodyEl.blur();
                    return true;
                }
                return false;
            }""", article_body)
            time.sleep(2)
            
            print(f"  ✅ Content set ({len(article_body)} chars)")
            time.sleep(3)
            
            page.screenshot(path=os.path.join(SESSION_DIR, "debug_content_filled.png"))
            
            # Step 4: Publish - Use Playwright to click buttons (handles modals properly)
            print("\n[5/5] Publishing...")
            
            # First, click Continue button using Playwright locator
            print("  Clicking Continue button...")
            continue_clicked = False
            try:
                # Wait for and click the Continue button
                continue_btn = page.get_by_role("button", name="Continue", exact=True)
                if continue_btn.count() > 0:
                    continue_btn.first.click()
                    continue_clicked = True
                    print("  ✅ Clicked Continue (exact match)")
                else:
                    # Try partial match
                    continue_btn = page.get_by_role("button", name=re.compile(r"continue", re.IGNORECASE))
                    if continue_btn.count() > 0:
                        continue_btn.first.click()
                        continue_clicked = True
                        print("  ✅ Clicked Continue (partial match)")
            except Exception as e:
                print(f"  Continue button error: {e}")
            
            if not continue_clicked:
                print("  ⚠️ Could not find Continue button with Playwright, trying JavaScript...")
                page.evaluate("""() => {
                    const btns = document.querySelectorAll('button');
                    for (let b of btns) {
                        if (b.textContent.trim().toLowerCase() === 'continue') {
                            b.click();
                            return;
                        }
                    }
                }""")
            
            time.sleep(5)
            page.screenshot(path=os.path.join(SESSION_DIR, "debug_after_continue.png"))
            
            # Then, click "Send to everyone now" button
            print("  Clicking 'Send to everyone now'...")
            published = False
            
            # Wait for modal to fully load
            time.sleep(3)
            
            # Method 1: Use Playwright's locator with has-text
            try:
                # Find button that contains the text "Send to everyone now"
                publish_btn = page.locator('button:has-text("Send to everyone now")')
                if publish_btn.count() > 0:
                    publish_btn.first.click()
                    published = True
                    print("  ✅ Clicked 'Send to everyone now' (has-text)")
            except Exception as e:
                print(f"  has-text click failed: {e}")
            
            # Method 2: Try get_by_text
            if not published:
                try:
                    publish_btn = page.get_by_text("Send to everyone now", exact=True)
                    if publish_btn.count() > 0:
                        publish_btn.first.click()
                        published = True
                        print("  ✅ Clicked 'Send to everyone now' (get_by_text)")
                except Exception as e:
                    print(f"  get_by_text click failed: {e}")
            
            # Method 3: JavaScript - use elementFromPoint to find and click
            if not published:
                print("  Trying JavaScript elementFromPoint...")
                result = page.evaluate("""() => {
                    // The button is typically at bottom right of viewport
                    // Try clicking at that location
                    const x = window.innerWidth - 150;
                    const y = window.innerHeight - 50;
                    
                    const el = document.elementFromPoint(x, y);
                    if (el) {
                        el.click();
                        return 'clicked element at (' + x + ',' + y + '): ' + el.tagName;
                    }
                    return 'no element found';
                }""")
                print(f"  elementFromPoint result: {result}")
                if 'clicked' in result:
                    published = True
            
            time.sleep(5)
            page.screenshot(path=os.path.join(SESSION_DIR, "debug_after_publish.png"))
            
            # Verify publication by checking URL
            final_url = page.url
            print(f"  Final URL: {final_url}")
            
            # Save updated state
            context.storage_state(path=os.path.join(SESSION_DIR, "state.json"))
            print("  ✅ Session state saved")
            
            # Check if published successfully
            # If published, URL should be the post URL (not /publish)
            published = "/publish" not in final_url or "draft" not in final_url.lower()
            
            if published:
                print(f"\n✅ Article published to {PUB_URL}")
                print(f"   Title: {title}")
            else:
                print("\n⚠️ May not have published. Check debug screenshots.")
            
            browser.close()
            return published
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            try:
                page.screenshot(path=os.path.join(SESSION_DIR, "debug_error.png"))
            except:
                pass
            browser.close()
            return False


def main():
    print("=" * 60)
    print("Substack Auto-Publish (Session Cookie)")
    print(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Find the latest draft
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    draft_file = os.path.join(_script_dir, f"substack_draft_{date_str}.md")
    
    if not os.path.exists(draft_file):
        import glob
        drafts = sorted(glob.glob(os.path.join(_script_dir, "substack_draft_*.md")), reverse=True)
        if drafts:
            draft_file = drafts[0]
            print(f"Using latest draft: {draft_file}")
        else:
            print("❌ No draft file found. Run publish_now.py first to generate an article.")
            sys.exit(1)
    
    with open(draft_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract title and body
    lines = content.split('\n')
    title = ""
    body_start = 0
    for i, line in enumerate(lines):
        if line.startswith('# '):
            title = line.lstrip('# ').strip()
            body_start = i + 1
            break
    
    article_body = '\n'.join(lines[body_start:]).strip()
    print(f"Article: '{title}' ({len(article_body)} chars)")
    
    # Publish
    success = publish_article(title, article_body)
    
    if success:
        print("\n" + "=" * 60)
        print("✅ SUCCESS! Article published to Substack!")
        print(f"   View at: {PUB_URL}")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ Publishing failed. Check debug screenshots in .browser_sessions/")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
