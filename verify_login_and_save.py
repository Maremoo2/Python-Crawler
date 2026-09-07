from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto('https://www.licensingschool.co.uk/licenseverse/', wait_until='domcontentloaded', timeout=60000)
    body = page.locator('body').inner_text().lower()
    print('logout_visible', 'logout' in body or 'log out' in body)
    print('login_visible', 'login' in body or 'sign in' in body or 'log in' in body)
    print('page_url', page.url)
    context.storage_state(path='licenseverse_state.json')
    print('saved state')
