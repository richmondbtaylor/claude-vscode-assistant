"""
Automated LinkedIn login with SMS verification support.
Uses a VISIBLE browser window so you can see what's happening
and enter the verification code directly if needed.
"""
import os, json, time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
email = os.getenv('LINKEDIN_EMAIL')
password = os.getenv('LINKEDIN_PASSWORD')
cookies_file = os.getenv('LINKEDIN_COOKIES_FILE', './linkedin_cookies.json')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=50)
    context = browser.new_context(
        viewport={'width': 1280, 'height': 800},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    )
    page = context.new_page()

    print('Opening LinkedIn login page...')
    page.goto('https://www.linkedin.com/login', wait_until='domcontentloaded', timeout=60000)
    page.wait_for_selector('#username', timeout=30000)
    time.sleep(1)
    page.fill('#username', email)
    time.sleep(0.5)
    page.fill('#password', password)
    time.sleep(0.5)
    page.click('button[type=submit]')
    time.sleep(5)

    current_url = page.url
    print(f'URL after login: {current_url}')

    if 'checkpoint' in current_url or 'challenge' in current_url:
        print()
        print('=' * 60)
        print('VERIFICATION REQUIRED')
        print('A verification code has been sent to your phone.')
        print('Please enter it in the browser window that just opened.')
        print('The script will wait up to 3 minutes...')
        print('=' * 60)

        # Wait for user to complete verification in the visible browser
        # We wait until the URL changes away from checkpoint
        for i in range(60):  # wait up to 3 minutes
            time.sleep(3)
            url = page.url
            if 'checkpoint' not in url and 'challenge' not in url and 'login' not in url:
                print(f'Verification complete! URL: {url}')
                break
            print(f'  Waiting... ({(i+1)*3}s)')
        else:
            print('Timed out waiting for verification.')

    print(f'Final URL: {page.url}')
    cookies = context.cookies()
    with open(cookies_file, 'w') as f:
        json.dump(cookies, f, indent=2)
    print(f'Saved {len(cookies)} cookies to {cookies_file}')
    browser.close()
