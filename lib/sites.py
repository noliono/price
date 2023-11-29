import requests
import bs4
import json
import yaml
import logging
import logging.handlers
import random
import re
#import time
#import unidecode
from pyvirtualdisplay import Display
#from selenium import webdriver
from seleniumwire import webdriver
from selenium.webdriver.firefox.options import Options 

with open('config/config.yml', 'r') as file:
    configyml = yaml.safe_load(file)

#logging.basicConfig(filename="/logs/app.log",level=configyml["level"])
#logging.basicConfig(filename="/logs/app.log",level="DEBUG")
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("elastic_transport").setLevel(logging.ERROR)
logging.getLogger("seleniumwire").setLevel(logging.ERROR)

# Creates the log handler in case the default move does not work
handler = logging.handlers.RotatingFileHandler("/logs/app.log",maxBytes=2000000, backupCount=5)
handler.setFormatter(logging.Formatter(u'%(asctime)s %(levelname)-s -- %(module)s:%(lineno)d - %(message)s'))

# Creates the logger
logger = logging.getLogger("prix-app")
#logger.setLevel(configyml["level"])
#logger.addHandler(handler)

class sites():

    def __init__(self,URL,name_site):

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

        self.headers = random.choice(headers_list)
        self.name_site = name_site
        self.URL = URL
        with open('config/site.yml', 'r') as file:
            self.siteyml = yaml.safe_load(file)
        if self.name_site == "deporvillage.fr" or self.name_site == "alltricks.fr" or self.name_site == "intersport.fr" or self.name_site == "bike24.fr":
            self.bs4WithJS()
        else:
            self.response = requests.get(URL, headers=self.headers) #, allow_redirects=True)
            self.soup = bs4.BeautifulSoup(self.response.text, "html.parser")
        self.name_tree_tag = self.siteyml[name_site]["name_tree"].split(',')
        self.products = self.soup.find_all(self.name_tree_tag[0], attrs={self.name_tree_tag[1]:self.name_tree_tag[2]})
        #self.products = self.soup.find_all("script")

    def trim_the_ends(self,x):
        """
        Returns a string with space on the left and right removed.
        """
        try:
            x = x.strip(' \t\n\r')
            #x = x.strip('\n')
        except:
            pass
        return x

    def remove_blank_list(self,x):
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

    def decathlon(self,name_search):
        matox = dict()

        if len(self.products) != 0:
            datas = json.loads(self.products[0].contents[0].replace("__DKT = ",""))["_ctx"]["data"]
            #print(json.dumps(json.loads(self.products[0].contents[0])))
            #print(json.dumps(datas))
            #print(json.dumps(datas[5]["data"]["blocks"]["items"]))
            #exit()
            if "data" in datas[5] and "blocks" in datas[5]["data"]:
                items = datas[5]["data"]["blocks"]["items"]
            else:
                items=[]

            while len(items) != 0 and len(self.products[0].contents) != 0:

                #print(self.URL)            
                
                #print(json.dumps(items))
                for kk in items:
                    marque = kk["brand"]["label"]
                    #supermodelId = kk["models"][0]["modelId"]
                    for kkk in kk["models"]:
                        supermodelId = kkk["modelId"]
                        if "webLabel" in kkk: 
                            name = kkk["webLabel"]
                        else: 
                            name = ""
                        prix = kkk["price"]
                        variations = kkk["availableSizes"]
                        url = "https://" + self.name_site + "/" + kkk["url"]
                        matox[marque + " " + name + "-" + supermodelId] = {"marque":marque.lower(), "name":name.lower(), "prix":prix, "variations":variations, "name_search":name_search, "name_site":self.name_site, "fullname":marque.lower() + " " + name.lower(), "modelId":supermodelId, "url":url}

                pattern = re.compile(r"from=(\d+)&size=(\d+)")
                newstart = int(pattern.search(self.URL).group(1)) + int(pattern.search(self.URL).group(2))
                self.URL = re.sub(r"from=\d+", "from=" + str(newstart), self.URL)
                logger.info("URL=" + str(self.URL))
                self.response = requests.get(self.URL, headers=self.headers)
                self.soup = bs4.BeautifulSoup(self.response.text, "html.parser")
                self.products = self.soup.find_all(self.name_tree_tag[0], attrs={self.name_tree_tag[1]:self.name_tree_tag[2]})            
            
                items = list()

                #print(len(self.products))
                #print(len(self.products))
                if len(self.products) != 0:
                    #datas = json.loads(self.products[0].contents[0])["_ctx"]["data"]
                    datas = json.loads(self.products[0].contents[0].replace("__DKT = ",""))["_ctx"]["data"]
                    if "data" in datas[5] and "blocks" in datas[5]["data"]:
                        items = datas[5]["data"]["blocks"]["items"]
                    else:
                        items=[]
                
                #print(items)


            '''
            jsonresult = json.loads(self.products[0].contents[0])
            for key in jsonresult["_ctx"]["data"]:
                if "Super" in key["id"]:
                    for kk in key["data"]["blocks"]["items"]:
                        marque = kk["brand"]["label"]
                        supermodelId = kk["supermodelId"]
                        for kkk in kk["models"]:
                            name = kkk["webLabel"]
                            prix = kkk["price"]
                            variations = kkk["availableSizes"]
                            url = "https://" + self.name_site + "/" + kkk["url"]
                            matox[marque + " " + name + "-" + supermodelId] = {"marque":marque.lower(), "name":name.lower(), "prix":prix, "variations":variations, "name_search":name_search, "name_site":self.name_site, "fullname":marque.lower() + " " + name.lower(), "modelId":supermodelId, "url":url}
            '''
        return matox

    def bs4WithJS(self):

        display = Display(visible=0, size=(800, 600))
        display.start()
        options = Options() 
        options.add_argument("-headless")
        #options.add_argument("--lang=fr-FR")
        driver = webdriver.Firefox(options=options)
        driver.request_interceptor #= self.interceptor
        driver.get(self.URL)
        if self.name_site == "alltricks.fr" or self.name_site == "intersport.fr":
            from selenium.webdriver.common.by import By
            from PIL import Image #pip install Pillow
            import time
            SCROLL_PAUSE_TIME = 10
            # Get scroll height
            last_height = driver.execute_script("return document.body.scrollHeight")

            #<div id="didomi-popup" class="didomi-popup-backdrop didomi-notice-popup didomi-popup__backdrop"
            #driver.save_screenshot("image1.png")
            #if driver.find_element(By.ID, 'didomi-notice-agree-button'):
            try:
                driver.find_element(By.ID, 'didomi-notice-agree-button').click()
            except:
                logger.debug('No popup Cookie')
            #driver.save_screenshot("image2.png")
            #if driver.find_element(By.CLASS_NAME, 'locale-redirect-popin'):
            try:
                driver.find_element(By.CLASS_NAME, 'close-btn').click()
            except:
                logger.debug('No popup lang')
            #driver.save_screenshot("image3.png")
            #exit()

            while True:
                # Scroll down to bottom
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                # Wait to load page
                time.sleep(SCROLL_PAUSE_TIME)

                # Calculate new scroll height and compare with last scroll height
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    if self.name_site == "alltricks.fr":
                        #class="alltricks-Pager__Waypoint alltricks-Pager__Waypoint--WaitClick"
                        #logger.debug( driver.find_element(By.CLASS_NAME, 'alltricks-Pager__Waypoint') )
                        #driver.save_screenshot("image1.png")
                        #print( driver.find_element(By.CLASS_NAME, 'alltricks-Pager__Waypoint--WaitClick') )
                        try:
                            #driver.find_element(By.CSS_SELECTOR, 'div.class.alltricks-Pager__Waypoint.alltricks-Pager__Waypoint--WaitClick')
                            driver.find_element(By.CLASS_NAME, 'alltricks-Pager__Waypoint--WaitClick')
                        #driver.find_elements(By.XPATH("//div[contains(@class, 'alltricks-Pager__Waypoint--WaitClick')]")):
                        #if driver.find_element(By.CLASS_NAME, 'alltricks-Pager__Waypoint'):
                            #driver.save_screenshot("image1.png")
                            driver.find_element(By.CLASS_NAME, 'alltricks-Pager__Waypoint').click()
                            logger.debug("Encore des produits")
                            #driver.save_screenshot("image2.png")
                        except:
                            break
                    elif self.name_site == "intersport.fr":
                        driver.save_screenshot("image1.png")
                        break
                    #else:
                    #    break
                last_height = new_height
        
        html = driver.page_source

        driver.close()
        del driver.request_interceptor
        del driver.response_interceptor

        self.soup = bs4.BeautifulSoup(html, "html.parser") 


    def parsejson(self,name_search):
        matox = dict()

        name_tree2_tag = self.siteyml[self.name_site]["name_tree2"].split(',')
        #print(self.products[0].string)
        #print(name_tree2_tag)
        #exit()
        #print(json.loads(self.products[0].string)["props"]["pageProps"]["model"]["items"])
        myjson = json.loads(self.products[0].string)
        myitems = myjson
        for mydict in name_tree2_tag:
            myitems = myitems[mydict]
        myarti = myjson
        for tag_arti in self.siteyml[self.name_site]["number_articles"].split(','):
            myarti = myarti[tag_arti]
        
        mybrand = myjson
        for tag_arti in self.siteyml[self.name_site]["brandlist"].split(','):
            mybrand = mybrand[tag_arti]
        for my in mybrand:
            if my["id"] == 66:
                mybrand = my['options']
        mybranddict = dict()
        for my in mybrand:
            mybranddict[my['id']] = my['label']
        
        #print(mybranddict[10300])
        #exit()

        pageslist=["page=","p="]
        i = 1

        while len(myitems) != 0 and myarti > len(matox) :

            if i > 1:
                for page in pageslist:
                    if page in self.URL:
                        self.URL = re.sub(page+"[0-9]*", page + str(i), self.URL)
                #print(self.URL)
                #time.sleep(30)
                if self.name_site == "deporvillage.fr":
                    self.bs4WithJS()
                else:
                    self.response = requests.get(URL, headers=self.headers) #, allow_redirects=True)
                    self.soup = bs4.BeautifulSoup(self.response.text, "html.parser")
                self.products = self.soup.find_all(self.name_tree_tag[0], attrs={self.name_tree_tag[1]:self.name_tree_tag[2]})

                myjson = json.loads(self.products[0].string)
                myitems = myjson
                for mydict in name_tree2_tag:
                    myitems = myitems[mydict]

            for kk in myitems:

                if kk["defaultVariant"]["stockLabel"] == "NO_STOCK":
                    myarti = myarti - 1
                    continue
                supermodelId = str(kk[self.siteyml[self.name_site]["id"]])
                #marque=kk[self.siteyml[self.name_site]["marque_id"]]
                marque=mybranddict[kk[self.siteyml[self.name_site]["marque_id"]]]
                name=kk[self.siteyml[self.name_site]["name"]]
                #print(name)
                prix = kk
                for mydict in self.siteyml[self.name_site]["price_sale"].split(','):
                    prix = prix[mydict]
                variations_tag = self.siteyml[self.name_site]["variations"].split(',')
                variations = list()
                #print(kk)
                if kk[variations_tag[0]]:
                    for kkk in kk[variations_tag[0]][0][variations_tag[1]]:
                        variations.append(kkk[variations_tag[2]])
                #print(variations)
                url="https://" + self.name_site + kk[self.siteyml[self.name_site]["url"]]
                #print(marque + " " + name + "-" + supermodelId)
                matox[marque + " " + name + "-" + supermodelId] = {"marque":marque.lower(), "name":name.lower(), "prix":prix, "variations":variations, "name_search":name_search, "name_site":self.name_site, "fullname":marque.lower() + " " + name.lower(), "modelId":supermodelId, "url":url}

            i = i + 1
        #price_tag = self.siteyml[self.name_site]["price"].split(',')
        #price_sale_tag = self.siteyml[self.name_site]["price_sale"].split(',')
        #name_tag = self.siteyml[self.name_site]["name"].split(',')
        #marque_tag = self.siteyml[self.name_site]["marque"].split(',')
        #variations_tag = self.siteyml[self.name_site]["variations"].split(',')
        #print(len(matox))
        #print(matox)
        #exit()

        return matox

    def aliexpress(self,name_search): #Page multiples à gérer
        matox = dict()
        print(self.products)
        exit()
        #print(self.products[3].contents[0])
        #myjson = self.products[3].contents[0].split("window.runParams = ", 1)[1].split("window.runParams.csrfToken",1)[0]
        myjson = self.products[3].split("window._dida_config_._init_data_= ", 1)[1].split("</script>",1)[0]
        print(json)
        #exit()
        myjson = myjson.replace(";","")
        myjson = myjson.replace("window.runParams =","")
        myjson = myjson.replace(myjson[0],"",1)
        myjson = myjson.replace(myjson[0],"",1)
        #print(myjson)
        jsonresult = json.loads( myjson )
        #print( str( len(jsonresult["mods"]["itemList"]["content"]) ) ) # =60 => La première page seulement
        #print( json.dumps(jsonresult["mods"]["itemList"]["content"], indent=2) )
        for key in jsonresult["mods"]["itemList"]["content"]:
            #print( json.dumps(key["prices"]["salePrice"]["formattedPrice"], indent=2) )
            #exit()
            if "title" in key:
                name = key["title"]["displayTitle"]
                #marque = "" # a trouver dans le nom
                marque = name.split(" – ")[0].replace(" – ","") #"PIPO – "
                if len(marque) > 15:
                    marque = ""
                if marque != "":
                    name = name.replace(marque + " – ","")
                else:
                    marque = name.split(" ")[0].replace(" ","")
                    name = name.replace(marque + " ","")
                #print(name)
                supermodelId = key["productId"]
                if not "prices" in key:
                    continue
                prix = key["prices"]["salePrice"]["formattedPrice"]
                prix = prix.replace("€ ","")
                prix = prix.replace(".","")
                prix = prix.replace(",",".")
                variations = [] #version CPU / RAM / disque ... à trouver mais à des pruix différents !! => Comment le gérer !!
                url = "https://" + self.name_site + "/item/" + supermodelId + ".html"
                matox[marque + " " + name + "-" + supermodelId] = {"marque":marque.lower(), "name":name.lower(), "prix":prix, "variations":variations, "name_search":name_search, "name_site":self.name_site, "fullname":marque.lower() + " " + name.lower(), "modelId":supermodelId, "url":url}
        return matox

    '''
    def interceptor(request):
        for headername,headervalue in self.headers.items():
            request.headers[headername] = headervalue
    '''
    def generic(self,name_search):
        matox = dict()
        variations = ""
        # Get html tag from config
        price_tag = self.siteyml[self.name_site]["price"].split(',')
        price_sale_tag = self.siteyml[self.name_site]["price_sale"].split(',')
        name_tag = self.siteyml[self.name_site]["name"].split(',')
        marque_tag = self.siteyml[self.name_site]["marque"].split(',')
        variations_tag = self.siteyml[self.name_site]["variations"].split(',')
        if self.siteyml[self.name_site]["number_articles"]:
            number_articles = self.siteyml[self.name_site]["number_articles"].split(',')
            if self.name_site == "probikeshop.fr":
                if not self.soup.find(number_articles[0], attrs={number_articles[1]:number_articles[2]}) is None:
                    number_articles = int(self.soup.find(number_articles[0], attrs={number_articles[1]:number_articles[2]})["value"])
                else:
                    return None
            else:
                number_articles = int(self.trim_the_ends(self.soup.find(number_articles[0], attrs={number_articles[1]:number_articles[2]}).contents[0].replace("Articles","")).replace(".",""))
        else:
            number_articles = 100000 #1

        if self.siteyml[self.name_site]["number_pages"]:
            number_pages_key = self.siteyml[self.name_site]["number_pages"].split(',')
            number_pages2 = self.soup.find(number_pages_key[0],attrs={number_pages_key[1]:number_pages_key[2]})
            try:
                number_pages = int(number_pages2.find_all(number_pages_key[3])[-2].find(number_pages_key[4]).contents[0])
            except: 
                number_pages = 1
                logger.info("No page found !")
        else:
            number_pages = 1000

        i = 1
        alea = 3
        while len(matox) < number_articles - alea and i <= number_pages:
            #print(str(len(matox)) + "/" + str(number_articles) + "/" + str(i) + "/" + str(number_pages))
            #print(str(len(matox)) + " / " + str(number_articles) )
            pageslist=["page=","p="]
            if i > 1:
                for page in pageslist:
                    if page in self.URL:
                        self.URL = re.sub(page+"[0-9]*", page + str(i), self.URL)
                if self.name_site == "culturevelo.com":
                    '''
                    #<input type="hidden" id="URLNEXT" value="/shop/Produits/ListeAjaxFF?filterCategoryPathROOT=V%C3%A9los&filterCategoryPathROOT%2FV%C3%A9los=BMX&page=2&followSearch=9699&navigation=true&verbose=true"/>
                    if self.soup.find("input", attrs={"id":"URLNEXT"}):
                        self.URL = 'https://www.culturevelo.com' + self.soup.find("input", attrs={"id":"URLNEXT"}).get("value")
                    '''
                    '''
                    <script type="text/javascript">
                        if(domCharge == 1){;

                            // affichage de la suite de produits
                            
                            document.getElementById("URLNEXT").value = "/shop/Produits/ListeAjaxFF?filterCategoryPathROOT=V%C3%A9los&filterCategoryPathROOT%2FV%C3%A9los=Electriques&page=2&followSearch=9999&navigation=true&verbose=true" ;
                            document.getElementById("PAGEENCOURS").value = "1" ;
                            document.getElementById("MAXPAGES").value = "41";
                            taggerTop();

                            $(function () {
                            $(".lazy").lazy(
                                //		{threshold : 200}
                                );
                            });

                            document.location = '#finpage'+(document.getElementById("PAGEENCOURS").value - 1);

                                
                        }

                    </script>
                    '''
                    #self.URL = 'https://www.culturevelo.com' + self.soup.find("input", attrs={"id":"URLNEXT"}).get("value")
                    #print( self.soup.find_all("script", attrs={"type":"text/javascript"})[23] )
                    #print(str(self.soup))
                    m = re.search( r"""document\.getElementById\(\"URLNEXT\"\).value = \"(.*)\" ;""", str(self.soup) )
                    if m and m.group(1):
                        self.URL = 'https://www.culturevelo.com' + m.group(1)
                logger.info("URL=" + str(self.URL))

                if self.name_site == "bike24.fr":
                    self.bs4WithJS()
                else:
                    self.response = requests.get(self.URL, headers=self.headers)
                    self.soup = bs4.BeautifulSoup(self.response.text, "html.parser")
                self.products = self.soup.find_all(self.name_tree_tag[0], attrs={self.name_tree_tag[1]:self.name_tree_tag[2]})

            '''
            if self.name_site == "intersport.fr":
                # apt install firefox-esr
                from pyvirtualdisplay import Display
                #from selenium import webdriver
                from seleniumwire import webdriver
                from selenium.webdriver.firefox.options import Options 
                display = Display(visible=0, size=(800, 600))
                display.start()
                options = Options() 
                options.add_argument("-headless")
                driver = webdriver.Firefox(options=options)
                driver.request_interceptor # = self.interceptor
                driver.get(self.URL)

                html = driver.page_source
                self.soup = bs4.BeautifulSoup(html, "html.parser")
                self.products = self.soup.find_all(self.name_tree_tag[0], attrs={self.name_tree_tag[1]:self.name_tree_tag[2]})
            '''

            if not self.products:
                logger.error("Error: No products found !")
                #logger.debug(self.response.text)
                #continue #exit()
                break

            if i == 1 and self.name_site == "culturevelo.com":
                myproducts = self.soup.find_all()
                #print(str(myproducts))
                m = re.search( r"""document\.getElementById\("MAXPAGES"\)\.value \= \"([0-9]*)\"""", str(myproducts) )
                # document.getElementById("MAXPAGES").value = "14";
                if m and m.group(1):
                    number_pages = int(m.group(1))
                
                #print(number_pages)
                #exit()

            TypesInName = ['Vélo de Randonnée', 'vélo ville', 'Velo de Voyage / Velotaf','Vélo de Voyage','Vélo de Route Électrique', 'Vélo de Ville', 'vélo de ville', 
            'vtc électrique', 'vélo de course électrique', 'vélo de gravel', 'vélo de course', 'vtt électrique', 'vtt enfant', 'vtt trail/enduro', 'cross country', 'vtt trail/randonnée','vtt trail',
            'vtc électrique', 'vtc enfant','vtc','vtt']

            logger.debug(len(self.products))
            #exit()

            for product in self.products:
                #logger.debug("product = " + str(product))
                if self.name_site == "culturevelo.com" and "dalleconseil" in str(product):
                    continue
                if len(marque_tag) > 1:
                    marque = self.trim_the_ends( product.find(marque_tag[0], attrs={marque_tag[1]:marque_tag[2]}) )
                    #logger.debug(marque.contents)
                    if self.name_site == "probikeshop.fr" or self.name_site == "alltricks.fr" and marque:
                        for marquee in marque:
                            marque = self.trim_the_ends(marquee)
                    elif ( self.name_site == "bikester.fr" or self.name_site == "bike24.fr") and marque:
                        marque = self.trim_the_ends( product.find(marque_tag[0], attrs={marque_tag[1]:marque_tag[2]}).contents[0] )
                    elif self.name_site == "cyclable.com" and marque:
                        marque = self.trim_the_ends( marque.contents[1] ).text
                else:
                    if self.name_site == "culturevelo.com":
                        marque = self.trim_the_ends( product.find(marque_tag[0]).contents[0] )
                    else:
                        marque = "Inconnu" #Cas probikeshop

                if self.name_site == "bike24.fr":
                    marque = marque.lower().replace(" bikes", "")

                if self.name_site == "culturevelo.com":
                    name = self.trim_the_ends( product.find(name_tag[0]).contents[0] )
                else:
                    if len(name_tag) > 1 and product.find(name_tag[0], attrs={name_tag[1]:name_tag[2]}) is None:
                        return matox
                    name = self.trim_the_ends( product.find(name_tag[0], attrs={name_tag[1]:name_tag[2]}).contents[0] )

                for TypeInName in TypesInName:
                    if name:
                        name = name.lower().replace(TypeInName.lower() + " - ","")
                        name = name.lower().replace(TypeInName.lower() + " ","")
                        name = name.lower().replace(TypeInName.lower(),"")
                    if marque:
                        marque = marque.lower().replace(TypeInName.lower() + " - ","")
                        marque = marque.lower().replace(TypeInName.lower() + " ","")
                        marque = marque.lower().replace(TypeInName.lower(),"")
                    #name = unidecode.unidecode(name).replace(unidecode.unidecode(TypeInName + " ","")
                if marque == "inconnu": #Try to get from name
                    marque = name.split(" ")[0]
                    if marque == "VSF":
                        marque = "VSF FAHRRADMANUFAKTUR"
                if marque and name:
                    name = name.replace(marque + " ","")
                prix = product.find(price_tag[0], attrs={price_tag[1]:price_tag[2]})
                if self.name_site == "alltricks.fr":
                    prix = self.trim_the_ends( prix.contents[len(prix)-1].contents[0]).encode('ascii','ignore').decode()
                elif self.name_site == "bike24.fr":
                    prix = self.trim_the_ends( prix.contents[len(prix)-2]).encode('ascii','ignore').decode()
                else:
                    prix = self.trim_the_ends( prix.contents[len(prix)-1] ).encode('ascii','ignore').decode()
                #logger.debug(prix)
                '''
                if len(prix) == 1:
                    prix = self.trim_the_ends( prix.contents[0] ).encode('ascii','ignore').decode()
                else:
                    prix = self.trim_the_ends( prix.contents[2] ).encode('ascii','ignore').decode()
                '''
                #print(prix)
                if (prix == "PVC" or prix == "" or prix == "*") and price_sale_tag != "":
                    prix = self.trim_the_ends( product.find(price_sale_tag[0], attrs={price_sale_tag[1]:price_sale_tag[2]}).contents[0] )
                if prix and type(prix) == str:
                    prix = self.trim_the_ends( prix )
                    prix = prix.replace(" €", "")
                    prix = prix.replace("€", "")
                    prix = prix.replace(".","")
                    prix = prix.replace(" ","")
                    prix = prix.replace(",",".")
                    #prix = prix.replace("À partir de\n","")
                    prix = prix.replace("Àpartirde\n","")
                    prix = prix.replace("partirde\n","")
                if prix == "N/A":
                    prix = ""
                if self.name_site == "bikester.fr":
                    variations = product.find(variations_tag[0], attrs={variations_tag[1]:variations_tag[2]})
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
                if self.name_site == "probikeshop.fr":
                    variations = product.find(variations_tag[0], attrs={variations_tag[1]:variations_tag[2]})
                    if variations:
                        variations = self.remove_blank_list( self.trim_the_ends(variations.contents[0]).split(",") )
                #if variations != "":
                #    matox[marque + " " + name] = {"marque":marque, "name":name, "prix":prix, "variations":variations, "name_search":name_search, "name_site":name_site, "fullname":marque + " " + name}
                if self.name_site == "alltricks.fr" or self.name_site == "culturevelo.com":
                    #print(product)
                    variations_temp = product.find_all(variations_tag[0], attrs={variations_tag[1]:variations_tag[2]})
                    #print(variations_temp)
                    #exit()
                    variationlist = list()
                    if self.name_site == "culturevelo.com":
                        variations_temp = variations_temp[0].contents[0].split(",")
                        for variation in variations_temp:
                            variationlist.append(variation)
                    elif self.name_site == "alltricks.fr":
                        for variation in variations_temp:
                            variationlist.append(variation.contents[0])
                    variations = variationlist
                supermodelId = ""
                '''
                if self.siteyml[self.name_site]["id"]:
                    idtag = self.siteyml[self.name_site]["id"].split(',')
                    #supermodelId = self.trim_the_ends(self.soup.find(idtag[0], attrs={idtag[1]:idtag[2]}))
                    supermodelId = product.find(idtag[0],attrs={idtag[1]:idtag[2]})
                    #print(str(supermodelId))
                    #print(supermodelId.prettify())
                    #print(supermodelId.value)
                    m = re.search( r"""data-gtm-productdata='({.*"\)"})'""", str(supermodelId) )
                    #print(m.group(1))
                    #print(json.loads(m.group(1)))
                    supermodelId = json.loads(m.group(1))["id"]
                '''
                if self.name_site == "bikester.fr":
                    '''
                    m = re.search( r"""data-gtm-productdata='({.*})' data-masterid=""", str(product) )
                    if m and m.group(1) and "id" in m.group(1):
                        supermodelId = json.loads(m.group(1))["id"]
                    '''
                    #data-productid="G1791454"
                    '''
                    m = re.search( r"""data-productid=\"G(.*)\" data-uv-item=""", str(product) )
                    if m and m.group(1):
                        supermodelId = m.group(1)
                    '''
                    #data-uv-item='{"id":"1392315","unit_sale_price":2429}' id
                    m = re.search( r"""data-uv-item='(.*)' id""", str(product) )
                    if m and m.group(1) and "id" in m.group(1):
                        supermodelId = json.loads(m.group(1))["id"]
                    
                    link = product.find("a",attrs={"class":"js_producttile-link"})
                    m = re.search( r"""href="(.*)" title=""", str(link) )
                    if m and m.group(1):
                        uri = m.group(1)
                    url = "https://www." + self.name_site + uri
                    '''
                    if supermodelId == "":
                        print(product)
                        print(str(supermodelId) + " / " + url)
                    '''
                if self.name_site == "probikeshop.fr":
                    link = product.find("a",attrs={"class":"product_link"})
                    m = re.search( r"""href="(.*)">""", str(link) )
                    if m and m.group(1):
                        uri = m.group(1)
                    url = "https://www." + self.name_site + uri
                    supermodelId = uri.split("/")[-1].strip(".html")
                    #print(str(supermodelId) + " //" + str(url))
                    #exit()

                if self.name_site == "alltricks.fr":
                    m = re.search( r"""href="(\/?\/?[^\s]+)">""", str(product) )
                    if m and m.group(1):
                        uri = m.group(1)
                    url = "https://www." + self.name_site + uri
                    
                    m = re.search( r"""data-product-id="([0-9]*)" """, str(product) )
                    if m and m.group(1):
                        supermodelId = m.group(1)

                if self.name_site == "cyclable.com":
                    m = re.search( r"""data-id-product=\"([0-9]*)\" href=\"(\w+:\/?\/?[^\s]+)\"""", str(product) )
                    if m and m.group(2):
                        url = m.group(2)
                    
                    if m and m.group(1):
                        supermodelId = m.group(1)

                if self.name_site == "culturevelo.com":
                    
                    ''' product : 
                    * 10/11/2023 08h25:
                    <article class="dalle code-SA29FT7__220" id="dallep353544"><img alt="Moustache-Shop" class="marque" src="/shop/images/Logos/fit/Moustache-Shop.png"><p class="promotion-sticker">- 0%</p><p class="nouveaute-sticker">Nouveau</p><p class="flash-sticker">Un seul produit à ce prix</p><p class="top-sticker">Top</p><a href="/shop/moustache-samedi-29-trail-7-353544?source=ffrech&amp;recherche=" onclick="javascript:tracking.click('fr','gupii36lrd7tvb460qiqahkose','353544','353544','*','1','1','1','27','','');"><div class="visuel-produit"><img alt="VTT électrique Moustache SAMEDI 29 TRAIL 7 750Wh" class="prod-img lazy" data-src="https://static.cyclelab.eu/velos/moustache/2007/lowres/sa29ft7--220-samedi-29-trail-7-side-drivetrain-view-studio-1.jpg"/></div><h3>Moustache</h3><h4>Vtt électrique Moustache samedi 29 trail 7 750wh<span class="dispo" style="color:green">Disponible en ligne et en magasin</span></h4><div class="dalle-prix">6 899,00€</div></a></img></article>
                    '''
                    m = re.search( r"""article class=\"dalle.*\" id=\"[a-z]+([0-9]+)\"""", str(product) )
                    if m and m.group(1):
                        supermodelId = m.group(1)
                    '''
                    m = re.search( r"""<a href=\"(.*=)\" """, str(product) )
                    if m and m.group(1):
                        uri = m.group(1)
                    '''
                    uri = product.find('a').get('href')
                    url = "https://www." + self.name_site + uri

                if self.name_site == "bike24.fr":
                    m = re.search( r"""div .* data-product='{\"id\":([0-9]+)}""", str(product) )
                    if m and m.group(1):
                        supermodelId = m.group(1)
                    url = "https://www." + self.name_site + '/produits/' + supermodelId

                if supermodelId != "" and marque:
                    if url and url != "":
                        matox[marque + " " + name + "-" + supermodelId] = {"marque":marque.lower(), "name":name.lower(), "prix":prix, "variations":variations, "name_search":name_search, "name_site":self.name_site, "fullname":marque.lower() + " " + name.lower(), "modelId":supermodelId, "url":url}
                    else:
                        matox[marque + " " + name + "-" + supermodelId] = {"marque":marque.lower(), "name":name.lower(), "prix":prix, "variations":variations, "name_search":name_search, "name_site":self.name_site, "fullname":marque.lower() + " " + name.lower(), "modelId":supermodelId} #, "url":url}
                    #print(marque + " " + name + "-" + supermodelId)
                elif marque:
                    if marque + " " + name in matox:
                        id = str(random.randrange(0, 50000, 5))
                        matox[marque + " " + name + " " + id] = {"marque":marque.lower(), "name":name.lower(), "prix":prix, "variations":variations, "name_search":name_search, "name_site":self.name_site, "fullname":marque.lower() + " " + name.lower()}
                        #print(matox[marque + " " + name + " " + id])
                    else:
                        matox[marque + " " + name] = {"marque":marque.lower(), "name":name.lower(), "prix":prix, "variations":variations, "name_search":name_search, "name_site":self.name_site, "fullname":marque.lower() + " " + name.lower()}
                        #print(matox[marque + " " + name])
                ## Récupération de l'ID produit qui change pour le cas de même nom de pduit : exemple : Ortler Bozen Trapèze, rouge : Année 2021 et 2022
                #  1319869 dans le code : 
                # <div id="5899e52714c17e73464b7fd54b" data-productid="G1319869" data-masterid="M920128" class="js-product-tile-lazyload gtm-producttile product-tile product-tile--sale uv-item   " data-uv-item={&quot;id&quot;:&quot;1319869&quot;,&quot;unit_sale_price&quot;:2239} data-gtm-productdata="{&quot;name&quot;:&quot;Ortler Bozen Trapèze, rouge&quot;,&quot;id&quot;:&quot;1319869&quot;,&quot;brand&quot;:&quot;Ortler&quot;,&quot;price&quot;:1865.83,&quot;dimension42&quot;:&quot;Available&quot;,&quot;dimension51&quot;:4.8,&quot;dimension43&quot;:&quot;rouge&quot;,&quot;dimension62&quot;:&quot;10.4&quot;,&quot;dimension49&quot;:&quot;2499&quot;,&quot;dimension50&quot;:&quot;true&quot;,&quot;metric2&quot;:260,&quot;metric4&quot;:2499,&quot;metric7&quot;:1,&quot;metric8&quot;:0,&quot;variant&quot;:&quot;45cm (28\&quot;)&quot;,&quot;dimension53&quot;:&quot;45cm (28\&quot;)&quot;}">
                #
            #print(str(len(matox)))
            #if i == 6:
            #    print(str(matox))
            
            if i > 200:
                break

            i = i + 1

        return matox
