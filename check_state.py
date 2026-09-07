from pathlib import Path
from playwright.sync_api import sync_playwright

files = ['licenseverse_state.json', 'licenseverse_state.backup.json', 'licenseverse_state.pre_relogin_20260703.json', 'licenseverse_state.stale.json']
urls = ['https://www.licensingschool.co.uk/licenseverse/', 'https://www.licensingschool.co.uk/licenseverse/on-premises/']
print('testing state files')
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    for f in files:
        path = Path(f)
        if not path.exists():
            print(f'{f}: missing')
            continue
        try:
            ctx = browser.new_context(storage_state=str(path))
            page = ctx.new_page()
            page.goto(urls[0], wait_until='domcontentloaded', timeout=60000)
            page.wait_for_load_state('networkidle', timeout=60000)
            body = page.locator('body').inner_text().lower()
            logged_in = 'logout' in body or 'log out' in body
            login_visible = 'login' in body or 'sign in' in body or 'log in' in body
            print(f'{f}: url={page.url} logged_in={logged_in} login_visible={login_visible}')
            ctx.close()
        except Exception as e:
            print(f'{f}: ERROR {e}')
    browser.close()
