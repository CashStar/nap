from __future__ import unicode_literals
from __future__ import absolute_import
try:
    import flask_caching
except ImportError as e:
    raise ImportError("Error loading Flask-Caching: %s" % e)


from .base import BaseCacheBackend, DEFAULT_TIMEOUT


class FlaskCacheBackend(BaseCacheBackend):

    def __init__(self, app, config=None, **kwargs):
        super(FlaskCacheBackend, self).__init__(**kwargs)
        self.cache = flask_caching.Cache(app, config=config)

    def get(self, key):
        return self.cache.get(key)

    def set(self, key, value, response=None):
        timeout = self.get_timeout(response)
        return self.cache.set(key, value, timeout)
