# 🌐 MTUOC Mirroring Crawler

A robust website mirroring tool designed to create local copies of websites while ensuring maximum coverage by using the **Wayback Machine** as a fallback.

## ✨ Key Features

* **Live-First Logic**: Downloads the current version of the site directly from the web.
* **Wayback Fallback**: If a page is missing (404) or the server fails, it automatically retrieves the latest available version from the Internet Archive.
* **Recursive Crawling**: Discovers new internal links as it downloads, expanding the queue dynamically.
* **Checkpoint System**: Automatically saves progress to `.tmp` files. You can stop and resume the crawl at any time without losing data or redownloading files.
* **Smart Delays**: Uses randomized wait times (±50% of the base delay) to avoid being blocked by servers.
* **Selective Mirroring**: Choose exactly what to save: HTML, PDFs, Documents, or Media.

---

## Installation Guide

### 1. Install Dependencies

`pip install crawl4ai requests urllib3 ultrasitemap`

### 2. Setup Crawl4AI (Browser Engines)

The crawler uses a headless browser to render pages correctly. Run these commands to install the required components:
Bash

```
playwright install chromium
playwright install-deps chromium
```

## Usage

### Basic Command

`python mirror_crawler.py https://example.com --web --pdf --wayback`

### Full Options List

``
Option	Description
url	The starting URL (e.g., https://domain.com).
-o, --output_dir	Local folder for the mirror (Default: mirror_site).
-l, --output_list	File to save the final list of processed URLs (Default: links.txt).
--web	Download HTML pages.
--pdf	Download PDF files.
--docs	Download Office docs (.docx, .xlsx, .pdf, etc.).
--media	Download images and videos.
--robots	Respect robots.txt rules for live downloads.
--delay	Base seconds to wait between requests (randomized ±50%).
--sitemap	Extract all URLs from the site's sitemap at the start.
--wayback	Discover historical URLs and use them as fallback.
--date	Target a specific snapshot date (YYYYMMDDhhmmss).
--visible	Run the browser in non-headless (visible) mode. 
```

### Resuming a Session

If the script is interrupted (e.g., power loss or Ctrl+C), it maintains three persistent files:

* `toDownload.tmp`: The current queue of pending URLs.

* `alreadyDownloaded.tmp`: List of successfully processed URLs.

* `errors.tmp`: URLs that failed both live and archival attempts.

To resume: Simply run the script again with the same initial URL. It will detect the .tmp files and continue from the last checkpoint.

If you want to restart without resuming delerte these tmp files before restarting.

###Disclaimer

This tool is for researach and educational purposes. Always ensure you have permission to crawl a website and respect the site's terms of service.

# Founding

A set of scripts to download a whole website and store it locally developed in the framework of the project TAN-IBE: Neural Machine Translation for the romance languages of the Iberian Peninsula, founded by the Spanish Ministry of Science and Innovation Proyectos de generación de conocimiento 2021. Reference: PID2021-124663OB-I00 founded by MCIN /AEI /10.13039/501100011033 / FEDER, UE.

