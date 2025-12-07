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

    def push_to_list(self, queue, instance, trim=500, redis_conn=None, bump=True, site=None, expiry=None):
        backend = RedisBackend(conn=redis_conn)
        key = self.get_key(queue, site=site)
        current_list = backend.get_ids(key)
        known_length = len(list(current_list)) + 1
        if bump:
            if instance.pk in current_list:
                backend.remove(key, instance.pk)
                known_length -= 1
        backend.add(key, instance.pk)
        if trim and known_length > trim:
            backend.trim(key, trim)
        if expiry is not None:
            backend.conn.expire(key, expiry)

    def base_qs(self):
        return self.model.objects.all()

    def get_list(self, queue, as_model=True, limit=None, in_pks=None, randomize=False, site=None, unique=True):
        backend = RedisBackend()
        pks = backend.get_ids(self.get_key(queue, site=site), limit=limit)
        if not pks:
            return []
        if in_pks:
            pks = [i for i in pks if i in in_pks]
        if not as_model:
            return pks
        if unique:
            used = []
            for item in pks:
                if item not in used:
                    used.append(item)
            pks = used

        def generator_inner(inner_pks):
            qs = None
            if len(inner_pks) > 10 and (not limit or limit > 10):
                qs = list(self.base_qs().filter(pk__in=inner_pks))
            count = 0
            if randomize:
                random.shuffle(inner_pks)
            for pk in inner_pks:
                if qs:
                    for item in qs:
                        if item.pk == pk:
                            yield item
                            count += 1
                            qs.remove(item)
                            break
                else:
                    try:
                        yield self.base_qs().get(pk=pk)
                        count += 1
                    except self.model.DoesNotExist:
                        continue
                if limit and count == limit:
                    break
        return generator_inner(pks)
