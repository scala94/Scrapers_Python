import scrapy
import json

class HM_Item(scrapy.Item):
    # define the fields for your item here like:
    prod_name = scrapy.Field()
    price = scrapy.Field()
    color_code = scrapy.Field()
    color = scrapy.Field()
    full_id = scrapy.Field()
    size_code = scrapy.Field()
    few_size_left = scrapy.Field()
    macro_category = scrapy.Field()
    category = scrapy.Field()
    category2 = scrapy.Field()

    #fewPieceLeft = scrapy.Field()


class HMSpider(scrapy.Spider):
    name = 'HM_italy'

    availabl = []
    PieceLeft = []

    start_urls = [
        'https://www2.hm.com/it_it/index.html'
    ]

    def parse(self, response):

        paths = response.xpath('//*[contains(concat( " ", @class, " " ), concat( " ", "menu__super-link", " " ))]/@href').extract()

        for url_site in paths:
            yield response.follow(url_site, callback=self.next_parse)

    def next_parse(self, response):

        cat_url = []
        pre_check = response.xpath('//*[contains(concat( " ", @class, " " ), concat( " ", "link", " " ))]/@href').extract()
        current = response.url
        current = current.split(".")[2][3:-1]

        for i in range(len(pre_check)):
            if current in pre_check[i]:
                cat_url.append(pre_check[i])

        for url_cat in cat_url:
            url_cat = url_cat + "?page-size=7000"

            yield response.follow(url_cat, callback=self.product_parse)

    def product_parse(self, response):

        prod_url = response.xpath('//*[contains(concat( " ", @class, " " ), concat( " ", "item-heading", " " ))]//*[contains(concat( " ", @class, " " ), concat( " ", "link", " " ))]/@href').extract()

        for url_prod in prod_url:
            id_prod = url_prod.split(".")[1][:-3]
            id_prod = 'https://www2.hm.com/hmwebservices/service/product/it/availability/' + id_prod + '.json'
            yield response.follow(id_prod, callback=self.availability_parse)

    def availability_parse(self, response):

        data = json.loads(response.text)
        HMSpider.availabl.append(data['availability'])
        HMSpider.PieceLeft.append(data["fewPieceLeft"])
        current_items = data['availability'] + data["fewPieceLeft"]
        for i in range(len(current_items)):
            current_items[i] = current_items[i][:-3]

        current_items = list(set(current_items))
        current_items = ["https://www2.hm.com/it_it/productpage." + ii + ".html" for ii in current_items]

        for urls in current_items:
            yield response.follow(urls, callback=self.final_parse)

    def final_parse(self, response):
        items = HM_Item()
        prod_name = response.xpath('//*[contains(concat( " ", @class, " " ), concat( " ", "product-item-headline", " " ))]/text()').extract()
        price = response.xpath('//*[contains(concat( " ", @class, " " ), concat( " ", "price-value", " " ))]/text()').extract()
        color_xpath = response.xpath('//*[contains(concat( " ", @class, " " ), concat( " ", "miniature", " " ))]').extract()
        macro_category = response.xpath('//*[contains(concat( " ", @class, " " ), concat( " ", "breadcrumb-list-item", " " )) and (((count(preceding-sibling::*) + 1) = 2) and parent::*)]//span/text()').extract()
        category = response.xpath('//*[contains(concat( " ", @class, " " ), concat( " ", "breadcrumb-list-item", " " )) and (((count(preceding-sibling::*) + 1) = 3) and parent::*)]//span/text()').extract()
        category2 = response.xpath('//*[contains(concat( " ", @class, " " ), concat( " ", "breadcrumb-list-item", " " )) and (((count(preceding-sibling::*) + 1) = 4) and parent::*)]//span/text()').extract()
        item_code = response.url
        color_code = item_code.split(".")[3][-3:]
        item_code = item_code.split(".")[3]

        full_id = []
        for x in range(len(HMSpider.availabl)):
            for xx in range(len(HMSpider.availabl[x])):
                if item_code in HMSpider.availabl[x][xx]:
                    full_id.append(HMSpider.availabl[x][xx])

        few_piece = []
        for y in range(len(HMSpider.PieceLeft)):
            for yy in range(len(HMSpider.PieceLeft[y])):
                if item_code in HMSpider.PieceLeft[y][yy]:
                    few_piece.append(HMSpider.PieceLeft[y][yy])

        color = []
        for z in range(len(color_xpath)):
            if color_code in color_xpath[z].split(" ")[1].split(".")[1][-3:]:
                color = color_xpath[z].split('"')[3]

        items["prod_name"] = prod_name
        items["price"] = price
        items["color_code"] = color_code
        items["color"] = color
        items["full_id"] = full_id
        items["size_code"] = [q[-3:] for q in full_id]
        items["few_size_left"] = [qq[-3:] for qq in few_piece]
        items["macro_category"] = macro_category
        items["category"] = category
        items["category2"] = category2

        yield items







