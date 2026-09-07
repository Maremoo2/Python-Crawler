import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

ROOT_URL = "https://www.licensingschool.co.uk/licenseverse/on-premises/"

visited = set()
to_visit = [ROOT_URL]
queued = {ROOT_URL}

while to_visit:
    url = to_visit.pop(0)
    queued.discard(url)

    if url in visited:
        continue

    visited.add(url)

    try:
        response = requests.get(url, timeout=20)
        soup = BeautifulSoup(response.text, "html.parser")

        for link in soup.find_all("a", href=True):
            href = urljoin(url, link["href"])

            if (
                "licensingschool.co.uk/licenseverse/" in href
                and "dashboard" not in href
                and "login" not in href
                and "account" not in href
                and "#" not in href
                and href not in visited
                and href not in queued
            ):
                to_visit.append(href)
                queued.add(href)

    except Exception:
        pass

print(f"Done! Crawled {len(visited)} pages.")
