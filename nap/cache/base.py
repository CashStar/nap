import re
from hashlib import md5

DEFAULT_TIMEOUT = 60 * 5
# Default value for max cache key length favors memcached limitation of 250
# byte key and the assumption the web framework may append additional version
# to the key.
MAX_CACHE_KEY_LENGTH = 240


class BaseCacheBackend:
    CACHE_EMPTY = '!!!DNE!!!'

    def __init__(
            self,
            default_timeout=DEFAULT_TIMEOUT,
            obey_cache_headers=True,
            cache_max_key_size=MAX_CACHE_KEY_LENGTH
    ):
        self.obey_cache_headers = obey_cache_headers
        self.default_timeout = default_timeout
        self.cache_max_key_size = cache_max_key_size

    def get(self, key):
        return None

    def set(self, key, value, response=None):
        return None

    def get_timeout_from_header(self, response):
        cache_headers = response.headers.get('cache-control')
        if cache_headers is None:
            return None

        cache_header_age = re.search(r'max\-?age=(\d+)', cache_headers)
        if cache_header_age:
            return int(cache_header_age.group(1))

    def get_cache_key(self, model, url):
        """Cache key format is %(resource_name)s::%(url)s where the URL may be
        md5 hashed when it exceeds length.  strips white space from cache key
        as its a control character in memcached.
        """

        resource_name = model._meta['resource_name']
        cache_key = '{0}::'.format(resource_name)

        # Check
        if (
                self.cache_max_key_size is not None and
                (len(cache_key) + len(url)) > self.cache_max_key_size
        ):
            cache_key += md5(url.encode('utf-8')).hexdigest()
            logger = model._meta['logger']
            logger.info(
                'Cache key for url %s exceeds length so hashing to key %s',
                url,
                cache_key
            )
        else:
            cache_key += url

        cache_key = cache_key.replace(' ', '')
        return cache_key

    def get_timeout(self, response=None):
        if response and self.obey_cache_headers:
            header_timeout = self.get_timeout_from_header(response)
            if header_timeout:
                return header_timeout

        return self.default_timeout
