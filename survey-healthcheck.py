import yaml
from elasticsearch import Elasticsearch

with open('config/config.yml', 'r') as file:
    configyml = yaml.safe_load(file)

searchsite = list()

for name_search in configyml["tosurvey"]:
    site = name_search.split("-")[0]
    if not site in searchsite:
        searchsite.append(site)

print(searchsite)

elasticindex = configyml["elastic"]["index"] + "*" #"prix-test*"
ELASTIC_NODES = configyml["elastic"]["nodes"]
if not configyml["elastic"]["apiid"]:
    es = Elasticsearch(ELASTIC_NODES)

missing = list()

for site in searchsite:
    resp = es.search(index=elasticindex, query={ "bool": { "must": [ { "prefix": { "name_site": site } }, { "range": { "@timestamp": { "gte": "now-1d/d", "lte": "now/d" } } } ] } },size=1)
    #resp = es.search(index=elasticindex, query={ "bool": { "must": [ { "prefix": { "name_site": site } }, { "range": { "@timestamp": { "gte": "now-10h/h", "lte": "now/h" } } } ] } },size=1)
    #print(resp)
    if len(resp["hits"]["hits"]) >= 1:
        print(site + " : Found !")
    else:
        print(site + " : Not found !")
        missing.append(site)
    #print(resp)

if missing:
    from discord_webhook import DiscordWebhook, DiscordEmbed 
    urllog = "https://discordapp.com/api/webhooks/1093862613869404310/nCxY36jJCzzltRxp1w9WHQW1CW3bVEGZabEmXCtst2aHkHHAlOnMacjQLN5TB9g1VNWq"
    webhook = DiscordWebhook(url=urllog, content="Missing = " + (" / ").join(missing))
    response = webhook.execute()