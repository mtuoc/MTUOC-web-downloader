import requests
import argparse
import sys
import signal
from urllib.parse import urlparse

interrupted = False

def signal_handler(sig, frame):
    global interrupted
    print("\n\n[!] Aturada detectada. Guardant dades obtingudes...")
    interrupted = True

signal.signal(signal.SIGINT, signal_handler)

def get_wayback_index(url_input, output_file):
    global interrupted
    parsed = urlparse(url_input)
    domain = parsed.netloc if parsed.netloc else url_input
    domain = domain.replace("www.", "")

    print(f"--- MTUOC Web Archeologist ---")
    print(f"Searching: {domain}")
    print(f"Ctrl+C to stop and save.")
    print("-" * 40)

    # API CDX: demanem original i timestamp
    cdx_url = f"http://web.archive.org/cdx/search/cdx?url={domain}/*&output=txt&fl=original,timestamp&collapse=urlkey"

    count = 0
    try:
        with requests.get(cdx_url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(output_file, "w", encoding="utf-8") as f:
                for line in r.iter_lines(decode_unicode=True):
                    if interrupted: break
                    if not line.strip(): continue
                    
                    parts = line.split()
                    if len(parts) >= 2:
                        original_url = parts[0]
                        timestamp = parts[1]
                        
                        # Data llegible
                        date = f"{timestamp[:4]}-{timestamp[4:6]}-{timestamp[6:8]}"
                        
                        # URL CLICABLE: Format estàndard del Wayback Machine
                        # Traiem l' "id_" perquè el navegador la pugui gestionar bé
                        wayback_url = f"https://web.archive.org/web/{timestamp}/{original_url}"
                        
                        f.write(f"{date}\t{original_url}\t{wayback_url}\n")
                        count += 1
                        
                        if count % 10 == 0:
                            sys.stdout.write(f"\r      URLs trobades: {count} ({date})")
                            sys.stdout.flush()
                            f.flush()

        print(f"\n\n--- Fet! {count} URLs guardades a: {output_file}")
    except Exception as e:
        print(f"\n[!] Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("-o", "--output", default="mapa.txt")
    args = parser.parse_args()
    get_wayback_index(args.url, args.output)
