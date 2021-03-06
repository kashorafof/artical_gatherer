from bs4 import BeautifulSoup, SoupStrainer
import requests
import httplib2
import os
from os.path import exists
import time
import final_res as FS
from mainConfig import *
import functions as Fun
import json

def extractLinks():
    for website_name, link in website_list.items():
        path = result_path + '/'+website_name
        if not os.path.exists(path):
            os.makedirs(path)
        if not os.path.exists(path + '/texts'):
            os.makedirs(path+ '/texts')

        if not os.path.exists(path+"/"+website_name+"_Links.txt"):
            outFile = open(path+"/"+website_name+"_Links.txt", "w+")
            newList = ''
        else :
            outFile = open(path+"/"+website_name+"_Links.txt", "r+")
            newList = outFile.read()

        s = scrapLinks(link)
        
        newList = set(newList.split('\n'))
        newList.remove('')
        
        for x in s:
            newLink = ''
            if x.lower().endswith(forbidden_ends):
                continue
            if website_name == 'The New York Daily News' and not x.endswith('html'):
                continue
            if website_name == 'bbc' and  x.startswith('/') and '-' in x :
                newLink = link + x[1:] 
            if x.startswith('/news') and '-' in x  :
                newLink = link + x[1:] 
            if website_name == 'New York Post' and not x.startswith('https://nypost.com/2022'):
                continue
            if x.startswith(link) and '-' in x and len(x) >60:
                newLink = x 
            
            if newLink != '' and not newLink in newList :
                newList.add(newLink)
            
        outFile = open(path+"/"+website_name+"_Links.txt", "w+")
        for x in newList:
            outFile.write(x + "\n")
        outFile.close()

def scrapLinks(link):

    headers = requests.utils.default_headers()
    headers.update(
        {
            'User-Agent': 'My User Agent 1.0',
        }
    )

    url_extract = requests.get(link, headers= headers).text
    s = ""
    if link == "https://nypost.com/":
        link = link + "20"
    soup = BeautifulSoup(url_extract, )
    texts = soup.find_all('a')
    for L in texts:
        s+= str(L)
    s = set(s.split('"'))

    return s


def scrapArticles():
    save_point_dict = Fun.load(links_save_point_location)

    for website_name in website_list.keys():
        save_point = int(save_point_dict[website_name])
        website_time = time.time()
        inFile = open(result_path + '/' +website_name+'/'+website_name+"_Links.txt", "r")
        links = inFile.readlines()


        if len(links) <= save_point:
            continue
        i = 0
        for n in links:
            n = n.strip()

            i += 1
            if i < save_point:
                continue

            print(website_name, i)
            text,genre = scrapText(n.strip())
            if(genre == 'discard'):
                continue

            path = result_path + '/' + website_name + '/texts/' + genre
            if not os.path.exists(path):
                os.makedirs(path)
            
            num_files = len(os.listdir(path)) 

            outFile = open(path + '/'+ str(num_files)  +".txt", "w+" , encoding='utf-8' )

            outFile.write(text)
            outFile.close()

        print(time.time() - website_time)
        save_point_dict[website_name] = len(links)
        Fun.save(links_save_point_location, save_point_dict)
        

def scrapText(link):

    start = time.time()
    headers = requests.utils.default_headers()

    headers.update(
        {
            'Content-Type': 'application/json',
            'User-Agent': 'My User Agent 1.0',
        }
    )

    url_extract = requests.get(link, headers=headers).text
    soup = BeautifulSoup(url_extract,"html.parser" )
    texts = soup.find_all('p')
    s = ""
    
    before_merge = time.time()
    for text in texts:
        s = s + text.text + "\n"
    if len(s) < min_article_length:
        return s, 'discard'
    before_categories = time.time()
    genre , chance = FS.predict_from_text(s)
    if chance < minGenrePercent:
        genre = "other"
    print(before_merge-start, time.time()-before_categories, 'Total: ' + str(time.time()-start), genre ,chance)
    return s, genre



def flatten(list_of_lists):
    return [item for sublist in list_of_lists for item in sublist]

def jsonScrapFrom(path):
    return [json.load(open(path + file , encoding= 'UTF-8', errors='replace')) for file in os.listdir(path) if file.endswith('.json')]

def jsonScrap(categ):
    path = data_set_path 
    if categ == categories[-1]:
        folders = ['travel/', 'world/']
        
        txt = [jsonScrapFrom(path + folder) for folder in folders]
        return flatten(txt)
    path += categ + '/'
    return jsonScrapFrom(path)
