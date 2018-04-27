# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class DoubancrawlItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    # 类型,小类
    book_type = scrapy.Field()
    # 书封面链接
    book_cover_url = scrapy.Field()
    # 名
    book_name = scrapy.Field()
    # 作者
    book_author = scrapy.Field()
    # 图书链接
    book_link = scrapy.Field()
    # 出版社

    book_publisher = scrapy.Field()
    # 出版年
    book_publish_time = scrapy.Field()
    # 页数
    book_pages_num = scrapy.Field()
    # 价格
    book_price = scrapy.Field()
    # 豆瓣评分
    book_rating = scrapy.Field()
    # 评价人数
    book_comment_num = scrapy.Field()
    # 简介
    book_abstract = scrapy.Field()
    # 作者简介
    book_author_abstract = scrapy.Field()
    # 图书信息
    book_info = scrapy.Field()

