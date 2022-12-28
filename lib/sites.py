import json

class decathlon():

    #def init():

    def baseonjavascript(self, products,name_site,name_search):
        matox = dict()
        jsonresult = json.loads(products[0].contents[0])
        for key in jsonresult["_ctx"]["data"]:
            if "Super" in key["id"]:
                for kk in key["data"]["blocks"]["items"]:
                    marque = kk["brand"]["label"]
                    supermodelId = kk["supermodelId"]
                    for kkk in kk["models"]:
                        name = kkk["webLabel"]
                        prix = kkk["price"]
                        variations = kkk["availableSizes"]
                        url = "https://" + name_site + "/" + kkk["url"]
                        matox[marque + " " + name + "-" + supermodelId] = {"marque":marque.lower(), "name":name.lower(), "prix":prix, "variations":variations, "name_search":name_search, "name_site":name_site, "fullname":marque.lower() + " " + name.lower(), "modelId":supermodelId, "url":url}
        return matox

#class generic():