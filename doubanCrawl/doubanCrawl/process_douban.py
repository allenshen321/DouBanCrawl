

import json
import redis
import pymongo


class SaveToMongodb(object):
    def __init__(self, database='douban', collection='book_new'):
        self.redis_cli = redis.StrictRedis(host='127.0.0.1', port=6379, db=0)
        self.mongo_cli = pymongo.MongoClient(host='localhost', port=27017)
        # 创建数据库和集合
        self.db = self.mongo_cli[database]
        self.collection = self.db[collection]

    def save_data(self):
        i = 1
        while True:
            print('正在保存%s个' % i)
            i += 1
            # FIFO模式为blpop，LIFO模式为brpop，获取键值
            source, data = self.redis_cli.blpop(['douban:items'])
            item = json.loads(data.decode())
            self.collection.insert(item)


if __name__ == '__main__':
    save = SaveToMongodb()
    save.save_data()
