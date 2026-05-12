#!/usr/bin/env python3
"""
Substack Auto-Publish via Playwright (launch_persistent_context)

Uses launch_persistent_context which loads the full browser profile
(cookies, localStorage, sessionStorage, IndexedDB) — required for
Substack's React-based auth. The old browser.new_context + add_cookies
approach fails because it only provides HTTP cookies.

First imports cookies from state.json into the profile, then launches
persistent context browser for publishing.

Based on the May 8 working version (commit 26ab468) and verified by
test_publish_persistent.py.
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
PROFILE_DIR = os.path.join(SESSION_DIR, "substack_profile")
DEBUG_DIR = os.path.join(SESSION_DIR, "debug")
PUBLICATION_SLUG = "broadcastmarketintelligence"
PUB_URL = "https://{}.substack.com".format(PUBLICATION_SLUG)

os.makedirs(PROFILE_DIR, exist_ok=True)
os.makedirs(DEBUG_DIR, exist_ok=True)


def import_cookies_to_profile():
    """Import valid cookies from state.json into the persistent profile.
    This step ensures the profile has the latest session cookies."""
    from playwright.sync_api import sync_playwright

    if not os.path.exists(STATE_FILE):
        print("  No state.json found, skipping cookie import")
        return False

    with open(STATE_FILE, 'r') as f:
        state = json.load(f)

    substack_cookies = [c for c in state.get('cookies', []) if 'substack' in c.get('domain', '')]
    has_sid = any(c['name'] == 'substack.sid' for c in substack_cookies)
    print("  Found {} substack cookies in state.json (sid: {})".format(len(substack_cookies), has_sid))

    if not has_sid:
        print("  WARNING: No substack.sid cookie! Session may be expired.")

    # Use a temporary persistent context to import cookies into the profile
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            PROFILE_DIR,
            headless=True,
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        )

        cookies_to_add = []
        for c in substack_cookies:
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
        print("  Imported {} cookies into profile".format(len(cookies_to_add)))

        # Save updated state
        context.storage_state(path=STATE_FILE)
        context.close()

    return True


def publish_article(title, article_body):
    """Publish article to Substack using launch_persistent_context (same as May 8 working version)."""
    from playwright.sync_api import sync_playwright

    # Step 1: Import cookies into profile
    print("\n[1/6] Importing cookies into browser profile...")
    import_cookies_to_profile()

    # Step 2: Launch persistent context browser
    print("\n[2/6] Launching persistent context browser...")
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            PROFILE_DIR,
            headless=False,
            slow_mo=100,
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
        )

        page = context.new_page()

        try:
            # Step 3: Check login status
            print("\n[3/6] Checking login status...")
            page.goto("https://substack.com/settings", timeout=60000)
            time.sleep(5)

            # Handle Cloudflare
            for wait in range(30):
                page_title = page.title()
                if all(x not in page_title for x in ["Checking", "Just a moment", "Attention"]):
                    break
                time.sleep(2)

            current_url = page.url
            print("  Current URL: {}".format(current_url))

            if "sign-in" in current_url.lower():
                print("  Session expired - redirected to login!")
                page.screenshot(path=os.path.join(DEBUG_DIR, "session_expired.png"))
                context.close()
                return False

            print("  Login OK!")

            # Step 4: Create new post
            print("\n[4/6] Creating new post...")
            page.goto("{}/publish/post".format(PUB_URL), timeout=60000, wait_until="domcontentloaded")
            time.sleep(10)

            editor_url = page.url
            print("  Editor URL: {}".format(editor_url))

            if "/publish/post/" not in editor_url:
                page.goto("{}/publish/post?type=newsletter".format(PUB_URL), timeout=60000)
                time.sleep(8)
                editor_url = page.url
                print("  After direct URL: {}".format(editor_url))

            # Wait for editor
            editor_found = False
            for i in range(30):
                els = page.locator('[contenteditable="true"]')
                cnt = els.count()
                vis = 0
                for j in range(cnt):
                    try:
                        if els.nth(j).is_visible(timeout=1000):
                            vis += 1
                    except:
                        pass
                if vis >= 1:
                    editor_found = True
                    print("  Editor ready: {} total, {} visible".format(cnt, vis))
                    break
                time.sleep(1)
                if i % 10 == 9:
                    print("  Waiting for editor... ({}s)".format(i + 1))

            if not editor_found:
                print("  Editor not found!")
                page.screenshot(path=os.path.join(DEBUG_DIR, "no_editor.png"))
                context.close()
                return False

            # Step 5: Fill content using keyboard type (same as May 8 version)
            print("\n[5/6] Filling content...")
            try:
                # Click on ProseMirror editor
                editor_el = page.locator('.ProseMirror[contenteditable="true"]').first
                if not editor_el.is_visible(timeout=5000):
                    editor_el = page.locator('[contenteditable="true"]').first
                editor_el.click()
                time.sleep(0.5)
                page.keyboard.press("Control+a")
                page.keyboard.press("Backspace")
                time.sleep(0.3)

                # Type title on first line
                page.keyboard.type(title, delay=15)
                page.keyboard.press("Enter")
                page.keyboard.press("Enter")
                time.sleep(0.3)

                # Type body (split into paragraphs)
                paragraphs = article_body.split('\n\n')
                for idx, para in enumerate(paragraphs):
                    # Clean paragraph
                    para = para.strip()
                    if not para:
                        continue
                    # Skip the title if it's already in the body
                    if idx == 0 and para.startswith('# '):
                        para = para[2:]
                    if not para:
                        continue

                    page.keyboard.type(para, delay=8)
                    page.keyboard.press("Enter")
                    page.keyboard.press("Enter")
                    time.sleep(0.2)

                time.sleep(2)
                print("  Content filled!")
            except Exception as e:
                print("  Fill error: {}".format(e))
                page.screenshot(path=os.path.join(DEBUG_DIR, "fill_error.png"))
                context.close()
                return False

            page.screenshot(path=os.path.join(DEBUG_DIR, "content_filled.png"))

            # Step 6: Publish - Click Continue then Send
            print("\n[6/6] Publishing...")
            time.sleep(3)

            # Click Continue (force=True as in May 8 version)
            print("  Clicking Continue...")
            continue_clicked = False
            try:
                btn = page.locator('button:has-text("Continue")').first
                if btn.is_visible(timeout=5000):
                    is_disabled = btn.is_disabled(timeout=2000)
                    btn.click(force=True)
                    continue_clicked = True
                    print("  Clicked Continue (force=True, disabled={})".format(is_disabled))
                    time.sleep(4)
            except Exception as e:
                print("  Continue error: {}".format(e))

            if not continue_clicked:
                # Try alternative: JS click
                print("  Trying JS click for Continue...")
                page.evaluate("""() => {
                    var btns = document.querySelectorAll('button');
                    for (var i = 0; i < btns.length; i++) {
                        if (btns[i].textContent.trim().toLowerCase() === 'continue') {
                            btns[i].click();
                            return true;
                        }
                    }
                    return false;
                }""")
                time.sleep(4)

            page.screenshot(path=os.path.join(DEBUG_DIR, "after_continue.png"))

            # Click "Send to everyone now"
            print("  Looking for Send button...")
            time.sleep(5)

            published = False
            send_sels = [
                'button:has-text("Send to everyone now")',
                'button:has-text("Publish now")',
                '[role="button"]:has-text("Send to everyone now")',
                'button:has-text("Send")',
            ]

            for attempt in range(3):
                for sel in send_sels:
                    try:
                        btn = page.locator(sel).first
                        if btn.is_visible(timeout=8000):
                            btn.click()
                            published = True
                            print("  Clicked Send button: {} (attempt {})".format(sel, attempt + 1))
                            time.sleep(5)

                            # Check for confirmation dialog
                            for csel in ['button:has-text("Confirm")', 'button:has-text("Yes")']:
                                try:
                                    cb = page.locator(csel).first
                                    if cb.is_visible(timeout=3000):
                                        cb.click()
                                        time.sleep(3)
                                        break
                                except:
                                    continue
                            break
                    except:
                        continue

                if published:
                    break

                page.screenshot(path=os.path.join(DEBUG_DIR, "send_attempt_{}.png".format(attempt + 1)))
                print("  Send button not found (attempt {}/3), retrying...".format(attempt + 1))
                time.sleep(5)

            if not published:
                print("  Could not find Send button!")
                page.screenshot(path=os.path.join(DEBUG_DIR, "no_send_btn.png"))

            # Verify publish - multiple methods to avoid rate limits
            time.sleep(3)
            final_url = page.url
            print("\n  Final URL: {}".format(final_url))

            if published:
                current_url = page.url
                # Method 1: URL changed from /publish/post/ to /p/ (published post URL)
                if "/p/" in current_url and "/publish/" not in current_url:
                    print("  Published! Public URL: {}".format(current_url))
                # Method 2: URL still on /publish/post/ but with numeric ID (draft saved)
                # This happens when Substack keeps you on the editor after publishing
                elif "/publish/post/" in current_url:
                    # Check if page shows "Published" or "Sent" confirmation
                    try:
                        page_text = page.locator("body").inner_text(timeout=5000)
                        if "published" in page_text.lower() or "sent" in page_text.lower() or "scheduled" in page_text.lower():
                            print("  Published! (confirmed by page text)")
                        else:
                            # Extract post ID from URL and construct public URL
                            post_id_match = re.search(r'/publish/post/(\d+)', current_url)
                            if post_id_match:
                                post_id = post_id_match.group(1)
                                public_url = "https://{}.substack.com/p/{}".format(PUBLICATION_SLUG, post_id)
                                print("  Likely published! Post ID: {}".format(post_id))
                                print("  Public URL: {}".format(public_url))
                            else:
                                print("  Published! (URL indicates post was created)")
                    except Exception:
                        # If we can't read page text (e.g., rate limit), trust the URL pattern
                        post_id_match = re.search(r'/publish/post/(\d+)', current_url)
                        if post_id_match:
                            post_id = post_id_match.group(1)
                            public_url = "https://{}.substack.com/p/{}".format(PUBLICATION_SLUG, post_id)
                            print("  Likely published! Post ID: {}".format(post_id))
                            print("  Public URL: {}".format(public_url))
                        else:
                            print("  Published! (URL indicates post was created)")
                # Method 3: Check if we got redirected to a post URL
                elif re.match(r'https://[^/]+\.substack\.com/p/[^/]+', current_url):
                    print("  Published! Public URL: {}".format(current_url))
                else:
                    print("  Post may be a draft (unexpected URL: {})".format(current_url))
                    published = False

            # Save updated state
            context.storage_state(path=STATE_FILE)
            print("  Session state saved")

            page.screenshot(path=os.path.join(DEBUG_DIR, "final_result.png"))
            context.close()

            return published

        except Exception as e:
            print("\n  Error: {}".format(e))
            try:
                page.screenshot(path=os.path.join(DEBUG_DIR, "error.png"))
            except:
                pass
            context.close()
            return False


def main():
    print("=" * 60)
    print("Substack Auto-Publish (launch_persistent_context)")
    print("Time: {}".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    print("=" * 60)

    # Find the latest draft
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    draft_file = os.path.join(_script_dir, "substack_draft_{}.md".format(date_str))

    if not os.path.exists(draft_file):
        import glob
        drafts = sorted(glob.glob(os.path.join(_script_dir, "substack_draft_*.md")), reverse=True)
        if drafts:
            draft_file = drafts[0]
            print("Using latest draft: {}".format(draft_file))
        else:
            print("No draft file found. Run publish_now.py first to generate an article.")
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
    print("Article: '{}' ({} chars)".format(title, len(article_body)))

    # Publish
    success = publish_article(title, article_body)

    if success:
        print("\n" + "=" * 60)
        print("SUCCESS! Article published to Substack!")
        print("   View at: {}".format(PUB_URL))
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("FAILED. Check debug screenshots in .browser_sessions/debug/")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
