from __future__ import unicode_literals
from __future__ import absolute_import
import re
from .middleware import BaseMiddleware


class BaseAuthorization(BaseMiddleware):
    pass


class HttpAuthorization(BaseAuthorization):

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def handle_request(self, request):
        request.auth = (self.username, self.password)

        return request


class FoauthAuthorization(BaseAuthorization):

    def __init__(self, email, password):
        self.email = email
        self.password = password

    def handle_request(self, request):
        self.orig_url = request.url
        pattern = r'https?://'
        new_url = "https://foauth.org/%s" % re.sub(pattern, '', request.url)
        request.auth = (self.email, self.password)
        if request.method == 'PATCH':
            request.headers['X-HTTP-Method-Override'] = 'PATCH'
            request.method = 'POST'

        request.url = new_url

        return request
