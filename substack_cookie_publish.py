#!/usr/bin/env python3
"""
Substack Auto-Publish via Playwright (using saved session cookies)

Strategy: Use state.json (which has valid substack.sid cookie) to initialize
a browser context, then create and publish a new article on Substack.

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


def merge_state_into_profile():
    """Merge cookies from state.json into the Playwright profile directory.
    
    Playwright's launch_persistent_context uses its own cookie storage in the
    profile directory. We need to ensure the substack.sid cookie is available.
    Instead, we'll use add_cookies() after launching the browser.
    """
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
    
    state = merge_state_into_profile()
    if state is None:
        return False
    
    print("\n[1/5] Launching browser with saved session...")
    
    with sync_playwright() as p:
        # Use a fresh context (NOT persistent) so we can add cookies manually
        browser = p.chromium.launch(
            headless=False,  # Use headed mode for better compatibility
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
            # Step 1: Navigate to publish page to check login status
            print("\n[2/5] Checking login status...")
            page.goto(f"{PUB_URL}/publish", timeout=30000)
            time.sleep(5)
            
            current_url = page.url
            print(f"  Current URL: {current_url}")
            
            if "sign-in" in current_url.lower() or "login" in current_url.lower():
                print("❌ Session expired - redirected to login page!")
                print("  Need to refresh session manually. Run substack_manual_login.py first.")
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
            
            # Verify we're on the editor page
            if "/publish" not in current_url:
                print(f"  ⚠️ Unexpected URL. May not be on editor page.")
            
            # Step 3: Fill in the article content
            print("\n[4/5] Filling editor...")
            
            # Wait for contenteditable elements (Substack uses ProseMirror)
            editor_found = False
            for attempt in range(30):
                try:
                    editable_elements = page.locator('[contenteditable="true"]')
                    count = editable_elements.count()
                    if count >= 2:
                        editor_found = True
                        print(f"  Found {count} contenteditable elements")
                        break
                    elif count == 1:
                        editor_found = True
                        print(f"  Found 1 contenteditable element")
                        break
                except:
                    pass
                time.sleep(1)
                if attempt % 10 == 9:
                    print(f"  Waiting for editor... ({attempt+1}s)")
            
            if not editor_found:
                print("  ❌ Editor not found! Taking screenshot...")
                page.screenshot(path=os.path.join(SESSION_DIR, "debug_no_editor.png"))
                browser.close()
                return False
            
            # Fill title (first contenteditable)
            print("  Setting title...")
            
            # Use JavaScript to directly set the title (handles React state properly)
            page.evaluate("""(title) => {
                // Find the title contenteditable
                const titleEl = document.querySelector('[contenteditable="true"]');
                if (titleEl) {
                    // Focus the element
                    titleEl.focus();
                    // Clear existing content
                    titleEl.innerHTML = '';
                    // Create a text node
                    const textNode = document.createTextNode(title);
                    titleEl.appendChild(textNode);
                    // Trigger input event for React
                    titleEl.dispatchEvent(new InputEvent('input', { bubbles: true }));
                    titleEl.dispatchEvent(new Event('change', { bubbles: true }));
                    // Blur to trigger save
                    titleEl.blur();
                }
                return !!titleEl;
            }""", title)
            time.sleep(2)
            
            # Also try keyboard approach as backup
            title_el = page.locator('[contenteditable="true"]').first
            title_el.click()
            time.sleep(0.5)
            page.keyboard.press("Control+a")
            time.sleep(0.3)
            page.keyboard.type(title, delay=20)
            time.sleep(1)
            
            print(f"  ✅ Title set: {title}")
            
            # Fill body (second contenteditable or continue typing)
            print("  Typing article body...")
            
            # Use JavaScript to set body content directly
            page.evaluate("""(body) => {
                // Find all contenteditable elements
                const editors = document.querySelectorAll('[contenteditable="true"]');
                // Body is usually the 2nd one (index 1) or the one with "Start writing..." placeholder
                let bodyEl = null;
                for (let el of editors) {
                    if (el !== document.activeElement) {
                        // Check if this looks like the body editor
                        const text = el.textContent || el.innerText || '';
                        if (text.includes('Start writing') || text.length === 0 || el.getAttribute('data-placeholder')) {
                            bodyEl = el;
                            break;
                        }
                    }
                }
                // If not found, use the second one
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
            
            # Also try keyboard typing as backup
            page.keyboard.press("Enter")
            page.keyboard.press("Enter")
            time.sleep(0.5)
            
            # Type article in chunks (as backup to ensure content is there)
            chunk_size = 500
            for i in range(0, min(len(article_body), 1000), chunk_size):  # Only type first 1000 chars via keyboard
                chunk = article_body[i:i+chunk_size]
                page.keyboard.type(chunk, delay=5)
                time.sleep(0.2)
            
            print(f"  ✅ Content set ({len(article_body)} chars)")
            time.sleep(3)
            
            page.screenshot(path=os.path.join(SESSION_DIR, "debug_content_filled.png"))
            
            # Step 4: Publish the article
            print("\n[5/5] Publishing...")
            
            # Get the draft ID from the URL
            current_url = page.url
            draft_id = None
            if "/publish/post/" in current_url:
                draft_id = current_url.split("/publish/post/")[-1].split("?")[0]
                print(f"  Draft ID: {draft_id}")
            
            # Step 4a: Click "Continue" button to go to publish options
            print("  Clicking Continue button...")
            continue_clicked = False
            try:
                # Try to find the Continue button (orange button in top right)
                continue_btn = page.locator('button:has-text("Continue"), a:has-text("Continue")')
                if continue_btn.count() > 0:
                    continue_btn.first.click()
                    continue_clicked = True
                    print("  ✅ Clicked Continue")
                else:
                    # Try alternative selectors
                    for sel in ['button[class*="continue" i]', 'button[class*="publish" i]', 'button:has-text("Next")']:
                        try:
                            loc = page.locator(sel)
                            if loc.count() > 0 and loc.first.is_visible(timeout=2000):
                                loc.first.click()
                                continue_clicked = True
                                print(f"  ✅ Clicked alternative: {sel}")
                                break
                        except:
                            continue
            except Exception as e:
                print(f"  Continue button error: {e}")
            
            if not continue_clicked:
                print("  ⚠️ Could not find Continue button")
                page.screenshot(path=os.path.join(SESSION_DIR, "debug_no_continue.png"))
            
            # Wait for publish options page to load
            time.sleep(5)
            page.screenshot(path=os.path.join(SESSION_DIR, "debug_publish_options.png"))
            
            # Step 4b: Click "Send to everyone now" on the publish options page
            published = False
            if continue_clicked:
                print("  Looking for 'Send to everyone now' button...")
                publish_selectors = [
                    'button:has-text("Send to everyone now")',
                    'button:has-text("Send to everyone")',
                    'button:has-text("Publish now")',
                    'button:has-text("Publish")',
                    'div[role="button"]:has-text("Send to everyone")',
                    'button[class*="send" i]',
                    'button[class*="publish" i]',
                ]
                
                for sel in publish_selectors:
                    try:
                        loc = page.locator(sel)
                        if loc.count() > 0 and loc.first.is_visible(timeout=5000):
                            loc.first.click()
                            published = True
                            print(f"  ✅ Clicked publish: {sel}")
                            break
                    except Exception as e:
                        continue
                
                if not published:
                    print("  ⚠️ Could not find publish button. Taking screenshot...")
                    page.screenshot(path=os.path.join(SESSION_DIR, "debug_no_publish_btn.png"))
            
            time.sleep(5)
            
            time.sleep(5)
            page.screenshot(path=os.path.join(SESSION_DIR, "debug_after_publish.png"))
            
            # Save updated state
            context.storage_state(path=os.path.join(SESSION_DIR, "state.json"))
            print("  ✅ Session state saved")
            
            if published:
                print(f"\n✅ Article published to {PUB_URL}")
                print(f"   Title: {title}")
            else:
                print("\n⚠️ Could not auto-publish. Article is in editor as draft.")
                print("   You may need to click Publish manually in the browser.")
            
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
        # Try to find any recent draft
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
