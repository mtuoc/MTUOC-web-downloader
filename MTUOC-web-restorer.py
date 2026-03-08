import asyncio
import argparse
import os
import random
import requests
import urllib3
import sys
import re
from urllib.parse import urlparse, unquote
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, BrowserConfig

# Desactivar avisos de seguretat SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def url_to_local_path(url, base_folder, subfolder="html"):
    """
    Descodifica la URL i neteja caràcters prohibits per als sistemes operatius.
    """
    url_decoded = unquote(url)
    parsed = urlparse(url_decoded)
    path = parsed.path
    
    if not path or path == "/": 
        path = "/index.html"
    elif not os.path.splitext(path)[1]: 
        path = path.rstrip("/") + "/index.html"
    
    # Neteja de caràcters prohibits (Windows/Linux/Mac)
    caracters_conflictius = ['"', ':', '*', '?', '<', '>', '|', '\\']
    for char in caracters_conflictius:
        path = path.replace(char, "_")
    
    # Limitar longitud de camí per seguretat
    if len(path) > 200:
        base, ext = os.path.splitext(path)
        path = base[:190] + ext

    domain_folder = parsed.netloc.replace(".", "_")
    return os.path.normpath(os.path.join(base_folder, subfolder, domain_folder, path.lstrip("/")))

async def is_url_alive(url):
    """Comprova si la URL original respon (status 200)."""
    try:
        loop = asyncio.get_event_loop()
        r = await loop.run_in_executor(None, lambda: requests.head(url, timeout=5, verify=False, allow_redirects=True))
        return r.status_code == 200
    except:
        return False

def prepare_wayback_url(url):
    """
    Converteix una URL clicable de Wayback en una URL de contingut pur (id_).
    Exemple: .../web/20240101120000/http... -> .../web/20240101120000id_/http...
    """
    if "/web/" in url and "id_/" not in url:
        # Busquem el timestamp (14 dígits seguits de la barra /web/)
        match = re.search(r"/web/(\d{14})/", url)
        if match:
            timestamp = match.group(1)
            return url.replace(f"/web/{timestamp}/", f"/web/{timestamp}id_/")
    return url

async def main():
    parser = argparse.ArgumentParser(description="MTUOC Web Restorer - Original structure reconstructor")
    parser.add_argument("input_file", help="The mapping file (Date \t Real_URL \t Wayback_URL)")
    parser.add_argument("-o", "--output_dir", default="restored_site", help="Directory where the mirror will be created")
    parser.add_argument("--text", action="store_true", help="Also save a clean version in .txt format")
    parser.add_argument("--delay", type=float, default=1.0, help="Seconds to wait between pages")
    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"Error: File {args.input_file} not found")
        return

    tasks = []
    with open(args.input_file, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")
            # Suport per a 3 columnes (Data, Real, Wayback) o 2 columnes (Real, Wayback)
            if len(parts) == 3:
                tasks.append({"real": parts[1], "wayback": parts[2]})
            elif len(parts) == 2:
                tasks.append({"real": parts[0], "wayback": parts[1]})

    print(f"--- MTUOC Web Restorer ---")
    print(f"Destination: {args.output_dir}")
    print(f"Total tasks: {len(tasks)}")
    print("-" * 40)

    browser_config = BrowserConfig(headless=True, ignore_https_errors=True)
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler(config=browser_config) as crawler:
        for i, task in enumerate(tasks):
            real_url = task["real"]
            # Convertim a id_ només per a la descàrrega interna
            wayback_url = prepare_wayback_url(task["wayback"])
            
            print(f"[{i+1}/{len(tasks)}] {real_url}")
            
            alive = await is_url_alive(real_url)
            target_url = real_url if alive else wayback_url
            source_tag = "LIVE" if alive else "WAYBACK"
            
            print(f"      Source: {source_tag}")

            try:
                result = await crawler.arun(url=target_url, config=run_config)
                
                if result.success:
                    # Guardar HTML (sempre ruta basada en URL real)
                    html_path = url_to_local_path(real_url, args.output_dir, "html")
                    os.makedirs(os.path.dirname(html_path), exist_ok=True)
                    
                    with open(html_path, "w", encoding="utf-8") as f:
                        f.write(result.html)
                    
                    # Guardar Text si es demana
                    if args.text:
                        text_path = os.path.splitext(url_to_local_path(real_url, args.output_dir, "text"))[0] + ".txt"
                        os.makedirs(os.path.dirname(text_path), exist_ok=True)
                        with open(text_path, "w", encoding="utf-8") as f:
                            f.write(result.markdown or "")
                    
                    print(f"      Saved at: {html_path}")
                else:
                    print(f"      Render error: {result.error_message}")
            
            except Exception as e:
                print(f"      Critical error: {e}")

            await asyncio.sleep(args.delay * random.uniform(0.7, 1.3))

if __name__ == "__main__":
    asyncio.run(main())
