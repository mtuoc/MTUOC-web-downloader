import requests
import codecs
import tkinter as tk
from tkinter import filedialog, messagebox
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
        messagebox.showerror("Error", "Error retrieving URLs")
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
    messagebox.showinfo("Success", f"URLs saved to {outfile}")

def browse_file():
    filename = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
    if filename:
        entry_outfile.delete(0, tk.END)
        entry_outfile.insert(0, filename)

def run_script():
    url = entry_url.get()
    max_results = int(entry_max_results.get())
    outfile = entry_outfile.get()
    apply_filter = filter_var.get()
    if not url:
        messagebox.showerror("Error", "Please enter a URL")
        return
    go(url, max_results, outfile, apply_filter)

# GUI Setup
root = tk.Tk()
root.title("Wayback Machine URL Retriever")

tk.Label(root, text="Target domain:").grid(row=0, column=0, padx=5, pady=5)
entry_url = tk.Entry(root, width=40)
entry_url.grid(row=0, column=1, padx=5, pady=5)

tk.Label(root, text="Max results:").grid(row=1, column=0, padx=5, pady=5)
entry_max_results = tk.Entry(root, width=10)
entry_max_results.insert(0, "10")
entry_max_results.grid(row=1, column=1, padx=5, pady=5)

tk.Label(root, text="Output file:").grid(row=2, column=0, padx=5, pady=5)
entry_outfile = tk.Entry(root, width=30)
entry_outfile.grid(row=2, column=1, padx=5, pady=5)

tk.Button(root, text="Browse", command=browse_file).grid(row=2, column=2, padx=5, pady=5)

filter_var = tk.BooleanVar()
filter_checkbox = tk.Checkbutton(root, text="Apply Filtering", variable=filter_var)
filter_checkbox.grid(row=3, column=0, columnspan=2, pady=5)

tk.Button(root, text="Retrieve URLs", command=run_script).grid(row=4, column=0, columnspan=3, pady=10)

root.mainloop()
