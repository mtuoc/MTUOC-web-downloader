import asyncio
import argparse
import os
import random
import requests
import urllib3
import sys
from urllib.parse import urlparse
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, BrowserConfig

# Desactivar avisos de seguretat SSL i warnings de versions
from urllib.parse import urlparse, unquote

def url_to_local_path(url, base_folder, subfolder="html"):
    """
    Descodifica la URL per fer els noms de fitxer llegibles i neteja
    caràcters prohibits per als sistemes operatius.
    """
    # 1. Passem de "%22Hem%20de%20resar..." a '"Hem de resar...'
    url_decoded = unquote(url)
    
    parsed = urlparse(url_decoded)
    path = parsed.path
    
    # 2. Gestionem la pàgina principal o carpetes
    if not path or path == "/": 
        path = "/index.html"
    elif not os.path.splitext(path)[1]: 
        path = path.rstrip("/") + "/index.html"
    
    # 3. Neteja de caràcters prohibits al disc (sobretot per a Windows/Mac)
    # Substituïm cometes, dos punts, asteriscs, etc. per guions baixos
    caracters_conflictius = ['"', ':', '*', '?', '<', '>', '|', '\\']
    for char in caracters_conflictius:
        path = path.replace(char, "_")
    
    # També és recomanable limitar la longitud si el titular és extremadament llarg
    if len(path) > 200:
        base, ext = os.path.splitext(path)
        path = base[:190] + ext

    domain_folder = parsed.netloc.replace(".", "_")
    
    # 4. Construïm la ruta final
    full_path = os.path.normpath(os.path.join(base_folder, subfolder, domain_folder, path.lstrip("/")))
    return full_path

async def is_url_alive(url):
    """Comprova si la URL original respon amb un 200 OK."""
    try:
        loop = asyncio.get_event_loop()
        # Fem un GET ràpid o HEAD per verificar existència
        r = await loop.run_in_executor(None, lambda: requests.head(url, timeout=5, verify=False, allow_redirects=True))
        return r.status_code == 200
    except:
        return False

async def main():
    parser = argparse.ArgumentParser(description="MTUOC Web Restorer - Original structure reconstructor")
    parser.add_argument("input_file", help="The TSV file from the Archeologist (Real_URL \t Wayback_URL)")
    parser.add_argument("-o", "--output_dir", default="restored_site", help="Directory where the mirror will be created")
    parser.add_argument("--text", action="store_true", help="Also save a clean version in .txt format")
    parser.add_argument("--delay", type=float, default=1.0, help="Seconds to wait between pages")
    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"Error: File {args.input_file} not found.")
        return

    # Llegir el mapeig: línia a línia
    tasks = []
    with open(args.input_file, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) == 2:
                tasks.append({"real": parts[0], "wayback": parts[1]})

    print(f"--- MTUOC Web Restorer ---")
    print(f"Output dir: {args.output_dir}")
    print(f"📄 Tasks: {len(tasks)} URLs to process")
    print("-" * 40)

    browser_config = BrowserConfig(headless=True, ignore_https_errors=True)
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler(config=browser_config) as crawler:
        for i, task in enumerate(tasks):
            real_url = task["real"]
            wayback_url = task["wayback"]
            
            # 1. Decidir font: Intentem Live, si no, Wayback
            print(f"[{i+1}/{len(tasks)}] {real_url}")
            alive = await is_url_alive(real_url)
            
            target_url = real_url if alive else wayback_url
            status_msg = "🟢 LIVE" if alive else "🏛️  WAYBACK"
            print(f"      Source used: {status_msg}")

            try:
                # 2. Descarregar amb Crawl4AI
                result = await crawler.arun(url=target_url, config=run_config)
                
                if result.success:
                    # RUTA DE GUARDAT: Sempre basada en la REAL_URL
                    html_path = url_to_local_path(real_url, args.output_dir, "html")
                    os.makedirs(os.path.dirname(html_path), exist_ok=True)
                    
                    # Guardar el fitxer HTML
                    with open(html_path, "w", encoding="utf-8") as f:
                        f.write(result.html)
                    
                    # Guardar el fitxer TEXT (opcional, en estructura paral·lela)
                    if args.text:
                        text_path = os.path.splitext(url_to_local_path(real_url, args.output_dir, "text"))[0] + ".txt"
                        os.makedirs(os.path.dirname(text_path), exist_ok=True)
                        with open(text_path, "w", encoding="utf-8") as f:
                            f.write(result.markdown or result.extracted_content or "")
                    
                    print(f"Saved at: {html_path}")
                else:
                    print(f"Error rendering: {result.error_message}")
            
            except Exception as e:
                print(f"Unexpected error {e}")

            # Espera aleatòria per evitar bloquejos
            await asyncio.sleep(args.delay * random.uniform(0.7, 1.3))

if __name__ == "__main__":
    asyncio.run(main())
