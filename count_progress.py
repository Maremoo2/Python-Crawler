from pathlib import Path

visited_path = Path('visited_urls.txt')
errors_path = Path('errors.txt')
text_path = Path('LicenseVerse_clean.txt')

visited_lines = sum(1 for _ in visited_path.open('r', encoding='utf-8', errors='ignore')) if visited_path.exists() else 0
errors_lines = sum(1 for _ in errors_path.open('r', encoding='utf-8', errors='ignore')) if errors_path.exists() else 0
text_size = text_path.stat().st_size if text_path.exists() else 0

print(f'visited_urls_lines={visited_lines}')
print(f'errors_lines={errors_lines}')
print(f'LicenseVerse_clean_size_bytes={text_size}')
