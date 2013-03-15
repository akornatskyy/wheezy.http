
""" Unit tests for ``wheezy.http.middleware``.
"""

import unittest

from mock import Mock


class HTTPCacheMiddlewareFactoryTestCase(unittest.TestCase):
    """ Test the ``http_cache_middleware_factory``.
    """

    def test_required_options(self):
        """ Ensure raises KeyError if required configuration option is
            missing.
        """
        from wheezy.http.cacheprofile import RequestVary
        from wheezy.http.middleware import http_cache_middleware_factory

        class Cache(object):
            get = incr = set = set_multi = None

        cache = Cache()
        middleware_vary = RequestVary()
        options = {
            'http_cache': cache,
            'http_cache_middleware_vary': middleware_vary
        }

        middleware = http_cache_middleware_factory(options)
        assert cache == middleware.cache
        assert middleware_vary.key == middleware.key

        del options['http_cache_middleware_vary']
        middleware = http_cache_middleware_factory(options)
        assert middleware.key

        del options['http_cache']
        self.assertRaises(KeyError,
                          lambda: http_cache_middleware_factory(options))


class HTTPCacheMiddlewareTestCase(unittest.TestCase):
    """ Test the ``HTTPCacheMiddleware``.
    """

    def setUp(self):
        from wheezy.http.middleware import http_cache_middleware_factory
        from wheezy.http.response import HTTPResponse
        self.mock_cache = Mock()
        options = {
            'http_cache': self.mock_cache
        }
        self.middleware = http_cache_middleware_factory(options)
        self.mock_request = Mock()
        self.mock_request.method = 'GET'
        self.mock_request.environ = {'PATH_INFO': '/abc'}
        self.response = HTTPResponse()
        self.mock_following = Mock(return_value=self.response)

    def test_following_response_status_code_not_200(self):
        """ HTTP response status codes other than 200 are ignored.
        """
        for status_code in [301, 403, 405, 500]:
            self.mock_following.reset_mock()
            self.response.status_code = status_code

            response = self.middleware(self.mock_request, self.mock_following)

            self.mock_following.assert_called_once_with(self.mock_request)
            assert status_code == response.status_code

    def test_following_response_has_no_cache_profile(self):
        """ HTTP response status codes is 200 but has no cache profile.
        """
        self.response.status_code = 200
        self.response.cache_profile = None

        response = self.middleware(self.mock_request, self.mock_following)

        self.mock_following.assert_called_once_with(self.mock_request)
        assert response is self.response

    def test_cache_response(self):
        """ HTTP response status codes is 200 and has cache profile.
        """
        from wheezy.http.cache import CacheableResponse
        from wheezy.http.cacheprofile import CacheProfile
        self.response.status_code = 200
        self.response.cache_profile = CacheProfile('server', duration=60)

        response = self.middleware(self.mock_request, self.mock_following)

        self.mock_following.assert_called_once_with(self.mock_request)
        assert isinstance(response, CacheableResponse)
        assert self.mock_cache.set.called

    def test_cache_response_with_dependency(self):
        """ HTTP response:
            1. status codes is 200
            2. has cache profile
            3. has cache dependency key.
        """
        from wheezy.http.cache import CacheableResponse
        from wheezy.http.cacheprofile import CacheProfile
        self.response.status_code = 200
        self.response.cache_profile = CacheProfile('server', duration=60)
        self.response.cache_dependency.append('master_key')

        response = self.middleware(self.mock_request, self.mock_following)

        self.mock_following.assert_called_once_with(self.mock_request)
        assert isinstance(response, CacheableResponse)
        self.mock_cache.incr.assert_called_once_with('master_key', 1, None, 0)
        assert self.mock_cache.set_multi.called

    def test_cacheprofile_is_known(self):
        """ Cache profile for the incoming request is known.
        """
        from wheezy.http.cacheprofile import CacheProfile
        self.middleware.profiles['G/abc'] = CacheProfile('both', duration=60)

        mock_cache_response = Mock()
        self.mock_cache.get.return_value = mock_cache_response
        response = self.middleware(self.mock_request, self.mock_following)

        assert not self.mock_following.called
        assert mock_cache_response == response

    def test_cacheprofile_is_known_etag_match(self):
        """ Cache profile for the incoming request is known and match etag.
        """
        from wheezy.http.cache import NotModifiedResponse
        from wheezy.http.cacheprofile import CacheProfile
        self.middleware.profiles['G/abc'] = CacheProfile('both', duration=60)
        self.mock_request.environ = {
            'PATH_INFO': '/abc',
            'HTTP_IF_NONE_MATCH': '5d34ab31'
        }
        self.response.etag = '5d34ab31'
        self.mock_cache.get.return_value = self.response
        response = self.middleware(self.mock_request, self.mock_following)

        assert not self.mock_following.called
        assert isinstance(response, NotModifiedResponse)

    def test_cacheprofile_is_known_if_modified_check(self):
        """ Cache profile for the incoming request is known and
            HTTP request header If-Modified-Since is supplied but
            response was not modified since.
        """
        from datetime import datetime
        from wheezy.http.cache import NotModifiedResponse
        from wheezy.http.cacheprofile import CacheProfile
        self.middleware.profiles['G/abc'] = CacheProfile('both', duration=60)
        self.mock_request.environ = {
            'PATH_INFO': '/abc',
            'HTTP_IF_MODIFIED_SINCE': 'Tue, 17 Apr 2012 09:58:27 GMT'
        }
        self.response.etag = None
        self.response.last_modified = datetime(2012, 4, 17, 9, 0, 0)
        self.mock_cache.get.return_value = self.response
        response = self.middleware(self.mock_request, self.mock_following)

        assert not self.mock_following.called
        assert isinstance(response, NotModifiedResponse)

    def test_cache_if_modified_check(self):
        """ Return HTTP 304 if response is cached and there is a valid
            HTTP request header If-Modified-Since.
        """
        from datetime import datetime
        from wheezy.http.cache import NotModifiedResponse
        from wheezy.http.cacheprofile import CacheProfile
        self.mock_request.environ = {
            'PATH_INFO': '/abc',
            'HTTP_IF_MODIFIED_SINCE': 'Tue, 17 Apr 2012 09:58:27 GMT'
        }
        self.response.status_code = 200

        profile = CacheProfile('both', duration=60)
        self.response.cache_profile = profile

        policy = profile.client_policy()
        policy.last_modified(datetime(2012, 4, 17, 9, 0, 0))
        self.response.cache_policy = policy

        response = self.middleware(self.mock_request, self.mock_following)
        self.mock_following.assert_called_once_with(self.mock_request)
        assert self.mock_cache.set.called
        assert isinstance(response, NotModifiedResponse)

    def test_cache_etag_match_check(self):
        """ Return HTTP 304 if response is cached and there is a valid
            HTTP request header If-None-Match.
        """
        from wheezy.http.cache import NotModifiedResponse
        from wheezy.http.cacheprofile import CacheProfile
        self.mock_request.environ = {
            'PATH_INFO': '/abc',
            'HTTP_IF_NONE_MATCH': '5d34ab31'
        }
        self.response.status_code = 200

        profile = CacheProfile('public', duration=60)
        self.response.cache_profile = profile

        policy = profile.client_policy()
        policy.etag('5d34ab31')
        self.response.cache_policy = policy

        response = self.middleware(self.mock_request, self.mock_following)
        self.mock_following.assert_called_once_with(self.mock_request)
        assert self.mock_cache.set.called
        assert isinstance(response, NotModifiedResponse)


class WSGIAdapterMiddlewareFactoryTestCase(unittest.TestCase):
    """ Test the ``wsgi_adapter_middleware_factory``.
    """

    def test_required_options(self):
        """ Ensure raises KeyError if required configuration option is
            missing.
        """
        from wheezy.http.middleware import wsgi_adapter_middleware_factory
        options = {
            'wsgi_app': 'app',
        }

        middleware = wsgi_adapter_middleware_factory(options)
        assert 'app' == middleware.wsgi_app

        del options['wsgi_app']
        self.assertRaises(KeyError,
                          lambda: wsgi_adapter_middleware_factory(options))


class WSGIAdapterMiddlewareTestCase(unittest.TestCase):
    """ Test the ``wsgi_adapter_middleware``.
    """

    def test_response(self):
        """ Ensure raises KeyError if required configuration option is
            missing.
        """
        from wheezy.http.comp import b
        from wheezy.http.request import HTTPRequest
        from wheezy.http.middleware import WSGIAdapterMiddleware

        def wsgi_app(environ, start_response):
            start_response('200 OK', [('Content-Type', 'text/plain')])
            return [b('Hello')]

        middleware = WSGIAdapterMiddleware(wsgi_app)
        request = HTTPRequest({'REQUEST_METHOD': 'GET'}, None, None)
        response = middleware(request, None)
        assert response


class EnvironCacheAdapterMiddlewareFactoryTestCase(unittest.TestCase):
    """ Test the ``environ_cache_adapter_middleware_factory``.
    """

    def test_required_options(self):
        """ Ensure raises KeyError if required configuration option is
            missing.
        """
        from wheezy.http.middleware import \
            environ_cache_adapter_middleware_factory
        options = {
        }

        middleware = environ_cache_adapter_middleware_factory(options)
        assert middleware


class EnvironCacheAdapterMiddlewareTestCase(unittest.TestCase):
    """ Test the ``environ_cache_adapter_middleware``.
    """

    def test_none_set(self):
        """ Test cache_policy adapter.
        """
        from wheezy.http.request import HTTPRequest
        from wheezy.http.response import HTTPResponse
        from wheezy.http.middleware import EnvironCacheAdapterMiddleware

        middleware = EnvironCacheAdapterMiddleware()
        request = HTTPRequest({'REQUEST_METHOD': 'GET'}, None, None)
        response = HTTPResponse()
        response = middleware(request, lambda r: response)
        assert not response.cache_policy
        assert not response.cache_profile
        assert not response.cache_dependency

    def test_cache_policy(self):
        """ Test cache_policy adapter.
        """
        from wheezy.http.request import HTTPRequest
        from wheezy.http.response import HTTPResponse
        from wheezy.http.middleware import EnvironCacheAdapterMiddleware

        middleware = EnvironCacheAdapterMiddleware()
        request = HTTPRequest({
            'REQUEST_METHOD': 'GET',
            'wheezy.http.cache_policy': 'policy'
        }, None, None)
        response = HTTPResponse()
        response = middleware(request, lambda r: response)
        assert 'policy' == response.cache_policy

    def test_cache_profile(self):
        """ Test cache_profile adapter.
        """
        from wheezy.http.request import HTTPRequest
        from wheezy.http.response import HTTPResponse
        from wheezy.http.cacheprofile import CacheProfile
        from wheezy.http.middleware import EnvironCacheAdapterMiddleware

        middleware = EnvironCacheAdapterMiddleware()
        request = HTTPRequest({
            'REQUEST_METHOD': 'GET',
            'wheezy.http.cache_profile': CacheProfile('none')
        }, None, None)
        response = HTTPResponse()
        response = middleware(request, lambda r: response)
        assert response.cache_profile
        assert response.cache_policy

    def test_cache_profile_with_policy_override(self):
        """ Test cache_profile adapter in case cache policy
            is overriden.
        """
        from wheezy.http.request import HTTPRequest
        from wheezy.http.response import HTTPResponse
        from wheezy.http.middleware import EnvironCacheAdapterMiddleware

        middleware = EnvironCacheAdapterMiddleware()
        request = HTTPRequest({
            'REQUEST_METHOD': 'GET',
            'wheezy.http.cache_profile': 'profile',
            'wheezy.http.cache_policy': 'policy'
        }, None, None)
        response = HTTPResponse()
        response = middleware(request, lambda r: response)
        assert 'profile' == response.cache_profile
        assert 'policy' == response.cache_policy

    def test_cache_dependency(self):
        """ Test cache dependency adapter.
        """
        from wheezy.http.request import HTTPRequest
        from wheezy.http.response import HTTPResponse
        from wheezy.http.middleware import EnvironCacheAdapterMiddleware

        middleware = EnvironCacheAdapterMiddleware()
        cache_dependency = ['master_key']
        request = HTTPRequest({
            'REQUEST_METHOD': 'GET',
            'wheezy.http.cache_dependency': cache_dependency
        }, None, None)
        response = HTTPResponse()
        response = middleware(request, lambda r: response)
        assert cache_dependency == response.cache_dependency
