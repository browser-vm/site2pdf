import asyncio
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright
from pypdf import PdfWriter

# --- Interactive Configuration ---
start_url = input("Enter the URL to scrape (e.g., https://docs.example.com/): ").strip()
if not start_url.startswith("http"):
    start_url = "https://" + start_url

print("\n(Optional) Enter a path to restrict crawling (e.g., /docs/)")
path_scope = input("Leave empty to scan the whole domain: ").strip()

output_filename = input("\nEnter output PDF name (default: output.pdf): ").strip()
if not output_filename:
    output_filename = "output.pdf"
if not output_filename.endswith(".pdf"):
    output_filename += ".pdf"

# Auto-extract domain
parsed_start = urlparse(start_url)
target_domain = parsed_start.netloc

print(f"\n🎯 Target Domain: {target_domain}")
if path_scope:
    print(f"🔒 Scope Restricted to: {path_scope}")

TEMP_DIR = "./temp_pdfs"
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

def sanitize_filename(url):
    parsed = urlparse(url)
    path = parsed.path.strip("/").replace("/", "_")
    if not path:
        path = "index"
    return f"{path}.pdf"

def is_in_scope(url):
    parsed = urlparse(url)
    if parsed.netloc != target_domain:
        return False
    if path_scope and not parsed.path.startswith(path_scope):
        return False
    return True

# --- Part 1: Crawler ---
def crawl_site(start_url):
    print(f"\n🕷️  Indexing site structure...")
    visited = set()
    to_visit = [start_url]
    sorted_urls = []

    while to_visit:
        current_url = to_visit.pop(0)
        parsed = urlparse(current_url)
        clean_url = parsed.scheme + "://" + parsed.netloc + parsed.path
        
        if clean_url in visited:
            continue
            
        try:
            # Strict Scope Check
            if not is_in_scope(clean_url):
                continue

            visited.add(clean_url)
            sorted_urls.append(clean_url)
            print(f"   Found: {clean_url}")
            
            response = requests.get(clean_url, timeout=10)
            if 'text/html' not in response.headers.get('Content-Type', ''):
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            
            for link in soup.find_all('a', href=True):
                full_url = urljoin(clean_url, link['href'])
                full_parsed = urlparse(full_url)
                full_clean = full_parsed.scheme + "://" + full_parsed.netloc + full_parsed.path
                
                if full_clean not in visited and full_clean not in to_visit:
                    if is_in_scope(full_clean):
                        to_visit.append(full_clean)

        except Exception as e:
            print(f"⚠️  Error crawling {clean_url}: {e}")

    print(f"✅ Indexed {len(sorted_urls)} pages.")
    return sorted_urls

# --- Part 2: PDF Renderer ---
async def generate_pdfs(url_list):
    print(f"\n🖨️  Rendering {len(url_list)} pages to PDF...")
    generated_files = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        for i, url in enumerate(url_list):
            try:
                print(f"   Processing ({i+1}/{len(url_list)}): {url}")
                await page.goto(url, wait_until="networkidle")
                
                # Optional: Hide visual clutter
                # await page.add_style_tag(content="nav, footer, aside { display: none !important; }")
                
                filename = os.path.join(TEMP_DIR, f"{i:03d}_{sanitize_filename(url)}")
                await page.pdf(path=filename, format="A4", print_background=True, margin={"top": "20px", "bottom": "20px"})
                generated_files.append(filename)
                
            except Exception as e:
                print(f"❌ Failed to print {url}: {e}")

        await browser.close()
    return generated_files

# --- Part 3: Merger ---
def merge_pdfs(pdf_files, output_file):
    if not pdf_files:
        print("❌ No PDFs to merge.")
        return

    print(f"\n📚 Merging into {output_file}...")
    merger = PdfWriter()

    for pdf in pdf_files:
        merger.append(pdf)

    with open(output_file, "wb") as f_out:
        merger.write(f_out)
    
    print("✨ PDF Generation Complete!")

# --- Execution ---
if __name__ == "__main__":
    try:
        all_urls = crawl_site(start_url)
        if all_urls:
            pdf_files = asyncio.run(generate_pdfs(all_urls))
            merge_pdfs(pdf_files, output_filename)
            
            # Cleanup
            for f in pdf_files:
                if os.path.exists(f): os.remove(f)
            if os.path.exists(TEMP_DIR): os.rmdir(TEMP_DIR)
            
            print(f"\n🎉 Success! Saved to: {os.path.abspath(output_filename)}")
        else:
            print("❌ No URLs found matching criteria.")
            
    except KeyboardInterrupt:
        print("\n🛑 Process cancelled by user.")