import redis

from CrawlerInterface import ICrawlerDbHelper, singleton


@singleton
class CrawlerRedisHelper(ICrawlerDbHelper):
    redis_conn = None

    def __init__(self):
        if self.redis_conn is None:
            self.redis_conn = redis.StrictRedis(host='localhost', port=6379, db=0)

    def create_table(self, name):
        pass

    def delete_table(self, name):
        if self.redis_conn is not None:
            self.redis_conn.delete(name)

    def save_page(self, name, url, page_code):
        if self.redis_conn is not None:
            self.redis_conn.hset(name=name, key=url, value=page_code)

    def save_pages(self, name, page_dict: dict):
        if self.redis_conn is not None:
            self.redis_conn.hset(name=name, mapping=page_dict)

    def read_page(self, name, url):
        if self.redis_conn is not None:
            return self.redis_conn.hget(name=name, key=url)

    def read_pages(self, name, urls: list) -> list:
        if self.redis_conn is not None:
            return self.redis_conn.hmget(name=name, keys=urls)

    def read_all(self, name) -> dict:
        if self.redis_conn is not None:
            return self.redis_conn.hgetall(name)
