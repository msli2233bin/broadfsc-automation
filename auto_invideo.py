#!/usr/bin/env python3
"""
Auto-generate TikTok video using InVideo AI via browser automation.
- Opens InVideo AI
- Signs in with Google (user needs to complete auth)
- Enters prompt to generate video with AI voiceover
- Waits for generation and downloads
"""
import sys, time, os
sys.stdout.reconfigure('utf-8')

from playwright.sync_api import sync_playwright

SCRIPT = """Create a 60-second TikTok vertical video (9:16) about support and resistance levels in stock trading. Use a professional male voiceover with a calm, authoritative tone. Here's the exact narration:

"Support and resistance levels are the cornerstone of all technical analysis. Every professional trader uses these levels to make buy and sell decisions.

Today, I'll walk you through how to find them and trade them. Let's look at this NVIDIA 4-hour chart.

Now, look at this area right here. Price has tested this level near 920 dollars THREE times, and each time it got rejected. This is what we call RESISTANCE.

It acts like a ceiling that price struggles to break through. The more times price tests this level, the stronger the resistance becomes.

And down below, we have SUPPORT around 810 dollars. See how price bounced from here multiple times? Buyers consistently step in at this price. This is your floor.

Here's your actionable trading plan: First, always mark support and resistance before entering any trade. Second, buy near support with a tight stop loss below it. Third, sell near resistance or wait for a confirmed breakout. Fourth, remember that broken resistance becomes new support, and broken support becomes new resistance.

Thank you for watching! If you found this helpful, make sure to follow me for more technical analysis content. Got a different take? Let's discuss in the comments!"

Use stock market charts, candlestick patterns, and trading screen visuals. Style: dark background, neon green and red accents, professional financial education look."""

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        slow_mo=500,
    )
    context = browser.new_context(
        viewport={'width': 1280, 'height': 900},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130.0.0.0 Safari/537.36'
    )
    page = context.new_page()
    
    # Save script to clipboard-ready file
    script_path = os.path.join(os.path.expanduser('~'), 'Desktop', 'invideo_prompt.txt')
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(SCRIPT)
    print(f"✅ Prompt saved to Desktop/invideo_prompt.txt")
    
    # Go to InVideo AI
    print("🌐 Opening InVideo AI...")
    page.goto('https://invideo.io/make/ai-video-generator/', timeout=60000)
    time.sleep(5)
    
    print(f"Page title: {page.title()}")
    print(f"URL: {page.url}")
    
    # Take screenshot
    page.screenshot(path=os.path.join(os.path.expanduser('~'), 'Desktop', 'invideo_step1.png'))
    print("📸 Screenshot saved to Desktop/invideo_step1.png")
    
    # Try to find prompt input
    print("🔍 Looking for text input...")
    
    # Check all inputs
    textareas = page.query_selector_all('textarea')
    inputs = page.query_selector_all('input[type="text"]')
    content_editables = page.query_selector_all('[contenteditable="true"]')
    
    print(f"Found {len(textareas)} textareas, {len(inputs)} inputs, {len(content_editables)} content-editables")
    
    # Find buttons
    buttons = page.query_selector_all('button')
    print(f"Found {len(buttons)} buttons:")
    for i, btn in enumerate(buttons[:20]):
        try:
            text = btn.inner_text()[:60]
            vis = btn.is_visible()
            if vis:
                print(f"  [{i}] '{text}' (visible)")
        except:
            pass
    
    # Try to find and fill the prompt
    for selector in ['textarea', '[contenteditable="true"]', 'input[type="text"]']:
        try:
            el = page.query_selector(selector)
            if el and el.is_visible():
                print(f"\n✅ Found input: {selector}")
                el.click()
                time.sleep(0.5)
                
                # Type the prompt
                page.keyboard.type(SCRIPT, delay=10)
                print("✅ Prompt entered!")
                
                # Screenshot after typing
                page.screenshot(path=os.path.join(os.path.expanduser('~'), 'Desktop', 'invideo_step2.png'))
                print("📸 Screenshot saved to Desktop/invideo_step2.png")
                
                # Try to find and click Generate button
                time.sleep(2)
                for btn_text in ['Generate', 'Create', 'Make video', 'Start']:
                    try:
                        btn = page.query_selector(f'button:has-text("{btn_text}")')
                        if btn and btn.is_visible():
                            print(f"\n🎯 Found Generate button: '{btn_text}'")
                            print("⚠️  NOT auto-clicking - please review and click yourself")
                            break
                    except:
                        continue
                break
        except Exception as e:
            print(f"  Selector {selector} failed: {e}")
            continue
    
    print("\n" + "=" * 70)
    print("🎥 InVideo AI is open in the browser!")
    print("📋 If prompt wasn't auto-entered, find it on Desktop/invideo_prompt.txt")
    print("🖱️  Review the page and click Generate when ready")
    print("⏳ Video generation takes ~2-5 minutes")
    print("💾 Download the video when it's ready")
    print("❌ Close the browser when done")
    print("=" * 70)
    
    # Keep browser open
    try:
        while True:
            time.sleep(1)
            try:
                page.evaluate('1+1')
            except:
                break
    except KeyboardInterrupt:
        pass
    
    browser.close()
    print("✅ Done!")
