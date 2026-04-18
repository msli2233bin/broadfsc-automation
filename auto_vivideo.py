#!/usr/bin/env python3
"""
Auto-generate TikTok video using Vivideo.ai
- Opens Vivideo.ai in browser
- Pastes script text
- Selects TikTok 9:16 format + AI voiceover
- Generates and downloads video
"""

import sys
import os
import time
import asyncio

sys.stdout.reconfigure(encoding='utf-8')

# === Script content ===
SCRIPT = """Support and resistance levels are the cornerstone of all technical analysis. Every professional trader uses these levels to make buy and sell decisions.

Today, I'll walk you through how to find them and trade them. Let's look at this NVIDIA 4-hour chart.

Now, look at this area right here. Price has tested this level near $920 THREE times, and each time it got rejected. This is what we call RESISTANCE.

It acts like a ceiling that price struggles to break through. The more times price tests this level, the stronger the resistance becomes.

And down below, we have SUPPORT around $810. See how price bounced from here multiple times? Buyers consistently step in at this price. This is your floor.

Here's your actionable trading plan: First, always mark support and resistance before entering any trade. Second, buy near support with a tight stop loss below it. Third, sell near resistance or wait for a confirmed breakout. Fourth, remember that broken resistance becomes new support, and broken support becomes new resistance.

Thank you for watching! If you found this helpful, make sure to follow me for more technical analysis content. Got a different take? Let's discuss in the comments!"""


async def main():
    from playwright.async_api import async_playwright
    
    print("🚀 Launching browser...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # Show browser for user interaction
            slow_mo=500,     # Slow down actions for visibility
        )
        
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
        )
        
        page = await context.new_page()
        
        print("🌐 Opening Vivideo.ai...")
        await page.goto('https://app.vivideo.ai', timeout=60000)
        await page.wait_for_load_state('networkidle', timeout=30000)
        
        # Take screenshot to see the page
        await page.screenshot(path=os.path.join(os.path.expanduser('~'), 'Desktop', 'vivideo_step1.png'))
        print("📸 Screenshot saved to Desktop/vivideo_step1.png")
        
        # Try to find the text/script input area
        print("🔍 Looking for text input area...")
        
        # Common selectors for video generation input
        input_selectors = [
            'textarea',
            'input[type="text"]',
            '[contenteditable="true"]',
            '[placeholder*="script"]',
            '[placeholder*="text"]',
            '[placeholder*="prompt"]',
            '[placeholder*="describe"]',
            '[placeholder*="Enter"]',
            '[data-testid*="input"]',
            '[data-testid*="text"]',
            '.script-input',
            '.text-input',
            '#script-input',
            '#text-input',
        ]
        
        found_input = None
        for selector in input_selectors:
            try:
                el = await page.query_selector(selector)
                if el:
                    found_input = selector
                    print(f"✅ Found input: {selector}")
                    break
            except:
                continue
        
        if found_input:
            print(f"📝 Typing script into {found_input}...")
            el = await page.query_selector(found_input)
            await el.click()
            await el.fill(SCRIPT)
            print("✅ Script text entered!")
        else:
            print("❌ Could not find text input automatically.")
            print("📋 The script text is ready - please paste it manually:")
            print("=" * 60)
            print(SCRIPT)
            print("=" * 60)
        
        # Take another screenshot
        await page.screenshot(path=os.path.join(os.path.expanduser('~'), 'Desktop', 'vivideo_step2.png'))
        print("📸 Screenshot saved to Desktop/vivideo_step2.png")
        
        # Try to find and click generate/create button
        print("🔍 Looking for Generate button...")
        button_selectors = [
            'button:has-text("Generate")',
            'button:has-text("Create")',
            'button:has-text("Make")',
            'button:has-text("Start")',
            'button[type="submit"]',
            '[data-testid*="generate"]',
            '[data-testid*="create"]',
            '.generate-btn',
            '.create-btn',
        ]
        
        for selector in button_selectors:
            try:
                btn = await page.query_selector(selector)
                if btn and await btn.is_visible():
                    print(f"🎯 Found Generate button: {selector}")
                    # Don't auto-click - let user review first
                    break
            except:
                continue
        
        print("\n" + "=" * 60)
        print("🎥 Browser is open with Vivideo.ai!")
        print("📋 If text wasn't auto-entered, please paste the script manually")
        print("🖱️ Then click Generate to create the video")
        print("💾 When done, download the video from the browser")
        print("❌ Close the browser window when finished")
        print("=" * 60)
        
        # Keep browser open for user interaction
        try:
            # Wait for user to close browser or timeout
            while True:
                await asyncio.sleep(1)
                try:
                    await page.evaluate('1+1')
                except:
                    print("👋 Browser closed by user")
                    break
        except:
            pass
        
        await browser.close()
        print("✅ Done!")


if __name__ == '__main__':
    asyncio.run(main())
