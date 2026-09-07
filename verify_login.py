from pathlib import Path
from playwright.sync_api import sync_playwright

state = Path('licenseverse_state.json')
print('state_exists', state.exists())
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(storage_state=str(state))
    page = context.new_page()
    page.goto('https://www.licensingschool.co.uk/licenseverse/', wait_until='domcontentloaded', timeout=60000)
    body = page.locator('body').inner_text().lower()
    url = page.url.lower()
    print('url', url)
    print('logout_visible', ('logout' in body or 'log out' in body))
    print('login_visible', ('login' in body or 'sign in' in body or 'log in' in body))
    print('body_excerpt', body[:1000])
    context.close()
    browser.close()
