# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy_redis.spiders import RedisCrawlSpider
from doubanCrawl.items import DoubancrawlItem


class DoubanSpider(RedisCrawlSpider):
    name = 'douban'
    redis_key = 'DoubanSpider:start_urls'
    allowed_domains = ['book.douban.com']

    rules = (
        # 提取首页大类下的url
        Rule(LinkExtractor(allow=r'book.douban.com/tag/[\u2E80-\u9FFF]+$'), follow=True),
        # 提取小类下面的book链接
        Rule(LinkExtractor(allow=r'/subject/\d+/$'), callback='parse_book_info', follow=True),
        # 提取下一页连接
        Rule(LinkExtractor(allow=r'\?start=\d+&type=T$'), follow=True),

    )

    # def __init__(self, *args, **kwargs):
    #     domain = kwargs.pop('domain', '')
    #     self.allowed_domains = filter(None, domain.split(','))
    #
    #     super(DoubanSpider, self).__init__(*args, **kwargs)

    def parse_book_info(self, response):
        book_type = response.xpath('//div[@class="blank20"]/div[@class="indent"]/span/a/text()').extract()
        book_cover_url = response.xpath('//div[@class="subject clearfix"]/div[@id="mainpic"]/a/@href').extract_first()
        book_name = response.xpath('//h1/span/text()').extract_first()
        book_author = response.xpath('//div[@id="info"]/a[1]/text()').extract_first()
        if book_author == None:
            book_author = response.xpath('//div[@id="info"]/span/a[1]/text()').extract_first()
        book_link = response.url

        # 提取图书相关信息
        book_info = response.xpath(r'//div[@id="info"]/text()').extract()
        book_info_list = []
        for book in book_info:
            book1 = book.replace('\n', '')
            book2 = book1.strip()
            if book2 != '':
                book_info_list.append(book2)

        if len(book_info_list) == 7:
            book_publisher = book_info_list[0]
            book_publish_time = book_info_list[2]
            book_pages_num = book_info_list[3]
            book_price = book_info_list[4]
        elif len(book_info_list) == 8:
            book_publisher = book_info_list[0]
            book_publish_time = book_info_list[3]
            book_pages_num = book_info_list[4]
            book_price = book_info_list[5]
        elif len(book_info_list) == 6:
            book_publisher = book_info_list[0]
            book_publish_time = book_info_list[1]
            book_pages_num = book_info_list[2]
            book_price = book_info_list[3]
        else:
            book_publisher = ''
            book_publish_time = ''
            book_pages_num = ''
            book_price = ''

        # 评分
        book_rating = response.xpath(r'//div[@class="rating_self clearfix"]/strong/text()').extract_first()
        # 评论人数
        book_comment_num = response.xpath(r'//div[@class="rating_sum"]/span/a/span/text()').extract_first()

        # 简介
        abstract = response.xpath(r'//div[@class="intro"]')

        if len(abstract) > 0:
            book_abstract_list = abstract[0].xpath(r'./p/text()').extract()
        else:
            try:
                book_abstract_list = abstract.xpath(r'./p/text()').extract()
            except Exception as e:
                book_abstract_list = []
        book_abstract = ''
        for each in book_abstract_list:
            book_abstract += each + '\n'

        try:
            book_author_abstract_list = abstract[1].xpath(r'./p/text()').extract()
        except Exception as e:
            book_author_abstract_list = []

        book_author_abstract = ''
        for each in book_author_abstract_list:
            book_author_abstract += each + '\n'

        item = DoubancrawlItem(
            book_name=book_name,
            book_author=book_author,
            book_type=book_type,
            book_rating=book_rating,
            book_comment_num=book_comment_num,
            book_cover_url=book_cover_url,
            book_publisher=book_publisher,
            book_publish_time=book_publish_time,
            book_pages_num=book_pages_num,
            book_price=book_price,
            book_abstract=book_abstract,
            book_author_abstract=book_author_abstract,
            book_link=book_link,
            book_info=book_info_list
        )

        # 判断是否书名为空，若是，则重新发送请求并切换代理
        if book_name == '' or book_name is None:
            yield scrapy.Request(response.url,callback=self.parse_book_info)
        else:
            yield item
