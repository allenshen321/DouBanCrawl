
from scrapy import cmdline
from multiprocessing import Process


def start_spider1():
    cmdline.execute('scrapy runspider douban.py'.split())


def start_spider2():
    cmdline.execute('scrapy runspider douban.py'.split())


p1 = Process(target=start_spider1, name='douban1')
p2 = Process(target=start_spider2, name='douban2')

p1.start()
p2.start()
