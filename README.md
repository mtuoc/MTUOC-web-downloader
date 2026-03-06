A set of Python tools for website mirroring, historical data retrieval, and structural restoration. It utilizes the crawl4ai framework for high-fidelity asynchronous crawling and interacts with the Wayback Machine CDX API for archaeological web recovery.
Installation and Requirements

The suite requires Python 3.10 or higher.
 
**Install Dependencies:**

Install the required libraries using the provided requirements file:

`pip install -r requirements.txt`

**Setup Browser Engine:**

Since crawl4ai relies on Playwright for rendering, you must install the Chromium binaries:

`playwright install chromium`

## 1. MTUOC Web Downloader

The MTUOC Web Downloader is a recursive crawler designed for the comprehensive mirroring of active websites. It features advanced persistence and supports multiple file formats.

**Usage**

`python MTUOC-web-downloader.py <URL> [options]`

Key Arguments: 

* --web: Enables the download of HTML content.
* --text: Extracts and saves a cleaned text/markdown version in a parallel directory.
* --pdf / --docs / --media: Enables the download of specific binary categories (PDFs, Office documents, or media files).
* --wayback: Enables discovery and fallback via the Wayback Machine if the live page is inaccessible.
*  --robots: Enforces strict compliance with the site's robots.txt file.
* --delay: Sets a base delay (in seconds) between requests to avoid server throttling.

Persistence Mechanism

The script manages state through .tmp files (toDownload.tmp, alreadyDownloaded.tmp, and errors.tmp). This allows the process to be paused and resumed without losing progress or duplicating down#loads.

## 2. MTUOC Web Archeologist

The MTUOC Web Archeologist serves as a historical indexer. It queries the Internet Archive to map every capture ever recorded for a given domain.
Usage

`python MTUOC-web-archeologist.py <domain> -o <mapping_file>`

* Data Streaming: Connects to the CDX API and processes results line-by-line to handle large-scale indices efficiently.
* User Interruption: Supports Ctrl+C to stop the indexing process while automatically saving all data retrieved up to that point.
* Format: Generates a Tab-Separated Values (TSV) file containing the original URL and the direct "id_" Wayback download link.

## 3. MTUOC Web Restorer

The MTUOC Web Restorer is a hybrid reconstruction tool. It takes the index produced by the Archeologist and rebuilds the website locally using its original directory structure.

**Usage** 

`python MTUOC-web-restorer.py <mapping_file> -o <output_dir> [options]`

Hybrid Strategy

For every entry in the mapping file, the Restorer:

* Performs a fast check to see if the original URL is live.
* * If live, it downloads the current version.
* * If the live version is unavailable, it automatically fetches the archived snapshot from the Wayback Machine link.

Path Sanitization and Normalization

* URL Decoding: Converts URL-encoded characters (e.g., %22, %20) into readable characters (quotes, spaces).
* Filesystem Safety: Automatically replaces characters that are illegal in certain operating systems (" : * ? < > | \) with underscores.
* Depth Management: Automatically creates the necessary subdirectories to match the original URL hierarchy.
