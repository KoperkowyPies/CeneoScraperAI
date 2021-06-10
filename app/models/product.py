from app import app
from app.utils import extractElement
from app.models.opinion import Opinion
import requests
import json
import pandas as pd
from bs4 import BeautifulSoup

class Product:

    url_pre = 'https://www.ceneo.pl'
    url_post = '#tab=reviews'

    def __init__(self, productId=None, name=None, opinions=[], averageScore=None, opinionsCount=None, prosCount=None, consCount=None):
        self.productId = productId
        self.name = name
        self.opinions = opinions.copy()
        self.averageScore =  averageScore
        self.opinionsCount = opinionsCount
        self.prosCount = prosCount
        self.consCount = consCount

    def opinionsPageUrl(self):
        return self.url_pre+'/'+self.productId+self.url_post

    def extractName(self):
        respons = requests.get(self.opinionsPageUrl())
        if respons.status_code == 200:
            pageDOM = BeautifulSoup(respons.text, 'html.parser')
            self.name = extractElement(pageDOM, 'h1.product-top__product-info__name')
        return self.name
    
    def extractProduct(self):
        url = self.opinionsPageUrl()
        while url:
            respons = requests.get(url)
            pageDOM = BeautifulSoup(respons.text, 'html.parser')
            opinions = pageDOM.select("div.js_product-review")
            for opinion in opinions:
                self.opinions.append(Opinion().extractOpinion(opinion).transformOpinion())
            try:
                url = self.url_pre + extractElement(pageDOM, 'a.pagination__next', "href") 
            except TypeError:
                url = None

    def countDooku(self):
        #countProductStatistics
        opinions = self.opinionsToDataFrame()
        self.averageScore = float(opinions['stars'].mean())
        self.opinionsCount = len(self.opinions)
        self.prosCount = int(opinions['advantages'].count())
        self.consCount = int(opinions['disadvantages'].count())

    def exportProduct(self):
        with open("app/products/{}.json".format(self.productId), "w", encoding="UTF-8") as jf:
            json.dump(self.productsTodict(), jf, indent=4, ensure_ascii=False)
        with open("app/opinions/{}.json".format(self.productId), "w", encoding="UTF-8") as jf:
            json.dump(self.opinionsTodictList(), jf, indent=4, ensure_ascii=False)

    def importProduct(self):
        with open("app/products/{}.json".format(self.productId), "r", encoding="UTF-8") as jf:
            product = json.load(jf)
            self.__init__(**product)
        with open("app/opinions/{}.json".format(self.productId), "r", encoding="UTF-8") as jf:
            opinions = json.load(jf)
            for opinion in opinions:
                self.opinions.append(Opinion(**opinion))
        return self

    def __str__(self):
        return '''productId: {}<br>
        name: {}<br>'''.format(self.productId, self.name)+"<br>".join(str(opinion) for opinion in self.opinions)

    def todict(self):
        return self.productsTodict() | {"opinions": self.opinionsTodictList}

    def productsTodict(self):
        return {
            "productId": self.productId,
            "name": self.name,
            "averageScore": self.averageScore,
            "opinionsCount": self.opinionsCount,
            "prosCount": self.prosCount,
            "consCount": self.consCount
        }

    def opinionsTodictList(self):
        return [opinion.todict() for opinion in self.opinions]

    def opinionsToDataFrame(self):
        #opinions = pd.DataFrame.from_records(
            #[opinion.todict() for opinion in self.opinions])
        opinions = pd.json_normalize([opinion.todict() for opinion in self.opinions])
        return opinions

