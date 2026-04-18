#!/usr/bin/env python3
"""Analyze Vivideo.ai page structure with Playwright"""
import sys, time
sys.stdout.reconfigure(encoding='utf-8')

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=300)
    page = browser.new_page(viewport={'width': 1280, 'height': 800})
    
    print('Opening Vivideo.ai...')
    page.goto('https://app.vivideo.ai', timeout=60000)
    time.sleep(8)
    
    print(f'Page title: {page.title()}')
    print(f'URL: {page.url}')
    
    # Find all textareas and inputs
    textareas = page.query_selector_all('textarea')
    inputs = page.query_selector_all('input')
    content_editables = page.query_selector_all('[contenteditable="true"]')
    
    print(f'Found {len(textareas)} textareas, {len(inputs)} inputs, {len(content_editables)} content-editables')
    
    # Find all buttons
    buttons = page.query_selector_all('button')
    print(f'Found {len(buttons)} buttons:')
    for i, btn in enumerate(buttons[:20]):
        try:
            text = btn.inner_text()
            visible = btn.is_visible()
            print(f'  Button {i}: "{text[:80]}" (visible={visible})')
        except:
            pass
    
    # Find all links
    links = page.query_selector_all('a')
    print(f'Found {len(links)} links')
    for i, link in enumerate(links[:15]):
        try:
            text = link.inner_text().strip()
            href = link.get_attribute('href') or ''
            if text:
                print(f'  Link {i}: "{text[:50]}" -> {href[:60]}')
        except:
            pass
    
    # Save page HTML for analysis
    html = page.content()
    with open(r'C:\Users\Administrator\Desktop\vivideo_page.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print('HTML saved to Desktop/vivideo_page.html')
    
    page.screenshot(path=r'C:\Users\Administrator\Desktop\vivideo_step1.png')
    print('Screenshot saved')
    
    browser.close()
    print('Done')
