import json
import unittest
from unittest import mock

from flask import Flask
from nap.cache import django_cache, flask_cache
from nap.cache.base import (
    DEFAULT_TIMEOUT,
    MAX_CACHE_KEY_LENGTH,
    BaseCacheBackend
)
from tests import SampleCacheableResource, SampleResourceModel


class TestBaseCacheBackend:
    def get_backend(self, **kwargs):
        defaults = {
            'default_timeout': DEFAULT_TIMEOUT,
            'obey_cache_headers': True,
        }
        defaults.update(kwargs)

        return BaseCacheBackend(**defaults)

    def get_fake_request(self, **kwargs):
        defaults = {
            'url': 'http://www.foo.com/bar/',
        }

        defaults.update(kwargs)
        mock_request = mock.Mock()
        for attr, val in defaults.items():
            setattr(mock_request, attr, val)

        return mock_request

    def get_fake_response(self, **kwargs):
        defaults = {
            'status_code': 200,
            'url': 'http://www.foo.com/bar/',
            'headers': {},
        }

        defaults.update(kwargs)
        mock_response = mock.Mock()
        for attr, val in defaults.items():
            setattr(mock_response, attr, val)

        return mock_response

    def test_get_cache_key(self):
        obj = SampleResourceModel(
            title='expected_title',
            content='Blank Content'
        )
        cache_backend = self.get_backend()

        uri = SampleResourceModel.objects.get_lookup_url(resource_obj=obj)
        url = SampleResourceModel.objects.get_full_url(uri)
        key = cache_backend.get_cache_key(SampleResourceModel, url)
        assert key == "note::http://foo.com/v1/expected_title/"

    def test_cache_key_very_long_is_hashed(self):
        # Given: A cache backend and a very long URL
        cache_backend = self.get_backend()
        url = (
            'https://a.very.long.url.should.contain.a.famous.quote.such.as.'
            'Government.of.the people,by.the.people,for.the.people,shall.not.'
            'perish.from.the.Earth.'
            'Hmmm.That.wasnt.long.enough.How.About.'
            'And.in.the.end,its.not.the.years.in.your.life.that.count..Its.'
            'the.life.in.your.years.'
            'Abraham.Lincoln.com'
        )
        assert len(url) > MAX_CACHE_KEY_LENGTH
        cache_backend.get_cache_key(SampleResourceModel, url)
        SampleResourceModel(
            title='expected_title',
            content='Blank Content'
        )
        expected_key = 'note::020b8d3c397af5f2ade0a683608068ee'
        cache_key = cache_backend.get_cache_key(SampleResourceModel, url)
        assert len(cache_key) < MAX_CACHE_KEY_LENGTH
        assert cache_key == expected_key

    def test_get_cache_key_with_parameters(self):
        kwargs = {'c': 1, 'b': 2, 'a_list': [5, 4, 3]}
        obj = SampleResourceModel(
            title='expected_title',
            content='Blank Content',
        )
        cache_backend = self.get_backend()

        uri = SampleResourceModel.objects.get_lookup_url(
            resource_obj=obj, **kwargs
        )
        url = SampleResourceModel.objects.get_full_url(uri)
        key = cache_backend.get_cache_key(SampleResourceModel, url)
        expected_value = (
            'note::http://foo.com/v1/expected_title/?a_list=5&a_list=4&'
            'a_list=3&b=2&c=1'
        )
        assert key == expected_value

    def test_get_timeout_from_header(self):
        cache_backend = self.get_backend()
        headers = {
            'cache-control': 'public, max-age=2592000'
        }
        mock_response = self.get_fake_response(headers=headers)

        timeout = cache_backend.get_timeout_from_header(mock_response)
        assert timeout == 2592000

    def test_get_timeout_from_header_no_cache(self):
        cache_backend = self.get_backend()
        headers = {
            'cache-control': 'no-cache'
        }
        mock_response = self.get_fake_response(headers=headers)

        timeout = cache_backend.get_timeout_from_header(mock_response)
        assert timeout is None

    def test_get_timeout(self):
        cache_backend = self.get_backend()
        mock_response = self.get_fake_response()
        timeout = cache_backend.get_timeout(mock_response)
        assert timeout == DEFAULT_TIMEOUT

        cache_backend = self.get_backend(default_timeout=42)
        timeout = cache_backend.get_timeout(mock_response)
        assert timeout == 42

        headers = {
            'cache-control': 'public, max-age=2592000'
        }
        mock_response = self.get_fake_response(headers=headers)
        timeout = cache_backend.get_timeout(mock_response)
        assert timeout == 2592000

        cache_backend = self.get_backend(
            default_timeout=42,
            obey_cache_headers=False
        )
        timeout = cache_backend.get_timeout(mock_response)
        assert timeout == 42


class TestDjangoCacheBackend(TestBaseCacheBackend):
    def get_backend(self, **kwargs):
        defaults = {
            'default_timeout': DEFAULT_TIMEOUT,
            'obey_cache_headers': True,
        }
        defaults.update(kwargs)

        return django_cache.DjangoCacheBackend(**defaults)

    def test_get(self):
        backend = self.get_backend()
        res = mock.Mock()
        res.url = 'naprulez.org'

        with mock.patch('django.core.cache.cache.get') as dj_cache_get:
            dj_cache_get.return_value = 'a thing'
            backend.get(res)
            assert dj_cache_get.called

    def test_set(self):
        backend = self.get_backend()
        res = mock.Mock()
        res.url = 'naprulez.org'
        res.headers = {}

        with mock.patch('django.core.cache.cache.set') as dj_cache_set:
            backend.set(res, res.value)
            assert dj_cache_set.called


class TestFlaskCacheBackend(TestBaseCacheBackend):
    def get_backend(self, **kwargs):
        defaults = {
            'default_timeout': DEFAULT_TIMEOUT,
            'obey_cache_headers': True,
            'config': {
                'CACHE_TYPE': 'simple',
                'CACHE_KEY_PREFIX': '',
            }
        }
        app = Flask(__name__, static_url_path='/store/static')
        defaults.update(kwargs)

        return flask_cache.FlaskCacheBackend(app, **defaults)

    def test_get(self):
        backend = self.get_backend()
        res = mock.Mock()
        res.url = 'naprulez.org'

        with mock.patch('flask_caching.Cache.get') as fl_cache_get:
            fl_cache_get.return_value = 'a thing'
            backend.get(res)
            assert fl_cache_get.called

    def test_set(self):
        backend = self.get_backend()
        res = mock.Mock()
        res.url = 'naprulez.org'
        res.headers = {}

        with mock.patch('flask_caching.Cache.set') as fl_cache_set:
            backend.set(res, res.value)
            assert fl_cache_set.called


class TestCaching(unittest.TestCase):
    def setUp(self):
        self.the_cache = SampleCacheableResource._meta['cache_backend']
        # NOTE: there is a single instance of the in memory (fake) cache for
        # all instances of our model
        self.the_cache.clear()

    @mock.patch('requests.request')
    def test_get_response_from_filter_is_cached(self, mock_request):
        """Test that filter() responses can be cached.
        NOTE: nap only supports GETs on filter() calls. Weird"""

        # create mock request nap is going to issue and a mock response that
        # nap will get back
        r = mock.Mock()
        r.status_code = 200
        r.content = json.dumps([
            {'title': 'hello1', 'content': 'content1'},
            {'title': 'hello2', 'content': 'content2'}
        ])
        mock_request.return_value = r

        # Make a request with caching DISABLED and verify nothing was cached
        obj = SampleCacheableResource.objects.filter(skip_cache=True)
        assert len(obj) == 2
        assert len(self.the_cache.get_cached_data()) == 0

        # Repeat this time with caching ENABLED and verify the request /
        # response was cached
        obj = SampleCacheableResource.objects.filter(skip_cache=False)
        assert len(obj) == 2
        assert len(self.the_cache.get_cached_data()) == 1

        # Repeat a final time, this time we should get the object from cache
        # w/o making another network request
        mock_request.return_value = None
        mock_request.side_effect = Exception(
            'We\'re making a network request when we should be using the '
            'cached data'
        )
        SampleCacheableResource.objects.filter(skip_cache=False)
        assert obj is not None
        assert len(self.the_cache.get_cached_data()) == 1

    @mock.patch('requests.request')
    def test_get_response_from_lookup_is_cached(self, mock_request):
        """Test that lookup() responses can be cached."""

        # create mock request nap is going to issue and a mock response that
        # nap will get back
        r = mock.Mock()
        r.status_code = 200
        r.content = json.dumps({'title': 'hello1', 'content': 'content1'})
        mock_request.return_value = r

        # Make a request with caching DISABLED and verify nothing was cached
        obj = SampleCacheableResource.objects.lookup(skip_cache=True)
        assert obj is not None

        # NOTE: unlike filter() lookup() always puts the result in the cache.
        # filter() only stores values in the cache
        # if skip_cache is False
        assert len(self.the_cache.get_cached_data()) == 1

        # Repeat this time with caching ENABLED and verify the request /
        # response was cached
        obj = SampleCacheableResource.objects.lookup(skip_cache=False)
        assert obj is not None
        assert len(self.the_cache.get_cached_data()) == 1

        # Repeat a final time, this time we should get the object from cache
        # w/o making another network request
        mock_request.return_value = None
        mock_request.side_effect = Exception(
            'We\'re making a network request when we should be using the '
            'cached data'
        )
        obj = SampleCacheableResource.objects.lookup(skip_cache=False)
        assert obj is not None
        assert len(self.the_cache.get_cached_data()) == 1
