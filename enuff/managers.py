import random
from django.db import models
from django.conf import settings
from enuff.backends.redis import RedisBackend  # Only one for now.
from enuff.utils import ensure_pk


class EnuffManager(models.Manager):
    NS_SEP = '::'  # namespace separator

    def get_key(self, queue, site=None):
        site = ensure_pk(site) or settings.SITE_ID

        key_tokens = [site, self.model._meta.app_label, self.model._meta.model_name, queue]
        key = self.NS_SEP.join(map(str, key_tokens))
        return key

    def push_to_list(self, queue, instances, trim=500, redis_conn=None, bump=True, site=None):
        try:
            iter(instances)
        except TypeError:
            instances = [instances]
        backend = RedisBackend(conn=redis_conn)
        key = self.get_key(queue, site=site)
        current_list = backend.get_ids(queue, limit=trim)
        known_length = len(current_list) + len(instances)
        if bump:
            for item in instances:
                if item.pk in current_list:
                    backend.remove(key, item.pk)
                    known_length -= 1
        for item in instances:
            backend.add(key, item.pk)
        if trim and known_length > trim:
            backend.trim(key, trim)

    def base_qs(self):
        return self.model.objects.all()

    def get_list(self, queue, as_model=True, limit=None, in_pks=None, randomize=False, site=None, sort_lambda=None):
        backend = RedisBackend()
        pks = backend.get_ids(self.get_key(queue, site=site), limit=limit)
        if in_pks:
            pks = [i for i in pks if i in in_pks]
        if not pks:
            return []
        if randomize:
            random.shuffle(pks)
        if not as_model:
            return pks

        def generator_inner(qs):
            count = 0
            for pk in pks:
                for instance in qs:
                    if limit and count == limit:
                        break
                    if instance.pk == pk:
                        count += 1
                        yield instance

        qs = self.base_qs().filter(pk__in=pks)  # so ok, this is technically SQL but can SQL fuck this one up THAT bad??
        qs = qs if not sort_lambda else sort_lambda(qs)
        return generator_inner(qs)
