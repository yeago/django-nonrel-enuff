from redis import Redis
from enuff.utils import ensure_pk

class RedisBackend(object):
    def __init__(self, conn=None):
        self.conn = conn or Redis()

    def get_queue_template(self):
        raise NotImplementedError

    def remove(self, queue, instance):
        self.conn.lrem(queue, ensure_pk(instance))

    def add(self, queue, instance):
        self.conn.lrem(queue, ensure_pk(instance))

    def trim(self, queue, trim):
        self.conn.ltrim(queue, 0, trim)

    def get_ids(self, queue, limit=None):
        return map(int, self.conn.lrange(queue, 0, limit or -1))
