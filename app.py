#!/usr/bin/env python
# encoding: utf-8
#import requests
#import bs4
from urllib.parse import urlparse
from elasticsearch import Elasticsearch
from datetime import datetime
#import time
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
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("elastic_transport").setLevel(logging.ERROR)

logging.info("################ Script start #################################")

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
        #addtoelastic(matox)
        #logging.debug(matox)
        #continue
    elif name_site == "fr.aliexpress.com":
        matox = sites.sites(URL,name_site).aliexpress(name_search)
    else:
        matox = sites.sites(URL,name_site).generic(name_search)

    logging.debug(matox)
    #exit()
    addtoelastic(matox)

################################### Change détection and send mail

es.indices.refresh(index=elasticindex)

SMTPserver = configyml["mail"]["smtp"]
sender = "'" + configyml["mail"]["sender"] + "'"
destination = configyml["mail"]["recipient"]
USERNAME = configyml["mail"]["login"]
PASSWORD = configyml["mail"]["password"]
text_subtype = 'plain'
subject="Evolution prix"
content=""

## Requête elastic pour récupérer une liste de matériel
resp = es.search(index=elasticindex, sort={ "@timestamp": { "order": "desc"} },size=1500)
matoxlist = list()
for mato in resp["hits"]["hits"]:
    matoxdict = dict()
    matoxdict["fullname"] = mato["_source"]["fullname"]
    matoxdict["name_site"] = mato["_source"]["name_site"]
    if "modelId" in mato["_source"]:
        matoxdict["modelId"] = mato["_source"]["modelId"]
    if "url" in mato["_source"]:
        matoxdict["url"] = mato["_source"]["url"]
    matoxlist.append(matoxdict)

# Avoid duplicate
matoxlist = [x for n, x in enumerate(matoxlist) if x not in matoxlist[:n]]

for mato in matoxlist:        
    ## Requête elastic par matériel
    if "modelId" in mato:
        resp = es.search(index=elasticindex, query={ "bool": { "must": [ { "term": { "fullname": mato["fullname"] }},{"term": { "name_site": mato["name_site"]}},{"term": { "modelId": mato["modelId"] }}] } },sort={ "@timestamp": { "order": "desc"} },size=2)
    else:
        resp = es.search(index=elasticindex, query={ "bool": { "must": [ { "term": { "fullname": mato["fullname"] }},{"term": { "name_site": mato["name_site"]}}] } },sort={ "@timestamp": { "order": "desc"} },size=2)
    if len(resp["hits"]["hits"]) <= 1:
        continue
    NewPrice = resp["hits"]["hits"][0]["_source"]["prix"]
    ActualPrice = resp["hits"]["hits"][1]["_source"]["prix"]
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
            logging.info("Send mail with this change : " + str(content))
        finally:
            conn.quit()

    except Exception as exc:
        logging.error(exc)

logging.info("################ Script end #################################")