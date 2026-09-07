import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time

ROOT_URL = "https://www.licensingschool.co.uk/licenseverse/on-premises/"

visited = set()
to_visit = [ROOT_URL]

with open("LicenseVerse.txt", "w", encoding="utf-8") as outfile:
    while to_visit:
        url = to_visit.pop(0)

        if url in visited:
            continue

        visited.add(url)
        print(f"Visiting: {url}")

        try:
            response = requests.get(url, timeout=20)
            soup = BeautifulSoup(response.text, "html.parser")

            text = soup.get_text("\n", strip=True)

            outfile.write("\n\n")
            outfile.write("=" * 100)
            outfile.write("\n")
            outfile.write(url)
            outfile.write("\n")
            outfile.write("=" * 100)
            outfile.write("\n\n")
            outfile.write(text)

            for link in soup.find_all("a", href=True):
                href = urljoin(url, link["href"])

                if (
                    "licensingschool.co.uk/licenseverse/" in href
                    and "dashboard" not in href
                    and "login" not in href
                    and "account" not in href
                    and "#" not in href
                    and href not in visited
                ):
                    to_visit.append(href)

            time.sleep(1)

        except Exception as e:
            print(f"Error: {e}")

print(f"Done! Crawled {len(visited)} pages.")
