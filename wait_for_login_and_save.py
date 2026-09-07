from pathlib import Path
from playwright.sync_api import sync_playwright
import time

URL = 'https://www.licensingschool.co.uk/licenseverse/'
STATE_FILE = 'licenseverse_state.json'
PROFILE_DIR = Path('.playwright-profile')
PROFILE_DIR.mkdir(exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        str(PROFILE_DIR),
        headless=False,
        args=['--start-maximized'],
    )
    page = browser.new_page()
    page.goto(URL, wait_until='domcontentloaded', timeout=60000)
    print('Opened persistent browser. Please sign in to LicenseVerse if needed.')

    for _ in range(600):
        try:
            page.reload(wait_until='domcontentloaded', timeout=60000)
        except Exception:
            pass
        body_text = page.locator('body').inner_text().lower()
        current_url = page.url.lower()
        logged_in = ('logout' in body_text or 'log out' in body_text) and '/licenseverse/' in current_url
        login_visible = 'login' in body_text or 'sign in' in body_text or 'log in' in body_text
        if logged_in:
            break
        if 'licenseverse' in current_url and not login_visible:
            break
        time.sleep(1)

    body_text = page.locator('body').inner_text().lower()
    current_url = page.url.lower()
    logged_in = ('logout' in body_text or 'log out' in body_text) and '/licenseverse/' in current_url
    login_visible = 'login' in body_text or 'sign in' in body_text or 'log in' in body_text
    print('Final URL:', page.url)
    print('Logged in detected:', logged_in)
    print('Login visible:', login_visible)

    if logged_in or not login_visible:
        browser.storage_state(path=STATE_FILE)
        print(f'Saved state to {STATE_FILE}')
    else:
        print('Login not confirmed; state was not saved.')

    print('Keeping browser open until you close it manually...')
    while True:
        time.sleep(10)
