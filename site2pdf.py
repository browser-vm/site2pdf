import asyncio
import os
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright
from pypdf import PdfWriter

# --- Configuration ---
START_URL = "https://chemicaljs.github.io/"
TARGET_DOMAIN = "chemicaljs.github.io"
OUTPUT_PDF = "ChemicalJS_Documentation.pdf"
TEMP_DIR = "./temp_pdfs"

# Ensure temp directory exists
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

def sanitize_filename(url):
    """Converts a URL into a safe filename."""
    parsed = urlparse(url)
    path = parsed.path.strip("/").replace("/", "_")
    if not path:
        path = "index"
    return f"{path}.pdf"

# --- Part 1: Crawler (Synchronous) ---
def crawl_site(start_url, domain):
    print(f"🕷️  Indexing site: {start_url}...")
    visited = set()
    to_visit = [start_url]
    sorted_urls = []

    while to_visit:
        current_url = to_visit.pop(0)
        
        # Normalize URL (remove fragments)
        parsed = urlparse(current_url)
        clean_url = parsed.scheme + "://" + parsed.netloc + parsed.path
        
        if clean_url in visited:
            continue
            
        try:
            # Check if internal
            if parsed.netloc != domain:
                continue

            visited.add(clean_url)
            sorted_urls.append(clean_url)
            
            response = requests.get(clean_url, timeout=10)
            if 'text/html' not in response.headers.get('Content-Type', ''):
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            
            for link in soup.find_all('a', href=True):
                full_url = urljoin(clean_url, link['href'])
                # Remove hash and parameters for indexing
                full_url_clean = urlparse(full_url).scheme + "://" + urlparse(full_url).netloc + urlparse(full_url).path
                
                if full_url_clean not in visited and full_url_clean not in to_visit:
                    if urlparse(full_url_clean).netloc == domain:
                        to_visit.append(full_url_clean)

        except Exception as e:
            print(f"Error crawling {clean_url}: {e}")

    print(f"✅ Found {len(sorted_urls)} pages.")
    return sorted_urls

# --- Part 2: PDF Renderer (Async Playwright) ---
async def generate_pdfs(url_list):
    print("🖨️  Rendering pages to PDF...")
    generated_files = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        for i, url in enumerate(url_list):
            try:
                print(f"   Processing ({i+1}/{len(url_list)}): {url}")
                await page.goto(url, wait_until="networkidle")
                
                # Optional: Add custom CSS to hide navbars or fix layout for print
                # await page.add_style_tag(content="nav { display: none; }") 
                
                filename = os.path.join(TEMP_DIR, f"{i:03d}_{sanitize_filename(url)}")
                
                await page.pdf(path=filename, format="A4", print_background=True, margin={"top": "20px", "bottom": "20px"})
                generated_files.append(filename)
                
            except Exception as e:
                print(f"   Failed to print {url}: {e}")

        await browser.close()
    return generated_files

# --- Part 3: Merger ---
def merge_pdfs(pdf_files, output_filename):
    print(f"📚 Merging {len(pdf_files)} files into {output_filename}...")
    merger = PdfWriter()

    for pdf in pdf_files:
        merger.append(pdf)

    with open(output_filename, "wb") as f_out:
        merger.write(f_out)
    
    print("✨ Done!")

# --- Main Execution ---
if __name__ == "__main__":
    # 1. Crawl
    all_urls = crawl_site(START_URL, TARGET_DOMAIN)
    
    # 2. Render
    # Run async function in sync context
    pdf_files = asyncio.run(generate_pdfs(all_urls))
    
    # 3. Merge
    if pdf_files:
        merge_pdfs(pdf_files, OUTPUT_PDF)
        
        # Cleanup (Optional: remove temp files)
        # for f in pdf_files: os.remove(f)
        # os.rmdir(TEMP_DIR)
        print(f"File saved as: {os.path.abspath(OUTPUT_PDF)}")
    else:
        print("No PDFs were generated.")
