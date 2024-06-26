# MTUOC-web-downloader
A set of scripts to download a whole website and store it locally developed in the framework of the project **TAN-IBE: Neural Machine Translation for the romance languages of the Iberian Peninsula**, founded by the Spanish Ministry of Science and Innovation Proyectos de generación de conocimiento 2021. Reference: PID2021-124663OB-I00 founded by MCIN /AEI /10.13039/501100011033 / FEDER, UE.

# 1. Introduction

In this repository a set of scripts for downloading a whole website are available. To perform this task, two different steps should be:

- Retrieve all the sitemap of the website with MTUOC-sitemap.py
- Download all the links in the sitemap, and while downloading, detecting new internal links to download. This can be performed by MTUOC-download-from-sitemap-selenium.py and MTUOC-download-from-sitemap-requests.py

Not all strategies (selenium and requests) work for all websites, so you should try them and decide which is more suitable. You may also find some websites from where you can't get any file.

# 2. Prerequisites

The programs are develped in Python version 3 and you need a Python 3 interpreter in your system. To run the programs you should install the following prerequisites:

For MTUOC-sitemap.py

```
requests
ultimate_sitemap_parser
beautifulsoup4
```

For MTUOC-donwload-from-sitemap.py:

If you DON'T plan to use the Selenium strategy, these requisites are enough:

```
requests
beautifulsoup4
```

If you plan to use the Selenium strategy, these requisites are also needed:

```
selenium
```


For MTUOC-downloadedweb2text.py

```
dewiki
fasttext
regex
textract
lxml
html2text
beautifulsoup4
langcodes
language_data
```

To run this program you also need a FastText language identification model. By defaul, lid.176.bin is used. You can download this model from: [https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin](https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin). 


You can use pip or pip3 (depending on your installation) (use sudo if you plan to install in the whole system or use a virtual environment):

```
pip3 install beautifulsoup4 dewiki fasttext html2text langcodes language_data lxml regex requests selenium textract ultimate_sitemap_parser
```


# 3. MTUOC-sitemap

You can use the option -h to get the help of the program:

```
python3 MTUOC-sitemap.py -h
[usage: MTUOC-sitemap.py [-h] -u URL [-p PREFIX] [-n FILENAME]

MTUOC program to get the links from a website.

optional arguments:
  -h, --help            show this help message and exit
  -u URL, --url URL     The URL of the website to explore.
  -p PREFIX, --prefix PREFIX
                        The prefix to use for the file containing the links. The full name will
                        contain the prefix and the domain.
  -n FILENAME, --name FILENAME
                        The name of the file containing the links. This option overrides -p/--prefix.]
```

If we want to get the sitemap of a website, let's say https://medlineplus.gov/, we can run MTUOC-sitemap.py giving the URL with the option -u or --url. If we don't specify a prefix or a name, an automatic name for the sitemap file will be generated ("sitemap-"+domain+".txt")

```
python3 MTUOC-sitemap.py -u https://medlineplus.gov
```
The sitemap would be named: sitemap-medlineplus_gov.txt We can specify a different prefix with the -p/--prefix option or a name with the -n/--name option. The sitemap will contain "all" the links in the webpage, or at least some of them.

Now, in sitemap-medlineplus_gov.txt we have all the links in the website (the links found in the sitemap):

```
https://medlineplus.gov/all_easytoread.html
https://medlineplus.gov/games.html
https://medlineplus.gov/healthchecktools.html
https://medlineplus.gov/druginfo/herb_All.html
https://medlineplus.gov/organizations/all_organizations.html
https://medlineplus.gov/organizations/orgbytopic_v.html
https://medlineplus.gov/organizations/orgbytopic_e.html
https://medlineplus.gov/organizations/orgbytopic_n.html
https://medlineplus.gov/organizations/orgbytopic_j.html
https://medlineplus.gov/organizations/orgbytopic_p.html
https://medlineplus.gov/organizations/orgbytopic_g.html
...
```

If no links are retrieved, the output file will contain the URL and some links obtained from a search in Google.

Sometimes these sitemaps are too large. You can edit the file, copy desired links to another file, use grep or whatever to adapt the results to your needs.

# 4. MTUOC-download-from-sitemap

This program can use two diferents strategies to download the websites: Selenium (the default one) or requests. Depending on the website to download one version can work better than the other. The use of the selenium strategy is recommended as a first try. 

The program needs a text file contaning a list of links to download. This list can be constructed with the MTUOC-sitemap.py program. If you don't have such a list, you can create a text file with the URL of the website to download. The program will download all the links in the file and for each link it will try to detect new internal links to download.

The program has the option -h that shows the help of the program:

```
usage: MTUOC-download-from-sitemap.py [-h] -f SITEMAPFILE [-d OUTDIR] [-s STRATEGY]
                                      [--minwait MINWAIT] [--maxwait MAXWAIT]
                                      [--maxdowload MAXDOWLOAD] [--timeout TIMEOUT]

MTUOC program to get the links from a website.

optional arguments:
  -h, --help            show this help message and exit
  -f SITEMAPFILE, --file SITEMAPFILE
                        The file containing the links to download (the sitemap).
  -d OUTDIR, --directory OUTDIR
                        The directory where the downladed files will be stored. If not provided,
                        "download" subdirectory will be used.
  -s STRATEGY, --strategy STRATEGY
                        selenium (default) / requests.
  --nofollow            Do not follow new links.
  --minwait MINWAIT     The minimum time to wait between downloads. Default 0.
  --maxwait MAXWAIT     The maximum time to wait between downloads. Defautt 2 seconds.
  --maxdowload MAXDOWLOAD
                        The maximum number of webpages to download. Defautt 10,000.
  --timeout TIMEOUT     The timeout for Selenium. Defautt 10
```

To download the links contained in the file sitemap.txt we can write:

```
python3 MTUOC-download-from-sitemap-selenium.py -f sitemap.txt
```

As no directoy is provided, the files will be stored in a "download" directory under the current directory. We can provide an specific directory with the option -d:

```
python3 MTUOC-download-from-sitemap-selenium.py -f sitemap.txt -d webfiles
```

By default the program tries to find new links in each downloaded file. If the links are internal to the same URL, they are stored and downloaded. If you want to download only the pages in the sitemap and don't want to discover and follow new links, use the option --nofollow.

```
python3 MTUOC-download-from-sitemap-selenium.py -f sitemap.txt --nofollow
```


# 5. MTUOC-downloadedweb2text.py

This programs convert the downloaded files (htmls, pdfs and docx) to segmented text. It converts all the text in a given language into a single text file. Using the -h option you can get the help of the program:

```
python3 MTUOC-downloadedweb2text.py -h
usage: MTUOC-downloadedweb2text.py [-h] -d DIRENTRADA [-p PREFFIX] [--ldm LANGDETMODEL] [-s SRXFILE]

MTUOC program to convert a downloaded web into text.

optional arguments:
  -h, --help            show this help message and exit
  -d DIRENTRADA, --directory DIRENTRADA
                        The directory where the downladed files are stored.
  -p PREFFIX, --preffix PREFFIX
                        The preffix for the text files.
  --ldm LANGDETMODEL    The fastText language detection model. By default lid.176.bin.
  -s SRXFILE, --srx SRXFILE
                        The SRX file containing the segmentation rules. By default segment.srx.
```

For example, to convert all the files in the directori "download" into text files named converted-en.txt (for English), converted-es.txt (for Spanish), converted-fr.txt (for French) and so on, you can write:

```
python3 MTUOC-downloadedweb2text.py -d download -o converted
```

It will use the lid.176.bin language detection model, that you can download from https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin , or you can specify the language detection model with the --ldm option. By default it uses the SRX file segment.srx for segmentation, but you can specify any other SRX file with the option -s.
