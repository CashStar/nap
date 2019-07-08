import nap
from nap.cache.base import BaseCacheBackend


class SampleResourceModel(nap.ResourceModel):
    title = nap.Field()
    content = nap.Field()
    slug = nap.Field(resource_id=True)
    alt_name = nap.Field(api_name='some_field')

    class Meta:
        root_url = 'http://foo.com/v1/'
        resource_name = 'note'
        append_urls = (
            nap.lookup.nap_url(r'%(hello)s/%(what)s/'),
            nap.lookup.nap_url(r'%(title)s/', update=True),
        )


class SampleResourceNoIdModel(nap.ResourceModel):
    title = nap.Field()
    content = nap.Field()
    slug = nap.Field()
    alt_name = nap.Field(api_name='some_field')

    class Meta:
        root_url = 'http://foo.com/v1/'
        resource_name = 'note'
        append_urls = (
            nap.lookup.nap_url(r'%(hello)s/%(what)s/'),
            nap.lookup.nap_url(r'%(title)s/', update=True),
        )


class SampleResourceNoUpdateModel(nap.ResourceModel):
    title = nap.Field()
    content = nap.Field()
    slug = nap.Field(resource_id=True)
    alt_name = nap.Field(api_name='some_field')

    class Meta:
        root_url = 'http://foo.com/v1/'
        resource_name = 'note'
        append_urls = (
            nap.lookup.nap_url(r'%(hello)s/%(what)s/'),
            nap.lookup.nap_url(r'%(title)s/', update=True),
        )
        update_from_write = False


class AuthorModel(nap.ResourceModel):
    name = nap.Field()
    email = nap.Field(default=None)

    class Meta:
        root_url = 'http://foo.com/v1/'


class InMemoryCache(BaseCacheBackend):
    _cache = {}

    def get(self, key):
        return self._cache.get(key)

    def set(self, key, value, response=None):
        self._cache[key] = value

    def get_cached_data(self):
        return self._cache

    def clear(self):
        self._cache = {}


class SampleCacheableResource(nap.ResourceModel):
    title = nap.Field()
    content = nap.Field()
    slug = nap.Field(resource_id=True)
    alt_name = nap.Field(api_name='some_field')

    class Meta:
        root_url = "http://foo.com/v1/"
        resource_name = 'note'
        append_urls = (
            nap.lookup.nap_url(
                r'something/great/', collection=True, lookup=True
            ),
        )
        cache_backend = InMemoryCache()
