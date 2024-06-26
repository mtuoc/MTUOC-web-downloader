#    MTUOC-download-from-sitemap-selenium
#    Copyright (C) 2023  Antoni Oliver
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

import codecs
import sys
import os



from bs4 import BeautifulSoup

import urllib.parse
import requests
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

from random import randint
from time import sleep

import argparse


from urllib.parse import urlparse
from urllib.parse import urljoin

import pathlib

def base_url(url, with_path=False):
    parsed = urllib.parse.urlparse(url)
    path   = '/'.join(parsed.path.split('/')[:-1]) if with_path else ''
    parsed = parsed._replace(path=path)
    parsed = parsed._replace(params='')
    parsed = parsed._replace(query='')
    parsed = parsed._replace(fragment='')
    return parsed.geturl()

fileextensions=[".pdf",".PDF",".doc",".docx",".odt"]
htmlextensions=[".html",".HTML","htm","HTM"]


parser = argparse.ArgumentParser(description='MTUOC program to get the links from a website.')
parser.add_argument('-f','--file', action="store", dest="sitemapfile", help='The file containing the links to download (the sitemap).',required=True)
parser.add_argument('-d','--directory', action="store", dest="outdir", help='The directory where the downladed files will be stored. If not provided, "download" subdirectory will be used.',required=False, default="download")
parser.add_argument('-s','--strategy', action="store", dest="strategy", help='selenium (default) / requests.',required=False, default="selenium")
parser.add_argument('-l','--log', action="store", dest="logfile", help='The log file to write and load.',required=False)
parser.add_argument('-e','--exclude', nargs='+', help='List of file extensions to ignore')
parser.add_argument('--nofollow', action="store_true", dest="nofollow", help='Do not follow new links.',required=False, default=False)
parser.add_argument('--minwait', action="store", dest="minwait", help='The minimum time to wait between downloads. Default 0.',required=False, default=0)
parser.add_argument('--maxwait', action="store", dest="maxwait", help='The maximum time to wait between downloads. Defautt 2 seconds.',required=False, default=2)
parser.add_argument('--maxdownload', action="store", dest="maxdowload", help='The maximum number of webpages to download. Defautt 1,000,000.',required=False, default=1000000)
parser.add_argument('--timeout', action="store", dest="timeout", help='The timeout for Selenium. Defautt 10',required=False, default=10)

args = parser.parse_args()

exclude=args.exclude
if exclude==None:
    exclude=[]



sitemapfile=args.sitemapfile
nofollow=args.nofollow
minwait=args.minwait
maxwait=args.maxwait
maxdowload=int(args.maxdowload)
outdir=args.outdir
strategy=args.strategy
timeout=args.timeout

if not strategy=="selenium" and not strategy=="requests":
    print("ERROR: Strategy should be: selenium or requests")
    sys.exit()

if not os.path.exists(outdir):
    os.makedirs(outdir)
    
if strategy=="selenium":
    from selenium import webdriver
    from selenium.webdriver import Firefox
    from selenium.webdriver.firefox.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    opts = Options()
    opts.add_argument('-headless')
    opts.accept_untrusted_certs = True
    browser = webdriver.Firefox(options=opts)
    browser.set_page_load_timeout(timeout)  

entrada=codecs.open(sitemapfile,"r",encoding="utf-8")
if args.logfile==None:
    logfilename="downloadlog-"+sitemapfile.replace("sitemap-","")
else:
    logfilename=args.logfile

linkssuccess=[]
linkserrors=[]    

if os.path.exists(logfilename):
    entradalog=codecs.open(logfilename,"r",encoding="utf-8")
    for linia in entradalog:
        linia=linia.rstrip()
        camps=linia.split("\t")
        if camps[0]=="SUCCESS":
            linkssuccess.append(camps[1])
        elif camps[1]=="ERROR":
            linkserrors.append(camps[1])
    entradalog.close()

sortidalog=codecs.open(logfilename,"a",encoding="utf-8")

links=[]
done=[]


for linia in entrada:
    linia=linia.rstrip()
    if not linia in links and not linia.startswith("#"):
        links.append(linia)

links.extend(linkserrors)
links = [x for x in links if x not in linkssuccess]


contreplace=0
moreelements=len(links)
totaldownloaded=0
while moreelements>0:
    cadenalog=[]
    try:
        
        link=links.pop(0)
        done.append(link)
        baseurl=base_url(link)
        domain = urlparse(link).netloc
        camps=os.path.split(link)
        filename=camps[-1]
        dirs=camps[0].replace(baseurl,"").split("/")[1:]
        dir1=os.path.join(outdir,domain,"/".join(dirs))
        if not os.path.exists(dir1):
            os.makedirs(dir1)
        fullfilename=os.path.join(dir1,filename)
        file_extension = pathlib.Path(fullfilename).suffix
        if file_extension in fileextensions and not file_extension in exclude:
            #cadenalog.append("DOWNLOADING")
            #cadenalog.append(str(link))
            #cadenalog.append(fullfilename)
            print("DOWNLOADING: ",link," to ", fullfilename)
            response = requests.get(link, verify=False)
            document = open(fullfilename, 'wb')
            document.write(response.content)
            document.close()
            cadenalog.append("SUCCESS")
            cadenalog.append(str(link))
            cadenalog.append(fullfilename)
            cadenalog.append(strategy)
            totaldownloaded+=1
            sleep(randint(minwait,maxwait))
        else:
            print("GETTING: ",link)
            #cadenalog.append("GETTING")
            #cadenalog.append(link)
            if strategy=="selenium":
                browser.get(link)
                delay = 3
                html = browser.page_source
            elif strategy=="requests":
                response = requests.get(link, verify=False)
                page_source = response.content.decode("utf-8")
                html=page_source
            #text=h.handle(html)
            soup = BeautifulSoup(html, "lxml")
            newlinks=soup.findAll('a')
            if not nofollow:
                for l in newlinks:
                    l2=l.get('href')
                    if not l2==None and l2.startswith("/"):
                        l2=urljoin(baseurl,l2)
                    if not l2==None and l2.startswith(baseurl):
                        if not l2 in links and not l2 in done:
                            print("NEWLINK:",l2)
                            links.append(l2)
            file_extension = pathlib.Path(fullfilename).suffix
            
            if not file_extension in htmlextensions:
                fullfilename=fullfilename+".html"
            fullfilename=fullfilename.replace("?","_").replace("<","_")
            if len(fullfilename)>256:
                filename="replaced_filename_"+str(contreplace)+".html"
                fullfilename=os.path.join(dir1,filename)
                contreplace+=1
                
            #cadenalog.append(fullfilename)
            sortida=codecs.open(fullfilename,"w",encoding="utf-8")
            sortida.write(html+"\n")
            sortida.close()
            cadenalog.append("SUCCESS")
            cadenalog.append(str(link))
            cadenalog.append(fullfilename)
            cadenalog.append(strategy)
            totaldownloaded+=1
            sleep(randint(minwait,maxwait))
        print("DONE: ",str(len(done)),"TO DOWNLOAD:",str(moreelements))
    
    except:
        print("ERROR:",sys.exc_info())
        cadenalog.append("ERROR")
        cadenalog.append(str(link))
        cadenalog.append(fullfilename)
        cadenalog.append(strategy)
        cadenalog.append(str(sys.exc_info()[0]))
    moreelements=len(links)
    cadenalog="\t".join(cadenalog)
    sortidalog.write(cadenalog+"\n")
    sortidalog.close()
    sortidalog=codecs.open(logfilename,"a",encoding="utf-8")
    if totaldownloaded>=maxdowload:
        sys.exit()
sortidalog.close()    

    
    
    
    
    
