import scrapy
import json
import datetime
from scrapy.http import FormRequest
from ..items import ElcorteinglesItem
import w3lib.html
import re


from urllib.parse import urlparse,urljoin

from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, MapCompose



class ElCorteInglesSpider(scrapy.Spider):
    name = "ECI-ES"
    count = 0
    forgotten_fields = set()
    storeCountry=[]
    count_items = []
    category = []
    scrapetime = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S%Z") + "Z"

    def start_requests(self):
        start_urls = 'https://www.elcorteingles.es/supermercado/'
        cookies = {}
        self.logger.debug(start_urls)
        self.store_country = start_urls[26:28].upper()
        self.logger.debug(self.store_country)
        headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                   'Referer': 'https://www.google.de/',
                   'Sec-Fetch-Dest': 'document',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'}


        yield scrapy.Request(url=start_urls, callback=self.parse, headers= headers)

    def parse(self, response):
        all_categories = response.xpath('//*[contains(concat( " ", @class, " " ), concat( " ", "top_menu-item", " " ))]/@href').extract()
        self.logger.debug(len(all_categories))

        # referer = 'https://www.elcorteingles.es/supermercado/'
        for category in all_categories:
            category = category.replace('/supermercado/', '')
            categoryUrl = 'https://www.elcorteingles.es/supermercado/'+ category
            headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                       'Referer': 'https://www.elcorteingles.es/supermercado/',
                       'Sec-Fetch-Dest': 'document',
                       'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'}
            dict = {'category': category, 'page': 0}
            self.logger.debug(categoryUrl)
            yield response.follow(url=categoryUrl, meta=dict, callback=self.next_parse, headers=headers)


    def next_parse(self, response):

        category = response.meta.get("category")
        page = response.meta.get("page")
        headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                   'Referer': response.url,
                   'Sec-Fetch-Dest': 'document',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'}

        dict = {'category': category, 'page': page}
        allProductUrl = response.xpath('//*[contains(concat( " ", @class, " " ), concat( " ", "product_tile-description", " " ))]//a/@href').extract()
        maxPage = response.xpath('//div[@class="pagination c12 js-pagination"]/@data-pagination-total').extract()
        # print(maxPage)
        # print(allProductUrl)
        for item in allProductUrl:
                yield response.follow(url=item, meta=dict, callback=self.final_parse, headers = headers)

        while page <= int(maxPage[0]):
            page+=1
            next_page = 'https://www.elcorteingles.es/supermercado/'+ category + str(page) +'/'
            dict = {'category': category, 'page': page}
            yield response.follow(url=next_page, callback=self.next_parse, meta=dict, headers = headers)


    def final_parse(self, response):

        ElCorteInglesItemLoader = ItemLoader(item=ElcorteinglesItem(), response=response)
        ElCorteInglesItemLoader.default_output_processor = TakeFirst()

        data = response.xpath('//script[contains(text(),"dataLayer")]/text()')[0].extract()
        #print(data)
        dataLayer = data[13:-2]
        AllInfo = ''

        if 'products' in dataLayer:
            category = response.meta.get("category")
            page = response.meta.get("page")
            headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'Referer': response.url,
                'Sec-Fetch-Dest': 'document',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'}

            dict = {'category': category, 'page': page}
            subitems = response.xpath('//*[contains(concat( " ", @class, " " ), concat( " ", "js-product-link", " " ))]/@href').extract()
            for item in subitems:
                itemUrl = 'https://www.elcorteingles.es' + item
                yield response.follow(url=itemUrl, meta=dict, callback=self.final_parse, headers = headers)

        else:
            AllInfo = json.loads(dataLayer)
        #print(AllInfo['product'])
            Name = AllInfo['product'].get('name', " ")

            productCategory = AllInfo['product']['category'][0]
            productSubCategory = AllInfo['product']['category'][1]
            productFamily = AllInfo['product']['category'][2]
            productSubFamily = AllInfo['product']['category'][3]

            ShopCategory = productCategory + "|" + productSubCategory + "|" + productFamily + "|" + productSubFamily
            URL = response.url
            ProductID = AllInfo['product'].get('id', " ")
            GlobalIdentifier = response.xpath('//*[contains(concat( " ", @class, " " ), concat( " ", "pdp-reference", " " ))]//span/text()').get(default=' ')
            GlobalIdentifierType = 'GTIN'
            LocalIdentifier = ProductID
            LocalIdentifierType = "WebpageID"

            prices = AllInfo['product'].get('price', " ")
            Price = prices.get('final', ' ')

            StandardisedCurrency = AllInfo['product'].get('currency', " ")
            UndiscountedPrice = prices.get('original',' ')
            QuantityProduct = AllInfo['product'].get('quantity', " ")
            BasePrice = response.xpath('//*[contains(concat( " ", @class, " " ), concat( " ", "pdp-prices", " " ))]//*[contains(concat( " ", @class, " " ), concat( " ", "_pum", " " ))]/text()').get(default = ' ')
            available = AllInfo['product'].get('status', " ")
            if available == 'AVAILABLE':
                isAvailable = True
            else:
                isAvailable = False

            DiscountDescription = response.xpath('//*[contains(concat( " ", @class, " " ), concat( " ", "offer-description", " " ))]/text()').get(default=' ')
            Brand = AllInfo['product'].get('brand', " ")
            isDiscounted = AllInfo['product'].get('discount', " ")

            #postcode = AllInfo['session'].get('cod_postal', " ")
            #postcode = response.xpath('//b/text()').get(default = ' ')
            #print(postcode)

            ShopID = AllInfo['session'].get('id_center', " ")
            AllKeys = response.xpath('//*[contains(concat( " ", @class, " " ), concat( " ", "info", " " )) and (((count(preceding-sibling::*) + 1) = 1) and parent::*)]//*[contains(concat( " ", @class, " " ), concat( " ", "info-item", " " ))]').extract()
            Description = ""
            ProductCountry = ""
            Producer = ""
            AdditionalInfo = ""
            ProducerAddress = ""
            FullDescription = []
            for key in AllKeys:
                keySeparate = key.split('</span> ')
                for i,text in enumerate(keySeparate):
                    cleanr = re.compile('<.*?>')
                    cleantext = re.sub(cleanr, '', text)
                    keySeparate[i]=cleantext
                if keySeparate[0] == 'Denominación del alimento:':
                    Description = keySeparate[1]
                elif keySeparate[0] == 'País de origen:':
                    ProductCountry = keySeparate[1]
                elif keySeparate[0] == 'Nombre del operador:':
                    Producer = keySeparate[1]
                elif keySeparate[0] == 'Otras menciones obligatorias en la etiqueta:':
                    AdditionalInfo = keySeparate[1]
                elif keySeparate[0] == 'Dirección del operador:':
                    ProducerAddress = keySeparate[1]
                else:
                    FullDescription.append(keySeparate[0]+" "+keySeparate[1])

            productIngredients = response.xpath('//*[contains(concat( " ", @class, " " ), concat( " ", "info", " " )) and (((count(preceding-sibling::*) + 1) = 2) and parent::*)]//*[contains(concat( " ", @class, " " ), concat( " ", "info-item", " " ))]').get(default=" ")
            cleanr = re.compile('<.*?>')
            Ingredients = re.sub(cleanr, '', productIngredients)
            productAdvicesForUse = response.css('._nutrients+ .info').extract()
            if productAdvicesForUse == []:
                AdvicesForUse = " "
            else:
                AdvicesForUse = re.sub(cleanr, '', productAdvicesForUse[0])
            NutritionalValues = response.xpath('//*[contains(concat( " ", @class, " " ), concat( " ", "_nutrients", " " ))]//*[contains(concat( " ", @class, " " ), concat( " ", "_nutrients", " " ))]').get(default=" ")
            NutritionInformation = w3lib.html.remove_tags(NutritionalValues)
            NutritionDeclaration = response.xpath('//*[contains(concat( " ", @class, " " ), concat( " ", "_nutrients", " " ))]//*[contains(concat( " ", @class, " " ), concat( " ", "info", " " ))]//*[contains(concat( " ", @class, " " ), concat( " ", "info-item", " " ))]/text()').get(default = ' ')

            ElCorteInglesItemLoader.add_value('ScrapeDateTime', str(self.scrapetime))  # time when scraping started
            ElCorteInglesItemLoader.add_value('Country', self.storeCountry)
            #ElCorteInglesItemLoader.add_value('Postcode', Postcode)
            ElCorteInglesItemLoader.add_value('ShopID', ShopID)
            ElCorteInglesItemLoader.add_value('Name', Name)
            ElCorteInglesItemLoader.add_value('ShopCategory', ShopCategory)
            ElCorteInglesItemLoader.add_value('URL', URL)
            ElCorteInglesItemLoader.add_value('ProductID', ProductID)
            ElCorteInglesItemLoader.add_value('GlobalIdentifier', GlobalIdentifier)
            ElCorteInglesItemLoader.add_value('GlobalIdentifierType', GlobalIdentifierType)
            ElCorteInglesItemLoader.add_value('LocalIdentifier', LocalIdentifier)
            ElCorteInglesItemLoader.add_value('LocalIdentifierType', LocalIdentifierType)
            ElCorteInglesItemLoader.add_value('Price', Price)
            ElCorteInglesItemLoader.add_value('StandardisedCurrency', StandardisedCurrency)
            ElCorteInglesItemLoader.add_value('QuantityProduct', QuantityProduct)
            ElCorteInglesItemLoader.add_value('BasePrice', BasePrice)
            ElCorteInglesItemLoader.add_value('isAvailable', isAvailable)
            ElCorteInglesItemLoader.add_value('ProductCountry', ProductCountry)
            ElCorteInglesItemLoader.add_value('DiscountDescription', DiscountDescription)
            ElCorteInglesItemLoader.add_value('Description', Description)
            ElCorteInglesItemLoader.add_value('Brand', Brand)
            ElCorteInglesItemLoader.add_value('UndiscountedPrice', UndiscountedPrice)
            ElCorteInglesItemLoader.add_value('isDiscounted', isDiscounted)
            ElCorteInglesItemLoader.add_value('Producer', Producer)
            ElCorteInglesItemLoader.add_value('AdditionalInfo', AdditionalInfo)
            ElCorteInglesItemLoader.add_value('ProducerAddress', ProducerAddress)
            ElCorteInglesItemLoader.add_value('FullDescription', FullDescription)

            ElCorteInglesItemLoader.add_value('NutritionInformation', NutritionInformation)
            ElCorteInglesItemLoader.add_value('NutritionDeclaration', NutritionDeclaration)
            ElCorteInglesItemLoader.add_value('Ingredients', Ingredients)
            ElCorteInglesItemLoader.add_value('AdvicesForUse', AdvicesForUse)


            yield ElCorteInglesItemLoader.load_item()

            self.count_items.append(Name)
            self.logger.debug(len(self.count_items))
