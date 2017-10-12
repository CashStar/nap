from __future__ import unicode_literals
from __future__ import absolute_import
import mock
import pytest

from flask import Flask

from . import SampleResourceModel
from nap.cache import django_cache, flask_cache
from nap.cache.base import BaseCacheBackend, DEFAULT_TIMEOUT, MAX_CACHE_KEY_LENGTH


class TestBaseCacheBackend(object):

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
        url = """https://a.very.long.url.should.contain.a.famous.quote.such.as.
        Government.of.the people,by.the.people,for.the.people,shall.not.perish.from.the.Earth.
        Hmmm.That.wasnt.long.enough.How.About.
        And.in.the.end,its.not.the.years.in.your.life.that.count..Its.the.life.in.your.years.
        Abraham.Lincoln.com"""
        assert len(url) > MAX_CACHE_KEY_LENGTH
        cache_backend.get_cache_key(SampleResourceModel, url)
        obj = SampleResourceModel(
            title='expected_title',
            content='Blank Content'
        )
        expected_key = 'note::2c0d407be28bba0d46a37a91ac525e71'
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

        uri = SampleResourceModel.objects.get_lookup_url(resource_obj=obj, **kwargs)
        url = SampleResourceModel.objects.get_full_url(uri)
        key = cache_backend.get_cache_key(SampleResourceModel, url)
        assert key == "note::http://foo.com/v1/expected_title/?a_list=5&a_list=4&a_list=3&b=2&c=1"

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
