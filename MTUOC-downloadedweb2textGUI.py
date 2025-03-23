#    MTUOC-downloadedweb2text
#    Copyright (C) 2025  Antoni Oliver
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


import html2text
import os
from bs4 import BeautifulSoup
import codecs
import sys
import re
import fasttext
import html2text
from langcodes import *

import argparse

import textract

from tkinter import *
from tkinter.ttk import *
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import asksaveasfilename
from tkinter.filedialog import askdirectory

from tkinter import ttk


import tkinter 

def remove_tags(segment):
    segmentnotags=re.sub('<[^>]+>',' ',segment).strip()
    segmentnotags=re.sub(' +', ' ', segmentnotags)
    return(segmentnotags)

def arregla(text):
    textlist=text.split("\n")
    textlist2=[]
    i=0
    for t in textlist:
        try:
            if textlist[i+1].strip()[0].isupper():
                textlist2.append(t+"@SALTPARA@")
            else:
                textlist2.append(t)
        except:
            textlist2.append(t)
        i+=1
    aux="".join(textlist2)
    aux2=aux.replace("@SALTPARA@","\n")
    return(aux2)
    

#SRX_SEGMENTER
import lxml.etree
import regex
from typing import (
    List,
    Set,
    Tuple,
    Dict,
    Optional
)


class SrxSegmenter:
    """Handle segmentation with SRX regex format.
    """
    def __init__(self, rule: Dict[str, List[Tuple[str, Optional[str]]]], source_text: str) -> None:
        self.source_text = source_text
        self.non_breaks = rule.get('non_breaks', [])
        self.breaks = rule.get('breaks', [])

    def _get_break_points(self, regexes: List[Tuple[str, str]]) -> Set[int]:
        return set([
            match.span(1)[1]
            for before, after in regexes
            for match in regex.finditer('({})({})'.format(before, after), self.source_text)
        ])

    def get_non_break_points(self) -> Set[int]:
        """Return segment non break points
        """
        return self._get_break_points(self.non_breaks)

    def get_break_points(self) -> Set[int]:
        """Return segment break points
        """
        return self._get_break_points(self.breaks)

    def extract(self) -> Tuple[List[str], List[str]]:
        """Return segments and whitespaces.
        """
        non_break_points = self.get_non_break_points()
        candidate_break_points = self.get_break_points()

        break_point = sorted(candidate_break_points - non_break_points)
        source_text = self.source_text

        segments = []  # type: List[str]
        whitespaces = []  # type: List[str]
        previous_foot = ""
        for start, end in zip([0] + break_point, break_point + [len(source_text)]):
            segment_with_space = source_text[start:end]
            candidate_segment = segment_with_space.strip()
            if not candidate_segment:
                previous_foot += segment_with_space
                continue

            head, segment, foot = segment_with_space.partition(candidate_segment)

            segments.append(segment)
            whitespaces.append('{}{}'.format(previous_foot, head))
            previous_foot = foot
        whitespaces.append(previous_foot)

        return segments, whitespaces


def parse(srx_filepath: str) -> Dict[str, Dict[str, List[Tuple[str, Optional[str]]]]]:
    """Parse SRX file and return it.
    :param srx_filepath: is soruce SRX file.
    :return: dict
    """
    tree = lxml.etree.parse(srx_filepath)
    namespaces = {
        'ns': 'http://www.lisa.org/srx20'
    }

    rules = {}

    for languagerule in tree.xpath('//ns:languagerule', namespaces=namespaces):
        rule_name = languagerule.attrib.get('languagerulename')
        if rule_name is None:
            continue

        current_rule = {
            'breaks': [],
            'non_breaks': [],
        }

        for rule in languagerule.xpath('ns:rule', namespaces=namespaces):
            is_break = rule.attrib.get('break', 'yes') == 'yes'
            rule_holder = current_rule['breaks'] if is_break else current_rule['non_breaks']

            beforebreak = rule.find('ns:beforebreak', namespaces=namespaces)
            beforebreak_text = '' if beforebreak.text is None else beforebreak.text

            afterbreak = rule.find('ns:afterbreak', namespaces=namespaces)
            afterbreak_text = '' if afterbreak.text is None else afterbreak.text

            rule_holder.append((beforebreak_text, afterbreak_text))

        rules[rule_name] = current_rule

    return rules

def segmenta(cadena,srxlang,rules):
    parts=cadena.split("\n")
    resposta=[]
    for part in parts:
        segmenter = SrxSegmenter(rules[srxlang],part)
        segments=segmenter.extract()
        for segment in segments[0]:
            segment=segment.replace("’","'")
            segment=segment.replace("\t"," ")
            #segment=segment.replace("\n"," ")
            segment = " ".join(segment.split())
            resposta.append(segment)
    #resposta="\n".join(resposta)
    return(resposta)
    
def remove_wiki_markup(text):
    # Remove text within square brackets
    text = re.sub(r'\[.*?\]', '', text)
    
    # Remove text within curly braces
    text = re.sub(r'\{.*?\}', '', text)
    
    # Remove text within angle brackets
    text = re.sub(r'<.*?>', '', text)
    
    # Remove any remaining wiki markup tags
    text = re.sub(r'(\'{2,5}|\[{2}(.*?)\]{2})', '', text)
    
    return text


def go():
    
    filepreffix=E2.get()
    langdetmodel=E3.get()
    srxfile=E4.get()
    
    modelFT = fasttext.load_model(langdetmodel)

    rules = parse(srxfile)
    
    
    validLangs=rules.keys()
    direntrada=E1.get()

    h = html2text.HTML2Text()
    h.ignore_links = True
    h.body_width = 0
    createdfiles=[]
    for path, currentDirectory, files in os.walk(direntrada):
        for file in files:
            fullpath=os.path.join(path, file)
            try:
                if file.endswith(".pdf") or file.endswith(".PDF") and includepdf:
                    print("Converting PDF file:",file)
                    text = textract.process(fullpath,encoding='utf-8',extension=".pdf",method='pdftotext').decode("utf-8", "replace")
                    text=arregla(text)
                        
                elif file.endswith(".docx") or file.endswith(".DOCX"):   
                    print("Converting docx file:",file)     
                    text = textract.process(fullpath, extension='docx').decode("utf-8", "replace")
                
                
                else:
                    print("Converting html: ",file)
                    
                    content=open(fullpath,"r").read()
                    text=h.handle(content)
                
                textP=text.replace("\n"," ")
                DL1=modelFT.predict(textP, k=1)
                L1=DL1[0][0].replace("__label__","")
                LangObject=Language.get(L1)
                L1fullname=LangObject.display_name()
                print("Language detected: ", L1, L1fullname)
                if L1fullname in validLangs:
                    srxlang=L1fullname
                else:
                    srxlang="Generic"
                print("SRXLang:",srxlang)
                outfilename=filepreffix+"-"+L1+".txt"
                if outfilename in createdfiles:
                    outfile=codecs.open(outfilename,"a",encoding="utf-8")
                else:
                    outfile=codecs.open(outfilename,"w",encoding="utf-8")
                    createdfiles.append(outfilename)
                print("Writing text to: ",outfilename)
                segments=segmenta(text,srxlang,rules)
                for segment in segments:
                    if len(segment)>0:
                        segment2=segment.strip()
                        segment2=remove_wiki_markup(segment2)
                        segment2=remove_tags(segment2)
                        outfile.write(segment2+"\n")
                outfile.close()
                print("--------")
            except:
                print("ERROR",sys.exc_info())

def select_directory():
    directory = askdirectory(initialdir = ".",title = "Select the output directory.")
    E1.delete(0,END)
    E1.insert(0,directory)
    E1.xview_moveto(1)
    
def select_langdetect_model():
    infile = askopenfilename(initialdir = ".",filetypes =(("bin files","*.bin"),("All Files","*.*")),
                           title = "Select lang. detect model")
    E3.delete(0,END)
    E3.insert(0,infile)
    E3.xview_moveto(1)
    
def select_srx_file():
    infile = askopenfilename(initialdir = ".",filetypes =(("SRX files","*.srx"),("All Files","*.*")),
                           title = "Select SRX file")
    E4.delete(0,END)
    E4.insert(0,infile)
    E4.xview_moveto(1)
    

top = Tk()
top.title("MTUOC-downloadedweb2textGUI")

B1=tkinter.Button(top, text = str("Select directory"), borderwidth = 1, command=select_directory,width=18).grid(row=0,column=0)
E1 = tkinter.Entry(top, bd = 5, width=80, justify="right")
E1.grid(row=0,column=1)

L2=tkinter.Label(top, text = str("Preffix:")).grid(row=1,column=0)
E2 = tkinter.Entry(top, bd = 5, width=10, justify="left")
E2.grid(row=1,column=1, sticky="w")

B3=tkinter.Button(top, text = str("Lang. detect model"), borderwidth = 1, command=select_langdetect_model,width=18).grid(row=2,column=0)
E3 = tkinter.Entry(top, bd = 5, width=80, justify="right")
E3.grid(row=2,column=1)

B4=tkinter.Button(top, text = str("SRX file"), borderwidth = 1, command=select_srx_file,width=18).grid(row=4,column=0)
E4 = tkinter.Entry(top, bd = 5, width=80, justify="right")
E4.grid(row=4,column=1)

L5=tkinter.Label(top, text = str("Convert pdfs:")).grid(row=5,column=0)
convertPDF = tkinter.IntVar()
CB5 = tkinter.Checkbutton(top, text="", variable=convertPDF)
CB5.grid(row=5,column=1,sticky="w")

B4=tkinter.Button(top, text = str("Convert!"), borderwidth = 1, command=go,width=14).grid(sticky="W",row=6,column=0)

top.mainloop()




            


