#!/usr/bin/env python
# encoding: utf-8
import requests
import bs4
from urllib.parse import urlparse
from elasticsearch import Elasticsearch
from datetime import datetime
import time
import yaml #pyyaml
import re
import random
import json
import logging
from lib import sites

from smtplib import SMTP_SSL as SMTP
from email.mime.text import MIMEText

with open('config.yml', 'r') as file:
    configyml = yaml.safe_load(file)

logging.basicConfig(filename="/logs/app.log",level=configyml["level"])
#logging.basicConfig(filename="/logs/app.log",level="DEBUG")
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("elastic_transport").setLevel(logging.ERROR)

logging.info("################ Script start #################################")

logging.info("Load site info")

with open('site.yml', 'r') as file:
    siteyml = yaml.safe_load(file)

ELASTIC_NODES = configyml["elastic"]["nodes"]
if not configyml["elastic"]["apiid"]:
    es = Elasticsearch(ELASTIC_NODES)

elasticindex = configyml["elastic"]["index"]

headers_list = [{
	'authority': 'httpbin.org', 
	'cache-control': 'max-age=0', 
	'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"', 
	'sec-ch-ua-mobile': '?0', 
	'upgrade-insecure-requests': '1', 
	'user-agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:107.0) Gecko/20100101 Firefox/107.0', 
	'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9', 
	'sec-fetch-site': 'none', 
	'sec-fetch-mode': 'navigate', 
	'sec-fetch-user': '?1', 
	'sec-fetch-dest': 'document', 
	'accept-language': 'en-US,en;q=0.9', 
} # , {...} 
]
'''
headers_list = [{
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3",
    "Connection": "keep-alive",
    "Cookie": "visid_incap_989938=+V1vK2FCToyagUNWSg9zVKpaKmIAAAAAQUIPAAAAAACm/HQVk4zfjNaKSzkxjOZl; NFS_USER_ID=71deb699-3d48-4fbc-99aa-7fd69b45b7f6; CUSTOMER_LVP=4231289--4341863; DKT_SESSION=EbPKCq7d/daaFXVLJHYrMFWgGs1kCIQcSXyE8UCM8LWwkILr2/eKh1j+Ab2bMm6+w3nE9cM4E81NYkYtmjR6VMdKIzObrLh6vYuISWOdZeAO8EtR67Grejhu3S8g/g2AGSG0TXIjmwXU/0JcuY6nccmis/AxLDqH2tUthGf4EBQ=; didomi_token=eyJ1c2VyX2lkIjoiMTg0ZmRlODQtMWY1MS02OTFlLTgwNGItOWE1MTE4NmE4ODQ0IiwiY3JlYXRlZCI6IjIwMjItMTItMTBUMjE6MTk6MzAuMDQwWiIsInVwZGF0ZWQiOiIyMDIyLTEyLTEwVDI…V0005QIcywUQQqKQ==; incap_ses_391_989938=gvuCIMiMG2JM5i25JR1tBZjdomMAAAAAUa60Io/WVfOdsvIdWkDG+Q==; incap_ses_1175_989938=nTvZZjH6JHiR/q1b/nBOEJndomMAAAAA9zt3j79lHNOtEIblhKoBUQ==; incap_ses_464_989938=0kVIfhkRZVJ73OBGY3ZwBprdomMAAAAA1T5C2xWs/BUu1iKLdqiP6Q==; incap_ses_1176_989938=pNc+BeRk9WoUJFd3Of5REJrdomMAAAAARGUIx+xV3ZfkYObz50Ymdg==; incap_ses_1517_989938=fbVhcjTQ5SvKDzUIz3cNFavdomMAAAAAlrthMPliTL6d8Frd+b/uvA==; ACTIVE_USER=y; incap_ses_1543_989938=4bQ4JNBU/VEhpRiGlNZpFZniomMAAAAAO3jTLvgfnzrNl5lDya/S+A==",
    "DNT": "1",
    "Host": "www.decathlon.fr",
    "Referer": "https://www.decathlon.fr/search?Ntt=tribord+sailing+500",
    "Sec-Fetch-Dest": "script",
    "Sec-Fetch-Mode": "no-cors",
    "Sec-Fetch-Site": "same-origin",
    "Sec-GPC": "1",
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:107.0) Gecko/201001",
    "Content-Type": "text/html; charset=utf-8",
}
]
'''

headers = random.choice(headers_list)

def trim_the_ends(x):
    """
    Returns a string with space on the left and right removed.
    """
    try:
        x = x.strip(' \t\n\r')
        #x = x.strip('\n')
    except:
        pass
    return x

def remove_blank_list(x):
    """
    Returns a string with space on the left and right removed.
    """
    try:
        y = list()
        for xi in x:
            y.append(xi.replace(" ", ""))
    except:
        pass
    return y

for name_search,URL in configyml["tosurvey"].items():
    name_site = urlparse(URL).netloc.replace("www.","")
    logging.info("name site = " + name_site + " / name_search=" + name_search + " / URL=" + URL)
    response = requests.get(URL, headers=headers)
    soup = bs4.BeautifulSoup(response.text, "html.parser")
    
    name_tree_tag = siteyml[name_site]["name_tree"].split(',')
    
    matox = dict()

    if name_site == "decathlon.fr":
        products = soup.find_all(name_tree_tag[0], attrs={name_tree_tag[1]:name_tree_tag[2]})
        matox = sites.decathlon().baseonjavascript(products,name_site,name_search)
        #logging.debug(matox)
        #exit()
        continue

    price_tag = siteyml[name_site]["price"].split(',')
    price_sale_tag = siteyml[name_site]["price_sale"].split(',')
    name_tag = siteyml[name_site]["name"].split(',')
    marque_tag = siteyml[name_site]["marque"].split(',')
    variations_tag = siteyml[name_site]["variations"].split(',')
    if siteyml[name_site]["number_articles"]:
        number_articles = siteyml[name_site]["number_articles"].split(',')
        number_articles = int(trim_the_ends(soup.find(number_articles[0], attrs={number_articles[1]:number_articles[2]}).contents[0].replace("Articles","")))
    else:
        number_articles = 1

    i = 1
    while len(matox) < number_articles:
        if "page" in URL and i > 1:
            URL = re.sub("page=[0-9]*", "page=" + str(i), URL)
            logging.info("URL=" + str(URL))
            response = requests.get(URL, headers=headers)
            soup = bs4.BeautifulSoup(response.text, "html.parser")

        products = soup.find_all(name_tree_tag[0], attrs={name_tree_tag[1]:name_tree_tag[2]})

        if not products:
            print("Error: No products found !")
            print(response.text)
            continue #exit()

        TypesInName = ['Vélo de Randonnée']

        for product in products:
            logging.debug("product = " + str(product))
            if len(marque_tag) > 1:
                marque = trim_the_ends( product.find(marque_tag[0], attrs={marque_tag[1]:marque_tag[2]}) )
                if name_site == "probikeshop.fr" and marque:
                    for marquee in marque:
                        marque = marquee
                elif name_site == "bikester.fr" and marque:
                    marque = trim_the_ends( product.find(marque_tag[0], attrs={marque_tag[1]:marque_tag[2]}).contents[0] )
            else:
                marque = "Inconnu" #Cas probikeshop
            name = trim_the_ends( product.find(name_tag[0], attrs={name_tag[1]:name_tag[2]}).contents[0] )
            for TypeInName in TypesInName:
                name = name.replace(TypeInName + " ","")
            if marque == "Inconnu": #Try to get from name
                marque = name.split(" ")[0]
                if marque == "VSF":
                    marque = "VSF FAHRRADMANUFAKTUR"
                name = name.replace(marque + " ","")
            prix = product.find(price_tag[0], attrs={price_tag[1]:price_tag[2]})
            if len(prix) == 1:
                prix = trim_the_ends( prix.contents[0] ).encode('ascii','ignore').decode()
            else:
                prix = trim_the_ends( prix.contents[2] ).encode('ascii','ignore').decode()
            if prix == "PVC" or prix == "" or prix == "*" and price_sale_tag != "":
                prix = trim_the_ends( product.find(price_sale_tag[0], attrs={price_sale_tag[1]:price_sale_tag[2]}).contents[0] )
            if prix and type(prix) == str:
                prix = prix.replace(" €", "")
                prix = prix.replace("€", "")
                prix = prix.replace(".","")
                prix = prix.replace(",",".")
            if prix == "N/A":
                prix = ""
            variations = product.find(variations_tag[0], attrs={variations_tag[1]:variations_tag[2]})
            if name_site == "bikester.fr":
                if variations:
                    if variations.find("span"):
                        variations = product.find(variations_tag[0], attrs={variations_tag[1]:variations_tag[2]}).find_all("span")
                        variationlist = list()
                        for variation in variations:
                            variationlist.append(variation.contents[0])
                        variations = variationlist
                    else:
                        variations = ""
                else:
                    variations = ""
            if name_site == "probikeshop.fr":
                if variations:
                    variations = remove_blank_list( trim_the_ends(variations.contents[0]).split(",") )
            #if variations != "":
            #    matox[marque + " " + name] = {"marque":marque, "name":name, "prix":prix, "variations":variations, "name_search":name_search, "name_site":name_site, "fullname":marque + " " + name}
            if marque + " " + name in matox:
                id = str(random.randrange(0, 50000, 5))
                matox[marque + " " + name + " " + id] = {"marque":marque, "name":name, "prix":prix, "variations":variations, "name_search":name_search, "name_site":name_site, "fullname":marque + " " + name}
                #print(matox[marque + " " + name + " " + id])
            else:
                matox[marque + " " + name] = {"marque":marque.lower(), "name":name.lower(), "prix":prix, "variations":variations, "name_search":name_search, "name_site":name_site, "fullname":marque.lower() + " " + name.lower()}
                #print(matox[marque + " " + name])
            ## Récupération de l'ID produit qui change pour le cas de même nom de pduit : exemple : Ortler Bozen Trapèze, rouge : Année 2021 et 2022
            #  1319869 dans le code : 
            # <div id="5899e52714c17e73464b7fd54b" data-productid="G1319869" data-masterid="M920128" class="js-product-tile-lazyload gtm-producttile product-tile product-tile--sale uv-item   " data-uv-item={&quot;id&quot;:&quot;1319869&quot;,&quot;unit_sale_price&quot;:2239} data-gtm-productdata="{&quot;name&quot;:&quot;Ortler Bozen Trapèze, rouge&quot;,&quot;id&quot;:&quot;1319869&quot;,&quot;brand&quot;:&quot;Ortler&quot;,&quot;price&quot;:1865.83,&quot;dimension42&quot;:&quot;Available&quot;,&quot;dimension51&quot;:4.8,&quot;dimension43&quot;:&quot;rouge&quot;,&quot;dimension62&quot;:&quot;10.4&quot;,&quot;dimension49&quot;:&quot;2499&quot;,&quot;dimension50&quot;:&quot;true&quot;,&quot;metric2&quot;:260,&quot;metric4&quot;:2499,&quot;metric7&quot;:1,&quot;metric8&quot;:0,&quot;variant&quot;:&quot;45cm (28\&quot;)&quot;,&quot;dimension53&quot;:&quot;45cm (28\&quot;)&quot;}">
            #
        i = i + 1
    logging.debug(matox)

    for key,mato in matox.items():
        mato["@timestamp"] = datetime.utcnow()
        resp = es.index(index=elasticindex, document=mato)

################################### Change détection and send mail

time.sleep(5) #To avoid no index of actual data indexes

SMTPserver = configyml["mail"]["smtp"]
sender = "'" + configyml["mail"]["sender"] + "'"
destination = configyml["mail"]["recipient"]
USERNAME = configyml["mail"]["login"]
PASSWORD = configyml["mail"]["password"]
text_subtype = 'plain'
subject="Evolution prix"
content=""

## Requête elastic pour récupérer une liste de matériel
resp = es.search(index=elasticindex, sort={ "@timestamp": { "order": "desc"} },size=1000)
matoxlist = list()
for mato in resp["hits"]["hits"]:
    matoxdict = dict()
    #matoxlist.append(mato["_source"]["fullname"]) # + "-" + mato["_source"]["name_site"] + "-" + mato["_source"]["modelId"])
    matoxdict["fullname"] = mato["_source"]["fullname"]
    matoxdict["name_site"] = mato["_source"]["name_site"]
    if "modelId" in mato["_source"]:
        matoxdict["modelId"] = mato["_source"]["modelId"]
    #else:
    #    matoxdict["modelId"] = ""
    if "url" in mato["_source"]:
        matoxdict["url"] = mato["_source"]["url"]
    matoxlist.append(matoxdict)

#matoxlist_set = set(matoxlist)
#matoxlist = (list(matoxlist_set))
for mato in matoxlist:        
    ## Requête elastic par matériel
    #resp = es.search(index=elasticindex, query={ "bool": { "should": { "term": { "fullname": mato } }}},sort={ "@timestamp": { "order": "desc"} },size=2)
    if "modelId" in mato:
        resp = es.search(index=elasticindex, query={ "bool": { "must": [ { "term": { "fullname": mato["fullname"] }},{"term": { "name_site": mato["name_site"]}},{"term": { "modelId": mato["modelId"] }}] } },sort={ "@timestamp": { "order": "desc"} },size=2)
    else:
        resp = es.search(index=elasticindex, query={ "bool": { "must": [ { "term": { "fullname": mato["fullname"] }},{"term": { "name_site": mato["name_site"]}}] } },sort={ "@timestamp": { "order": "desc"} },size=2)
    #logging.debug(resp)
    if len(resp["hits"]["hits"]) <= 1:
        continue #break
    NewPrice = resp["hits"]["hits"][0]["_source"]["prix"]
    ActualPrice = resp["hits"]["hits"][1]["_source"]["prix"]
    #fullname = resp["hits"]["hits"][0]["_source"]["fullname"]
    logging.debug( "Mato : " + str(mato) + " / ActualPrice : " + str(ActualPrice) + " / NewPrice : " + str(NewPrice) )
    if NewPrice != ActualPrice:
        content = content + str(mato) + " : Price change : From " + str(ActualPrice) + " to " + str(NewPrice) + "\r\n"

if len(content) != 0:
    try:
        msg = MIMEText(content, text_subtype)
        msg['Subject']= subject
        msg['From']   = sender # some SMTP servers will do this automatically, not all
        conn = SMTP(SMTPserver)
        conn.set_debuglevel(False)
        conn.login(USERNAME, PASSWORD)
        try:
            conn.sendmail(sender, destination.split(','), msg.as_string())
            logging.info("Change price detect and send mail")
        finally:
            conn.quit()

    except Exception as exc:
        print(exc)

logging.info("################ Script end #################################")