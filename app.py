#!/usr/bin/env python
# encoding: utf-8
from urllib.parse import urlparse
from elasticsearch import Elasticsearch
from datetime import datetime
import yaml #pyyaml
import json
import logging
from lib import sites
import argparse



logging.info("################ Script start #################################")

with open('config/config.yml', 'r') as file:
    configyml = yaml.safe_load(file)

logging.basicConfig(filename="/logs/app.log",level=configyml["level"])
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("elastic_transport").setLevel(logging.ERROR)

ELASTIC_NODES = configyml["elastic"]["nodes"]
if not configyml["elastic"]["apiid"]:
    es = Elasticsearch(ELASTIC_NODES)

elasticindex = configyml["elastic"]["index"]

now = datetime.now()
elasticindexMonth = elasticindex + "-" + now.strftime("%Y.%m")


def addtoelastic(matox):
    for key,mato in matox.items():
        mato["@timestamp"] = datetime.utcnow()
        resp = es.index(index=elasticindexMonth, document=mato)

def PrintableMato(mato):
    #PrintableMato = " - name_site = " + str(mato["name_site"]) + " / fullname = " + str(mato["fullname"]) 
    PrintableMato = "- " + str(mato["fullname"])
    #if "modelId" in mato:
    #    PrintableMato += " / Id = " + str(mato["modelId"])
    if "url" in mato:
        PrintableMato += " / " + mato["url"]
    else:
        PrintableMato +=  " / " + str(mato["name_site"]) 
    return PrintableMato

def fetchwebsite():
    matoxx = dict()
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
        matoxx.update(matox)
    return matoxx

parser = argparse.ArgumentParser()
parser.add_argument('--send',
                    help='Send price change by masto or/and mail')
parser.add_argument('--fetchwebsite', action=argparse.BooleanOptionalAction)
parser.set_defaults(fetchwebsite=True)
parser.add_argument('--storeelastic', action=argparse.BooleanOptionalAction)
parser.set_defaults(storeelastic=True)

args = parser.parse_args()
#print(args)
#exit()

subject="Evolution prix"

if args.fetchwebsite:
    matox = fetchwebsite()
if args.storeelastic and matox:
    addtoelastic(matox)
    es.indices.refresh(index=elasticindexMonth)

################################### Change détection and send mail

if args.send:

    content=""
    elasticindex = elasticindex + "*"

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
        logging.debug( "Mato : " + PrintableMato(mato) + " ## " + str(ActualPrice) + " -> " + str(NewPrice) )
        if NewPrice != ActualPrice:
            content = content + PrintableMato(mato) + " ## " + str(ActualPrice) + " -> " + str(NewPrice) + "\r\n"


    if args.send == "masto":
        from mastodon import Mastodon
        Mastodon.create_app(
            'pytooterapp',
            api_base_url = configyml["masto"]["api_base_url"],
            to_file = 'pytooter_clientcred.secret'
        )

        mastodon = Mastodon(client_id = 'pytooter_clientcred.secret',)
        mastodon.log_in(
            configyml["masto"]["login"],
            configyml["masto"]["password"],
            to_file = 'pytooter_usercred.secret'
        )

        if len(content) != 0:
            limitmasto = 500
            if len(content) >= limitmasto:
                newcontent = ""
                for cont in content.split("\r\n"):
                    if len(newcontent) + len(cont) < limitmasto:
                        newcontent += cont + "\r\n"
                    else:
                        mastodon.status_post(newcontent, spoiler_text=subject)
                        newcontent = ""
            else:
                mastodon.status_post(content, spoiler_text=subject)

    if args.send == "mail":
        from smtplib import SMTP_SSL as SMTP
        from email.mime.text import MIMEText

        SMTPserver = configyml["mail"]["smtp"]
        sender = "'" + configyml["mail"]["sender"] + "'"
        destination = configyml["mail"]["recipient"]
        USERNAME = configyml["mail"]["login"]
        PASSWORD = configyml["mail"]["password"]
        text_subtype = 'plain'

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