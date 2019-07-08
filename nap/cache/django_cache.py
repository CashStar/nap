try:
    from django.core.cache import cache
except ImportError as e:
    raise ImportError('Error loading django cache module: {}'.format(e))


from nap.cache.base import BaseCacheBackend


class DjangoCacheBackend(BaseCacheBackend):
    def get(self, key):
        return cache.get(key)

    def set(self, key, value, response=None):
        timeout = self.get_timeout(response)
        return cache.set(key, value, timeout)
