#!/usr/bin/env python
# encoding: utf-8
#import requests
#import bs4
from urllib.parse import urlparse
from elasticsearch import Elasticsearch
from datetime import datetime
import time
import yaml #pyyaml
#import re
#import random
import json
import logging
from lib import sites

from smtplib import SMTP_SSL as SMTP
from email.mime.text import MIMEText

with open('config/config.yml', 'r') as file:
    configyml = yaml.safe_load(file)

logging.basicConfig(filename="/logs/app.log",level=configyml["level"])
#logging.basicConfig(filename="/logs/app.log",level="DEBUG")
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("elastic_transport").setLevel(logging.ERROR)

logging.info("################ Script start #################################")

#logging.info("Load site info")

#with open('site.yml', 'r') as file:
#    siteyml = yaml.safe_load(file)

ELASTIC_NODES = configyml["elastic"]["nodes"]
if not configyml["elastic"]["apiid"]:
    es = Elasticsearch(ELASTIC_NODES)

elasticindex = configyml["elastic"]["index"]

def addtoelastic(matox):
    for key,mato in matox.items():
        mato["@timestamp"] = datetime.utcnow()
        resp = es.index(index=elasticindex, document=mato)

def PrintableMato(mato):
    PrintableMato = " - name_site = " + str(mato["name_site"]) + " / fullname = " + str(mato["fullname"]) 
    if "modelId" in mato:
        PrintableMato += " / Id = " + str(mato["modelId"])
    if "url" in mato:
        PrintableMato += " / URL = " + mato["url"]
    return PrintableMato

for name_search,URL in configyml["tosurvey"].items():

    name_site = urlparse(URL).netloc.replace("www.","")
    logging.info("name site = " + name_site + " / name_search=" + name_search + " / URL=" + URL)

    matox = dict()

    if name_site == "decathlon.fr":
        matox = sites.sites(URL,name_site).decathlon(name_search)
        addtoelastic(matox)
        logging.debug(matox)
        continue
    else:
        matox = sites.sites(URL,name_site).generic(name_search)
    #response = requests.get(URL, headers=headers)
    #soup = bs4.BeautifulSoup(response.text, "html.parser")
    #name_tree_tag = siteyml[name_site]["name_tree"].split(',')
    #products = soup.find_all(name_tree_tag[0], attrs={name_tree_tag[1]:name_tree_tag[2]})

    logging.debug(matox)
    addtoelastic(matox)
    #exit()

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

# Avoid duplicate
matoxlist = [x for n, x in enumerate(matoxlist) if x not in matoxlist[:n]]
#logging.debug(matoxlist)

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
        #logging.debug("Mato : " + str(mato) + " disapear")
        continue #break
    NewPrice = resp["hits"]["hits"][0]["_source"]["prix"]
    ActualPrice = resp["hits"]["hits"][1]["_source"]["prix"]
    #fullname = resp["hits"]["hits"][0]["_source"]["fullname"]
    logging.debug( "Mato : " + PrintableMato(mato) + " / ActualPrice : " + str(ActualPrice) + " / NewPrice : " + str(NewPrice) )
    if NewPrice != ActualPrice:
        content = content + PrintableMato(mato) + " : Price change : From " + str(ActualPrice) + " to " + str(NewPrice) + "\r\n"

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