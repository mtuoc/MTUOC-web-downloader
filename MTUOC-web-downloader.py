import asyncio
import argparse
import os
import requests
import warnings
import sys
import random
import urllib.parse
from urllib.parse import urlparse, urljoin
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, BrowserConfig
import urllib3
from usp.tree import sitemap_tree_for_homepage

# --- CONFIGURATION ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
os.environ["PYTHONWARNINGS"] = "ignore"

EXT_MAP = {
    'pdf': ['.pdf'],
    'docs': ['.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.rfa', '.ifc', '.dwg'],
    'media': ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.mp4', '.avi', '.mov', '.mp3']
}

# --- PERSISTENCE HELPERS ---

def save_list_to_file(filename, data_set):
    """Saves a set of URLs to a text file."""
    with open(filename, "w", encoding="utf-8") as f:
        for item in sorted(list(data_set)):
            f.write(f"{item}\n")

def load_list_from_file(filename):
    """Loads URLs from a text file into a set."""
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

# --- DISCOVERY HELPERS ---

def discover_sitemaps_with_usp(url):
    print(f"--- 🗺️  Phase 0: Fetching Sitemap ---")
    try:
        tree = sitemap_tree_for_homepage(url)
        urls = set(page.url for page in tree.all_pages())
        print(f"      ✓ Found {len(urls)} URLs in sitemap.")
        return urls
    except Exception as e:
        print(f"      ! Sitemap error: {e}")
    return set()

def discover_wayback_links(domain):
    print(f"--- 🏛️  Phase 1: Querying Wayback Machine index for {domain} ---")
    cdx_url = f"http://web.archive.org/cdx/search/cdx?url={domain}/*&output=json&fl=original&collapse=urlkey&limit=15000"
    try:
        r = requests.get(cdx_url, timeout=60)
        data = r.json()
        if len(data) > 1:
            found = set(item[0] for item in data[1:])
            print(f"      ✓ Retrieved {len(found)} historical URLs from Wayback.")
            return found
    except Exception as e:
        print(f"      ! Wayback index error: {e}")
    return set()

async def get_wayback_snapshot_url(url, date=None):
    """Queries the Wayback Availability API for the closest snapshot."""
    api_url = f"http://archive.org/wayback/available?url={urllib.parse.quote(url)}"
    if date: api_url += f"&timestamp={date}"
    try:
        loop = asyncio.get_event_loop()
        r = await loop.run_in_executor(None, lambda: requests.get(api_url, timeout=10))
        data = r.json()
        if data.get("archived_snapshots", {}).get("closest"):
            wb_url = data["archived_snapshots"]["closest"]["url"]
            return wb_url.replace("/web/", "/webid_/", 1)
    except: pass
    return None

def url_to_local_path(url, base_folder):
    """Converts a URL to a structured local file path."""
    parsed = urlparse(url)
    path = parsed.path
    if not path or path == "/": path = "/index.html"
    elif not os.path.splitext(path)[1]: path = path.rstrip("/") + "/index.html"
    domain_folder = parsed.netloc.replace(".", "_")
    return os.path.normpath(os.path.join(base_folder, domain_folder, path.lstrip("/")))

async def download_binary(url, local_path):
    """Downloads non-HTML files directly using requests."""
    try:
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        r = requests.get(url, stream=True, timeout=20, verify=False)
        if r.status_code == 200:
            with open(local_path, 'wb') as f:
                for chunk in r.iter_content(8192): f.write(chunk)
            return True
    except: pass
    return False

# --- MAIN CRAWLER ---

async def main_crawler():
    parser = argparse.ArgumentParser(description="MTUOC Final Archeologist Crawler")
    parser.add_argument("url", type=str, nargs="?", help="The starting URL to crawl.")
    parser.add_argument("-o", "--output_dir", default="mirror_site", help="Local directory to save the mirror.")
    parser.add_argument("-l", "--output_list", default="links.txt", help="File to save the list of all found URLs.")
    parser.add_argument("-t", "--timeout", type=int, default=60, help="Timeout in seconds for page loading.")
    parser.add_argument("--web", action="store_true", help="Enable HTML downloading.")
    parser.add_argument("--pdf", action="store_true", help="Enable PDF downloading.")
    parser.add_argument("--docs", action="store_true", help="Enable documents downloading.")
    parser.add_argument("--media", action="store_true", help="Enable media downloading.")
    parser.add_argument("--robots", action="store_true", help="Respect robots.txt rules during the crawl.")
    parser.add_argument("--visible", action="store_true", help="Run the browser in visible mode.")
    parser.add_argument("--delay", type=float, default=1.0, help="Base delay between requests (randomized).")
    parser.add_argument("--sitemap", action="store_true", help="Discover URLs via sitemaps.")
    parser.add_argument("--wayback", action="store_true", help="Discover and recover URLs from Wayback Machine.")
    parser.add_argument("--date", type=str, help="Wayback snapshot date (YYYYMMDD).")
    
    args = parser.parse_args()
    if not args.url:
        parser.print_help()
        return

    if not (args.web or args.pdf or args.docs or args.media): args.web = True

    start_domain = urlparse(args.url).netloc
    TMP_TO_DOWNLOAD = "toDownload.tmp"
    TMP_ALREADY_DOWNLOADED = "alreadyDownloaded.tmp"
    TMP_ERRORS = "errors.tmp"

    # Load persistent state
    visited = load_list_from_file(TMP_ALREADY_DOWNLOADED)
    errors = load_list_from_file(TMP_ERRORS)
    to_visit_set = load_list_from_file(TMP_TO_DOWNLOAD)

    if not to_visit_set:
        print("--- 🔍 Discovery Mode: Initializing queue... ---")
        initial_url = args.url if args.url.startswith("http") else "https://" + args.url
        to_visit_set.add(initial_url)
        if args.sitemap: to_visit_set.update(discover_sitemaps_with_usp(args.url))
        if args.wayback: to_visit_set.update(discover_wayback_links(start_domain))
    else:
        print(f"--- ♻️  Resume Mode: {len(to_visit_set)} URLs pending ---")

    to_visit = [u for u in to_visit_set if u not in visited and u not in errors]
    
    browser_config = BrowserConfig(headless=not args.visible, ignore_https_errors=True)
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        try:
            while to_visit:
                current_url = to_visit.pop(0).split('#')[0].rstrip('/')
                if current_url in visited or current_url in errors: continue

                print(f"[{len(visited)} ✅ | {len(to_visit)} ⏳] -> {current_url}")
                local_path = url_to_local_path(current_url, args.output_dir)
                
                url_lower = current_url.lower()
                is_binary = any(url_lower.endswith(ext) for cat in EXT_MAP.values() for ext in cat)
                is_web = not is_binary

                if not ((args.web and is_web) or (args.pdf and url_lower.endswith('.pdf')) or 
                        (args.docs and any(url_lower.endswith(e) for e in EXT_MAP['docs'])) or 
                        (args.media and any(url_lower.endswith(e) for e in EXT_MAP['media']))):
                    visited.add(current_url)
                    continue

                success = False
                
                # Setup crawler config with ROBOTS option
                run_config = CrawlerRunConfig(
                    check_robots_txt=args.robots,  # <--- OPCIÓ ROBOTS INTEGRADA
                    cache_mode=CacheMode.BYPASS, 
                    wait_until="domcontentloaded", 
                    page_timeout=args.timeout*1000
                )

                # 1. ATTEMPT LIVE DOWNLOAD
                try:
                    if is_web:
                        result = await crawler.arun(url=current_url, config=run_config)
                        if result.success:
                            os.makedirs(os.path.dirname(local_path), exist_ok=True)
                            with open(local_path, "w", encoding="utf-8") as f: f.write(result.html)
                            success = True
                            for l in result.links.get("internal", []) + result.links.get("external", []):
                                full_url = urljoin(current_url, l.get('href', '')).split('#')[0].rstrip('/')
                                if start_domain in urlparse(full_url).netloc and full_url not in visited and full_url not in errors and full_url not in to_visit:
                                    to_visit.append(full_url)
                    else:
                        success = await download_binary(current_url, local_path)
                except: success = False

                # 2. ATTEMPT WAYBACK FALLBACK
                if not success:
                    wb_snapshot = await get_wayback_snapshot_url(current_url, args.date)
                    if wb_snapshot:
                        try:
                            if is_web:
                                # Per al Wayback normalment no mirem robots.txt ja que és un arxiu històric
                                wb_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, page_timeout=args.timeout*1000)
                                result = await crawler.arun(url=wb_snapshot, config=wb_config)
                                if result.success:
                                    os.makedirs(os.path.dirname(local_path), exist_ok=True)
                                    with open(local_path, "w", encoding="utf-8") as f: f.write(result.html)
                                    success = True
                            else:
                                success = await download_binary(wb_snapshot, local_path)
                        except: pass

                if success:
                    visited.add(current_url)
                else:
                    errors.add(current_url)

                if len(visited) % 10 == 0:
                    save_list_to_file(TMP_ALREADY_DOWNLOADED, visited)
                    save_list_to_file(TMP_TO_DOWNLOAD, set(to_visit))
                    save_list_to_file(TMP_ERRORS, errors)

                await asyncio.sleep(args.delay * random.uniform(0.5, 1.5))

        except KeyboardInterrupt:
            print("\n🛑 Stopped. Progress saved.")
        finally:
            save_list_to_file(TMP_ALREADY_DOWNLOADED, visited)
            save_list_to_file(TMP_TO_DOWNLOAD, set(to_visit))
            save_list_to_file(TMP_ERRORS, errors)
            save_list_to_file(args.output_list, visited)

if __name__ == "__main__":
    asyncio.run(main_crawler())
