"""Diagnose what LinkedIn's login page actually shows."""
import os, json
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=500)
    context = browser.new_context(
        viewport={'width': 1280, 'height': 800},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    )
    page = context.new_page()

    print('Navigating to LinkedIn login...')
    page.goto('https://www.linkedin.com/login', wait_until='domcontentloaded', timeout=60000)
    print(f'URL: {page.url}')
    page.wait_for_load_state('networkidle', timeout=15000)
    print(f'URL after load: {page.url}')

    # Take screenshot
    page.screenshot(path='login_page.png', full_page=True)
    print('Screenshot saved to login_page.png')

    # Check what form fields are visible
    username = page.query_selector('#username')
    username_input = page.query_selector('input[name="session_key"]')
    any_input = page.query_selector_all('input')
    print(f'#username found: {username is not None}')
    print(f'input[name=session_key] found: {username_input is not None}')
    print(f'Total input elements: {len(any_input)}')
    for inp in any_input[:10]:
        t = inp.get_attribute('type') or ''
        n = inp.get_attribute('name') or ''
        i = inp.get_attribute('id') or ''
        print(f'  input type={t} name={n} id={i}')

    import time
    time.sleep(30)  # Keep browser open for 30s so user can see it
    browser.close()
