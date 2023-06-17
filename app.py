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
import json


logging.info("################ Script start #################################")

with open('config/config.yml', 'r') as file:
    configyml = yaml.safe_load(file)

logging.basicConfig(filename="/logs/app.log",level=configyml["level"])
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("elastic_transport").setLevel(logging.ERROR)

ELASTIC_NODES = configyml["elastic"]["nodes"]
if not configyml["elastic"]["apiid"]:
    es = Elasticsearch(ELASTIC_NODES)

def addtoelastic(matox):
    elasticindexMonth = configyml["elastic"]["index"] + "-" + datetime.now().strftime("%Y.%m")
    for key,mato in matox.items():
        mato["@timestamp"] = datetime.utcnow()
        resp = es.index(index=elasticindexMonth, document=mato)
    es.indices.refresh(index=elasticindexMonth)

def searchelastic(matox):
    elasticindex = configyml["elastic"]["index"] + "*"
    newmatox = dict()
    for key,mato in matox.items():
        if "modelId" in mato:
            resp = es.search(index=elasticindex, query={ "bool": { "must": [ { "match_phrase": { "fullname": mato["fullname"] }},{"term": { "name_site": mato["name_site"]}},{"term": { "modelId": mato["modelId"] }}] } },sort={ "@timestamp": { "order": "desc"} },size=2)
        else:
            resp = es.search(index=elasticindex, query={ "bool": { "must": [ { "match_phrase": { "fullname": mato["fullname"] }},{"term": { "name_site": mato["name_site"]}}] } },sort={ "@timestamp": { "order": "desc"} },size=2)

        if len(resp["hits"]["hits"]) >= 1:
            NewPrice = mato["prix"]
            ActualPrice = resp["hits"]["hits"][0]["_source"]["prix"]
            if NewPrice != ActualPrice:
                newmatox[key] = mato
            elif len(resp["hits"]["hits"]) >= 2:
                OlderPrice = resp["hits"]["hits"][1]["_source"]["prix"]
                if ActualPrice != OlderPrice:
                    newmatox[key] = mato
            else:
                newmatox[key] = mato
        else:
            newmatox[key] = mato
    return newmatox

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

def PrintableMatoDiscord(mato):
    PrintableMato = str(mato["fullname"])
    if "url" in mato:
        PrintableMato += " / " + mato["url"]
    else:
        PrintableMato +=  " / " + str(mato["name_site"])
    PrintableMato +=  " ## " + str(mato["prix"])  + " -> " + str(mato["newprix"])
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
    matox = searchelastic(matox)
    addtoelastic(matox)

################################### Change détection and send mail

if args.send:

    content=""
    elasticindex = configyml["elastic"]["index"] + "*"
    maxmatox = 1000 #10000

    logging.info("Search elastic to find new price")

    ## Requête elastic pour récupérer une liste de matériel et limite sur les 3 dernières heures pour éviter les produits sans nouveau prix alors que le dernier prix enregistré avait changé
    resp = es.search(index=elasticindex, query={ "bool": { "must": [ {"range": { "@timestamp": { "gte": "now-3h/h"}}}]}}, sort={ "@timestamp": { "order": "desc"} },size=maxmatox)
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

    logging.debug("Len matox : " + str(len(matoxlist)))
    # Avoid duplicate
    matoxlist = [x for n, x in enumerate(matoxlist) if x not in matoxlist[:n]]
    ##
    logging.debug("Len matox whithout duplicate : " + str(len(matoxlist)))

    newmatoxlist = list()

    for mato in matoxlist:        
        ## Requête elastic par matériel
        if "modelId" in mato:
            resp = es.search(index=elasticindex, query={ "bool": { "must": [ { "match_phrase": { "fullname": mato["fullname"] }},{"term": { "name_site": mato["name_site"]}},{"term": { "modelId": mato["modelId"] }}] } },sort={ "@timestamp": { "order": "desc"} },size=6)
        else:
            resp = es.search(index=elasticindex, query={ "bool": { "must": [ { "match_phrase": { "fullname": mato["fullname"] }},{"term": { "name_site": mato["name_site"]}}] } },sort={ "@timestamp": { "order": "desc"} },size=6)
        if len(resp["hits"]["hits"]) <= 1:
            continue
        NewPrice = resp["hits"]["hits"][0]["_source"]["prix"]
        ActualPrice = resp["hits"]["hits"][1]["_source"]["prix"]
        #logging.debug( "Mato : " + PrintableMato(mato) + " ## " + str(ActualPrice) + " -> " + str(NewPrice) )
        if NewPrice < ActualPrice and ( resp["hits"]["hits"][0]["_source"]["variations"] or "cyclable" in resp["hits"]["hits"][0]["_source"]["name_site"]):
            content = content + PrintableMato(mato) + " ## " + str(ActualPrice) + " -> " + str(NewPrice) + "\r\n"
            ### Create new list
            tempdict = resp["hits"]["hits"][0]["_source"]
            tempdict["histoprix"] = list()
            pricee = ActualPrice
            for doc in resp["hits"]["hits"]:
                if pricee != doc["_source"]["prix"]:
                    tempdict["histoprix"].append( { "timestamp": doc["_source"]["@timestamp"] , "prix": doc["_source"]["prix"] } )
                    pricee = doc["_source"]["prix"]
            newmatoxlist.append(tempdict)

    logging.info( "Found " + str(len(content.split("##"))-1) + " new price")


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

        logging.debug("Content = " + str(content))

        if len(content) != 0:
            limitmasto = 500
            actualtootnumber = 1 
            if len(content) >= limitmasto:
                newcontent = ""
                for cont in content.split("\r\n"):
                    if len(newcontent) + len(cont) < limitmasto:
                        newcontent += cont + "\r\n"
                    else:
                        logging.info( "Send Masto toot number : " + str(actualtootnumber))
                        logging.debug( "newcontent = " + newcontent )
                        mastodon.status_post(newcontent) #, spoiler_text=subject)
                        newcontent = ""
                        actualtootnumber = actualtootnumber + 1
                if newcontent != "":
                    logging.info( "Send Masto toot number : " + str(actualtootnumber))
                    logging.debug( "newcontent = " + newcontent )
                    mastodon.status_post(newcontent) #, spoiler_text=subject)
                    newcontent = ""
                    actualtootnumber = actualtootnumber + 1
            else:
                logging.info( "Send single Masto toot")
                mastodon.status_post(content) #, spoiler_text=subject)

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

    if args.send == "discord":
        #from discord_webhook import DiscordWebhook
        from discord_webhook import DiscordWebhook, DiscordEmbed
        import time, pytz
        Found = False
        for newmatox in newmatoxlist:
            Found = False
            for kind in configyml["discord"]:
                if kind in newmatox["name_search"]:
                    Found = True
                    ## Pour envoi sur canal test
                    #configyml["discord"][kind] = "https://discordapp.com/api/webhooks/1093862613869404310/nCxY36jJCzzltRxp1w9WHQW1CW3bVEGZabEmXCtst2aHkHHAlOnMacjQLN5TB9g1VNWq"
                    ##
                    embed = DiscordEmbed(title=newmatox["fullname"],color="0fbff8",url=newmatox["url"])
                    #if thumb: embed.set_thumbnail(url = thumb)
                    embed.set_timestamp()
                    for histo in newmatox["histoprix"]:
                        date_time = datetime.strptime(histo["timestamp"], '%Y-%m-%dT%H:%M:%S.%f')
                        d = date_time.replace(tzinfo=pytz.UTC).astimezone(pytz.timezone('Europe/Paris')).strftime('%d-%m-%Y %H:%M') #:%S %Z%z')
                        #d = date_time.strftime("%d/%m/%Y, %H:%M")
                        embed.add_embed_field(name=d, value=str(histo["prix"]) +"€", inline=True)
                    embed.add_embed_field(name='Recherche', value=newmatox["name_search"], inline=False)
                    webhook = DiscordWebhook(url=configyml["discord"][kind])
                    webhook.add_embed(embed)
                    response = webhook.execute()
                    time.sleep(1)
            if not Found:
                kind = "default"
                ## Pour envoi sur canal test
                #configyml["discord"][kind] = "https://discordapp.com/api/webhooks/1093862613869404310/nCxY36jJCzzltRxp1w9WHQW1CW3bVEGZabEmXCtst2aHkHHAlOnMacjQLN5TB9g1VNWq"
                ##
                embed = DiscordEmbed(title=newmatox["fullname"],color="0fbff8",url=newmatox["url"])
                #if thumb: embed.set_thumbnail(url = thumb)
                embed.set_timestamp()
                for histo in newmatox["histoprix"]:
                    date_time = datetime.strptime(histo["timestamp"], '%Y-%m-%dT%H:%M:%S.%f')
                    d = date_time.replace(tzinfo=pytz.UTC).astimezone(pytz.timezone('Europe/Paris')).strftime('%d-%m-%Y %H:%M') #:%S %Z%z')
                    #d = date_time.strftime("%d/%m/%Y, %H:%M")
                    embed.add_embed_field(name=d, value=str(histo["prix"]) +"€", inline=True)
                embed.add_embed_field(name='Recherche', value=newmatox["name_search"], inline=False)
                webhook = DiscordWebhook(url=configyml["discord"][kind])
                webhook.add_embed(embed)
                response = webhook.execute()
                time.sleep(1)

logging.info("################ Script end #################################")