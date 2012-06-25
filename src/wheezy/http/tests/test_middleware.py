
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
        from wheezy.http.middleware import http_cache_middleware_factory
        options = {
            'http_cache_factory': 'cache_factory',
            'http_cache_middleware_vary': 'middleware_vary'
        }

        middleware = http_cache_middleware_factory(options)
        assert 'cache_factory' == middleware.cache_factory
        assert 'middleware_vary' == middleware.middleware_vary

        del options['http_cache_middleware_vary']
        middleware = http_cache_middleware_factory(options)
        assert middleware.middleware_vary

        del options['http_cache_factory']
        self.assertRaises(KeyError,
                          lambda: http_cache_middleware_factory(options))


class HTTPCacheMiddlewareTestCase(unittest.TestCase):
    """ Test the ``HTTPCacheMiddleware``.
    """

    def setUp(self):
        from wheezy.http.middleware import http_cache_middleware_factory
        from wheezy.http.response import HTTPResponse
        self.mock_cache = Mock()
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=self.mock_cache)
        mock_context.__exit__ = Mock()
        mock_cache_factory = Mock(return_value=mock_context)
        options = {
            'http_cache_factory': mock_cache_factory
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
            3. has cache dependency.
        """
        from wheezy.http.cache import CacheableResponse
        from wheezy.http.cacheprofile import CacheProfile
        self.response.status_code = 200
        self.response.cache_profile = CacheProfile('server', duration=60)
        mock_dependency = Mock()
        mock_dependency.next_key.return_value = 'x'
        self.response.dependency = mock_dependency

        response = self.middleware(self.mock_request, self.mock_following)

        self.mock_following.assert_called_once_with(self.mock_request)
        assert isinstance(response, CacheableResponse)
        assert self.mock_cache.set_multi.called

    def test_cacheprofile_is_known(self):
        """ Cache profile for the incoming request is known.
        """
        from wheezy.http.cacheprofile import CacheProfile
        self.middleware.profiles['CG/abc'] = CacheProfile('both', duration=60)

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
        self.middleware.profiles['CG/abc'] = CacheProfile('both', duration=60)
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
        self.middleware.profiles['CG/abc'] = CacheProfile('both', duration=60)
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
