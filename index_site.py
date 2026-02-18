import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import sys

# --- Interactive Setup ---
start_url = input("Enter the URL to index (e.g., https://docs.example.com): ").strip()
if not start_url.startswith("http"):
    start_url = "https://" + start_url

# Optional: Path Restriction
print("\n(Optional) Enter a path to restrict crawling (e.g., /docs/)")
path_scope = input("Leave empty to scan the whole domain: ").strip()

# Automatically extract domain to keep crawl internal
parsed_start = urlparse(start_url)
target_domain = parsed_start.netloc

print(f"\n🎯 Target Domain: {target_domain}")
if path_scope:
    print(f"🔒 Scope Restricted to: {path_scope}")
else:
    print(f"🌍 Scope: Entire Domain")

visited_urls = set()
urls_to_visit = [start_url]

def clean_url(url):
    """Normalize URL by removing fragments."""
    parsed = urlparse(url)
    return parsed.scheme + "://" + parsed.netloc + parsed.path

def is_valid_url(url):
    """Checks domain and path scope."""
    parsed = urlparse(url)
    
    # 1. Check Domain
    if parsed.netloc and parsed.netloc != target_domain:
        return False
    
    # 2. Check Protocol
    if parsed.scheme and parsed.scheme not in ['http', 'https']:
        return False
        
    # 3. Check Path Scope (if set)
    if path_scope and not parsed.path.startswith(path_scope):
        return False
        
    return True

print(f"\n🕷️  Starting scan...\n")

try:
    while urls_to_visit:
        current_url = urls_to_visit.pop(0)
        clean_current = clean_url(current_url)
        
        if clean_current in visited_urls:
            continue

        try:
            # Check scope before requesting
            if not is_valid_url(clean_current):
                continue

            response = requests.get(clean_current, timeout=10)
            visited_urls.add(clean_current)
            
            # Only parse HTML
            if 'text/html' not in response.headers.get('Content-Type', ''):
                continue

            soup = BeautifulSoup(response.text, "html.parser")

            for link in soup.find_all('a', href=True):
                raw_href = link['href']
                full_url = urljoin(clean_current, raw_href)
                final_url = clean_url(full_url)

                if is_valid_url(final_url) and final_url not in visited_urls:
                    if final_url not in urls_to_visit:
                        urls_to_visit.append(final_url)
                        print(f"Found: {final_url}")

        except Exception as e:
            print(f"⚠️  Error accessing {clean_current}: {e}")

except KeyboardInterrupt:
    print("\n🛑  Stopping scan early...")

# Save results
filename_slug = path_scope.strip("/").replace("/", "_") if path_scope else "full_site"
output_file = f"urls_{target_domain.replace('.', '_')}_{filename_slug}.txt"

print(f"\n💾  Saving {len(visited_urls)} URLs to {output_file}...")
with open(output_file, "w") as f:
    for url in sorted(visited_urls):
        f.write(url + "\n")

print("Done!")