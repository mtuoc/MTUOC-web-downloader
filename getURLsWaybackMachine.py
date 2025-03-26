import requests
import codecs
import argparse
import re

def limpiar_link(link):
    patron = re.compile(r'https?://web\.archive\.org/web/\d+/(http[s]?://[^\s]+)')
    match = patron.search(link.strip())
    if match:
        return match.group(1)
    else:
        return None

def obtener_urls_wayback(domain, max_results=10):
    url = f"https://web.archive.org/cdx/search/cdx?url={domain}/*&output=json&fl=timestamp,original&filter=statuscode:200&limit={max_results}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        return [f"https://web.archive.org/web/{row[0]}/{row[1]}" for row in data[1:]]
    else:
        print("Error retrieving URLs")
        return []

def go(url, max_results, outfile, apply_filter):
    urls = obtener_urls_wayback(url, max_results=max_results)
    control = []
    with codecs.open(outfile, "w", encoding="utf-8") as sortida:
        for url in urls:
            url_neta = limpiar_link(url) if apply_filter else url
            if url_neta and url_neta not in control:
                sortida.write(url_neta + "\n")
                control.append(url_neta)
    print(f"URLs saved to {outfile}")

def main():
    parser = argparse.ArgumentParser(description="Retrieve archived URLs from Wayback Machine.")
    parser.add_argument("-u", "--url", required=True, help="Target domain (e.g., example.com)")
    parser.add_argument("-m", "--max-results", type=int, default=10, help="Maximum number of results to retrieve (default: 10)")
    parser.add_argument("-o", "--outfile", default="output.txt", help="Output file to save the URLs")
    parser.add_argument("-f", "--filter", action="store_true", help="Apply filtering to clean URLs")
    
    args = parser.parse_args()
    go(args.url, args.max_results, args.outfile, args.filter)

if __name__ == "__main__":
    main()
