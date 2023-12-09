# Purpose

This script have severals steps : 
1. __Web crawl__ everals website (cf Managed Website below) with simple http request (like wget) or with more complexe request to be like a real human (use of selenium lib).
2. __Store__ in a python __dict__
3. __Store in elastic cluster__ in case the price has change (up or down)
4. __Create alerts__ in case of a degrease price of more than 20% by mail, mattermost or Discord. For now, Discord is for me the best and simplest one.

__Requirements to run :__ 
* [require] Docker service on a dedicated and always running VM/server
* [require] Elastic cluster to store price (and add config in config.yml)
* [optionnal] Discord webhook
* [optionnal] Mastodon account
* [optionnal] Mail account

# Managed website

* deporvillage.fr
* decathlon.fr
* cyclable.com
* probikeshop.fr
* bikester.fr
* culturevelo.com
* alltricks.fr
* bike24.fr

# Files details

## app.py

The main script that mainly manage the 4 phases describe in purpose part.

## conf/config.yml

Permit to manage all variable that can vary like : 
* Mail
* Mastodon
* Discord
* List of web pages to survey

## lib/site.py & conf/site.yml

`site.py` is the lib to manage crawling with the tag defined in `site.yml`. <br>
This lib is a try to be more generic as possible but need to adapt to specific website.

## survey.py

Permit to check if there is still data injected in Elastic Cluster from list `config.yml` -> "tosurvey".

## Dockers

`Dockerfile` and `docker-compose.yml̀` permit to create a container with all package and python lib `requirements.txt`.