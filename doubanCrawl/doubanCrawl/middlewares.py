# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
from .useragent import USER_AGENTS
from .get_proxy import get_ip_port_list
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.response import response_status_message
from scrapy.utils.python import global_object_name
import random
import requests
import logging
import time

logger = logging.getLogger(__name__)

# IP_PORT_QUEUE = get_ip_port_queue()
IP_PORT_LIST = get_ip_port_list()


class RandomUserAgent(object):
    """设置随机user-agent"""
    def process_request(self, request, spider):
        user_agent = random.choice(USER_AGENTS)
        request.headers.setdefault('User_Agent', user_agent)


class RandomProxy(object):
    """设置随机代理IP"""
    def process_request(self, request, spider):
        global IP_PORT_LIST
        if len(IP_PORT_LIST) < 30:
            IP_PORT_LIST = get_ip_port_list()
            if len(IP_PORT_LIST) < 20:
                time.sleep(300)
        if random.choice(IP_PORT_LIST) != '':  # 当选的代理部委空字符串时，使用以下代理，为空时，则不用代理，使用本机IP
            ip_port = random.choice(IP_PORT_LIST)[0]

            request.meta['proxy'] = 'http://' + ip_port

    def process_response(self, request, response, spider):
        if response.status != 200:
            # 删除当前代理，且重新分配代理
            proxy = request.meta.get('proxy', False)
            self._delete_proxy(proxy)
            self._delete_list_proxy(proxy)

            # 当代理列表中代理数小于20的时候，请求新的代理
            global IP_PORT_LIST
            if len(IP_PORT_LIST) < 30:
                IP_PORT_LIST = get_ip_port_list()
                # 如果代理池的ip少于30则等待300s
                if len(IP_PORT_LIST) < 30:
                    time.sleep(300)
            if random.choice(IP_PORT_LIST) != '':
                new_ip_port = random.choice(IP_PORT_LIST)[0]
                # 打印重试代理
                # print('重新发送请求代理：%s' % new_ip_port)
                request.meta['proxy'] = 'http://' + new_ip_port
            return request
        return response

    def _delete_proxy(self, proxy):
        """
        从数据库中删除代理
        :param proxy:
        :return:
        """
        if proxy:
            ip = proxy.split(':')[1][2:]
            ip_port = ip + ':' + proxy.split(':')[2]
            global IP_PORT_LIST
            for each in IP_PORT_LIST:
                if each != '':
                    if ip_port == each[0]:
                        requests.get('http://127.0.0.1:8000/delete?ip=%s' % ip)

    def _delete_list_proxy(self, proxy):
        """
        从列表中删除代理
        :param proxy:
        :return:
        """
        if proxy:
            ip_port = proxy.split(':')[1][2:] + ':' + proxy.split(':')[2]
            global IP_PORT_LIST
            for each in IP_PORT_LIST:
                if each != '':
                    if ip_port == each[0]:
                        IP_PORT_LIST.remove(each)


class MyRetryMiddleware(RetryMiddleware):

    def delete_proxy(self, proxy):
        """从数据库中删除代理"""
        if proxy:
            ip_port = proxy.split(':')[1][2:] + ':' + proxy.split(':')[2]
            ip = proxy.split(':')[1][2:]
            # delete proxy from proxies pool
            global IP_PORT_LIST
            for each in IP_PORT_LIST:
                if each != '':
                    if ip_port == each[0]:
                        requests.get('http://127.0.0.1:8000/delete?ip=%s' % ip)

    def delete_list_proxy(self, proxy):
        """从列表中删除失效代理"""
        if proxy:
            ip_port = proxy.split(':')[1][2:] + ':' + proxy.split(':')[2]
            global IP_PORT_LIST
            for each in IP_PORT_LIST:
                if each != '':
                    if ip_port == each[0]:
                        IP_PORT_LIST.remove(each)

    def add_proxy_tag(self, proxy):
        global IP_PORT_LIST
        ip_port = proxy.split(':')[1][2:] + ':' + proxy.split(':')[2]
        for each in IP_PORT_LIST:
            if each != '':
                if ip_port == each[0]:
                    each[1] += 1

    def _retry(self, request, reason, spider):

        # 为代理列表中代理tag+1,表示已经一次失效
        self.add_proxy_tag(request.meta.get('proxy', ''))
        # 判断失效次数，如果这是第二次则删除，该代理
        now_proxy = request.meta.get('proxy', '')
        now_ip_port = now_proxy.split(':')[1][2:] + ':' + now_proxy.split(':')[2]
        for each in IP_PORT_LIST:
            if each != '':
                if now_ip_port == each[0] and each[1] == 8:
                    self.delete_proxy(request.meta.get('proxy', False))
                    self.delete_list_proxy(request.meta.get('proxy', False))

        retries = request.meta.get('retry_times', 0) + 1

        retry_times = self.max_retry_times

        if 'max_retry_times' in request.meta:
            retry_times = request.meta['max_retry_times']

        stats = spider.crawler.stats
        if retries <= retry_times:
            # 删除该代理,并从列表中剔除
            # self.delete_proxy(request.meta.get('proxy', False))
            # self.delete_list_proxy(request.meta.get('proxy', False))

            logger.debug("Retrying %(request)s (failed %(retries)d times): %(reason)s",
                         {'request': request, 'retries': retries, 'reason': reason},
                         extra={'spider': spider})
            retryreq = request.copy()
            retryreq.meta['retry_times'] = retries
            retryreq.dont_filter = True
            retryreq.priority = request.priority + self.priority_adjust

            if isinstance(reason, Exception):
                reason = global_object_name(reason.__class__)

            stats.inc_value('retry/count')
            stats.inc_value('retry/reason_count/%s' % reason)
            return retryreq
        else:
            # 删除该代理,并从列表中剔除
            # self.delete_proxy(request.meta.get('proxy', False))
            # self.delete_list_proxy(request.meta.get('proxy', False))

            stats.inc_value('retry/max_reached')
            logger.debug("Gave up retrying %(request)s (failed %(retries)d times): %(reason)s",
                         {'request': request, 'retries': retries, 'reason': reason},
                         extra={'spider': spider})


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
