# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
from .useragent import USER_AGENTS
from .get_proxy import get_ip_port_queue
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.response import response_status_message
import random
import requests
import logging

IP_PORT_QUEUE = get_ip_port_queue()
IP_PORT = IP_PORT_QUEUE.get()


class RandomUserAgent(object):
    """设置随机user-agent"""
    def process_request(self, request, spider):
        user_agent = random.choice(USER_AGENTS)
        request.headers.setdefault('User_Agent', user_agent)


class RandomProxy(object):
    """设置随机代理IP"""
    def __init__(self):
        self.ip_port_queue = get_ip_port_queue()

    def process_request(self, request, spider):
        if self.ip_port_queue.empty():
            self.ip_port_queue = get_ip_port_queue()
        proxy = self.ip_port_queue.get()
        # 打印当前代理
        # print('当前代理是：%s' % proxy)
        request.meta['proxy'] = 'http://' + proxy

    def process_response(self, request, response, spider):
        if response.status != 200:
            # 删除当前代理，且重新分配代理
            proxy = request.meta.get('proxy', False)
            ip_port = proxy.split(':')[1][2:]
            self._delete_proxy(ip_port)
            # 判断当前ip_port_queue是否为空，如果为空，则请求新的
            if self.ip_port_queue.empty():
                self.ip_port_queue = get_ip_port_queue()
            new_ip_port = self.ip_port_queue.get()
            # 打印重试代理
            # print('重新发送请求代理：%s' % new_ip_port)
            request.meta['proxy'] = 'http://' + new_ip_port
            return request
        return response

    def _delete_proxy(self, proxy):
        requests.get('http://127.0.0.1:8000/delete?ip=%s' % proxy)


class MyRetryMiddleware(RetryMiddleware):
    logger = logging.getLogger(__name__)

    def delete_proxy(self, proxy):
        if proxy:
            ip_port = proxy.split(':')[1][2:]
            # delete proxy from proxies pool
            requests.get('http://127.0.0.1:8000/delete?ip=%s' % ip_port)

    def process_response(self, request, response, spider):
        if request.meta.get('dont_retry', False):
            return response
        if response.status in self.retry_http_codes:
            reason = response_status_message(response.status)
            # 删除该代理
            self.delete_proxy(request.meta.get('proxy', False))
            # 设置新的ip代理
            global IP_PORT_QUEUE
            global IP_PORT
            if IP_PORT_QUEUE.empty():
                IP_PORT_QUEUE = get_ip_port_queue()
            IP_PORT = IP_PORT_QUEUE.get()
            # request.meta['proxy'] = IP_PORT
            # 删除当前代理
            request.meta.pop('proxy')
            request.meta['proxy'] = 'http://' + IP_PORT
            # print('retry代理%s' % request.meta.get('proxy', '无'))
            # time.sleep(random.randint(3, 5))
            self.logger.warning('返回值异常, 进行重试...')
            # return self._retry(request, reason, spider) or response
            return request
        return response


class DoubancrawlSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class DoubancrawlDownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)
