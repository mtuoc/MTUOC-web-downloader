import requests
import argparse
import sys
import signal
from urllib.parse import urlparse

# Variable per gestionar la sortida neta
interrupted = False

def signal_handler(sig, frame):
    global interrupted
    print("\n\n[!] Stop detected (Ctrl+C). Saving data...")
    interrupted = True

# Assignem el control de Ctrl+C
signal.signal(signal.SIGINT, signal_handler)

def get_wayback_index(url_input, output_file):
    global interrupted
    parsed = urlparse(url_input)
    domain = parsed.netloc if parsed.netloc else url_input
    domain = domain.replace("www.", "")

    print(f"--- MTUOC Web Archeologist ---")
    print(f"Serching: {domain}")
    print(f"Press 'Ctrl+C' to stop i save the data found.")
    print("-" * 40)

    # Fem servir output=txt i fl=original,timestamp. És molt més lleuger.
    cdx_url = f"http://web.archive.org/cdx/search/cdx?url={domain}/*&output=txt&fl=original,timestamp&collapse=urlkey"

    count = 0
    try:
        # Iniciem la petició amb streaming
        with requests.get(cdx_url, stream=True, timeout=60) as r:
            r.raise_for_status()
            
            with open(output_file, "w", encoding="utf-8") as f:
                # El format txt de CDX torna una línia per cada entrada: "url timestamp"
                for line in r.iter_lines(decode_unicode=True):
                    if interrupted:
                        break
                    
                    if not line.strip():
                        continue
                    
                    parts = line.split()
                    if len(parts) >= 2:
                        original_url = parts[0]
                        timestamp = parts[1]
                        wayback_url = f"https://web.archive.org/web/{timestamp}id_/{original_url}"
                        
                        f.write(f"{original_url}\t{wayback_url}\n")
                        count += 1
                        
                        # Actualitzem el comptador cada 10 links per no saturar la CPU
                        if count % 10 == 0:
                            sys.stdout.write(f"\r      🔗 Links trobats: {count}")
                            sys.stdout.flush()
                            f.flush() # Assegurem que s'escriu al disc

        print(f"\n\n--- Done! Processed {count} URLs.")
        print(f"--- Results saved at: {output_file}")

    except Exception as e:
        print(f"\n[!] Conection error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MTUOC Web Archeologist - Fast indexer")
    parser.add_argument("url", help="URL or domain to investigate")
    parser.add_argument("-o", "--output", default="archeology_map.txt", help="Output file")
    
    args = parser.parse_args()
    get_wayback_index(args.url, args.output)
