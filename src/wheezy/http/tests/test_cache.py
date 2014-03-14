
""" Unit tests for ``wheezy.http.cache``.
"""

import unittest

from mock import Mock


class ResponseCacheDecoratorTestCase(unittest.TestCase):
    """ Test the ``response_cache`` decorator.
    """

    def test_none_cache_profile(self):
        """ If cache profile is not set use none_cache_profile.
        """
        from wheezy.http.cache import response_cache
        mock_response = Mock()
        mock_response.cache_profile = None
        mock_handler = Mock(return_value=mock_response)

        handler = response_cache()(mock_handler)

        mock_response.cache_profile = 'x'
        # cache_policy is not set by handler
        mock_response.cache_policy = None
        response = handler('request')
        assert not response.cache_profile
        assert response.cache_policy

    def test_cache_profile_not_enabled(self):
        """ If cache profile if not enabled return handler
            without any decoration.
        """
        from wheezy.http.cacheprofile import CacheProfile
        from wheezy.http.cache import response_cache
        profile = CacheProfile('none', enabled=False)

        handler = response_cache(profile)('handler')

        assert 'handler' == handler

    def test_etag_strategy(self):
        """ If cache profile has defined `request_vary`
            than response.cache_profile needs to be set.

            With etag_func set apply it to response buffer
            and set cache policy etag.

            Must not override cache_policy if it has been
            set already.
        """
        from wheezy.http.comp import b
        from wheezy.http.cacheprofile import CacheProfile
        from wheezy.http.cache import etag_md5crc32
        from wheezy.http.cache import response_cache
        profile = CacheProfile('both', duration=100,
                               etag_func=etag_md5crc32)
        mock_response = Mock()
        mock_response.buffer = [b('test')]
        mock_handler = Mock(return_value=mock_response)

        handler = response_cache(profile)(mock_handler)

        # cache_policy is not set by handler
        mock_response.cache_policy = None
        response = handler('request')

        assert mock_response == response
        mock_handler.assert_called_once_with('request')
        assert profile == mock_response.cache_profile
        assert '"fece0556"' == response.cache_policy.http_etag

        # cache_policy is set by handler
        mock_response.reset_mock()
        mock_response.cache_policy = 'policy'
        response = handler('request')

        assert profile == mock_response.cache_profile
        assert 'policy' != mock_response.cache_policy

    def test_cache_strategy(self):
        """ If cache profile has defined `request_vary`
            than response.cache_profile needs to be set.

            Must not override cache_policy if it has been
            set already.
        """
        from wheezy.http.cacheprofile import CacheProfile
        from wheezy.http.cache import response_cache
        profile = CacheProfile('server', duration=100)
        policy = profile.cache_policy()
        mock_response = Mock()
        mock_handler = Mock(return_value=mock_response)

        handler = response_cache(profile)(mock_handler)

        # cache_policy is not set by handler
        mock_response.cache_policy = None
        response = handler('request')

        assert mock_response == response
        mock_handler.assert_called_once_with('request')
        assert profile == mock_response.cache_profile
        assert policy == mock_response.cache_policy

        # cache_policy is set by handler
        mock_response.reset_mock()
        mock_response.cache_policy = 'policy'
        response = handler('request')

        assert profile == mock_response.cache_profile
        assert policy == mock_response.cache_policy

    def test_no_cache_strategy(self):
        """ If cache profile has not defined `request_vary`
            than proceed with no cache strategy.

            Must not override cache_policy if it has been
            set already.
        """
        from wheezy.http.cacheprofile import CacheProfile
        from wheezy.http.cache import response_cache
        profile = CacheProfile('none')
        policy = profile.cache_policy()
        mock_response = Mock()
        mock_response.cache_profile = None
        mock_handler = Mock(return_value=mock_response)

        handler = response_cache(profile)(mock_handler)

        # cache_policy is not set by handler
        mock_response.cache_policy = None
        response = handler('request')

        assert mock_response == response
        mock_handler.assert_called_once_with('request')
        assert None == mock_response.cache_profile
        assert policy == mock_response.cache_policy

        # cache_policy is set by handler
        mock_response.reset_mock()
        mock_response.cache_policy = 'policy'
        response = handler('request')

        assert None == mock_response.cache_profile
        assert policy == mock_response.cache_policy


class WSGICacheDecoratorTestCase(unittest.TestCase):
    """ Test the ``wsgi_cache`` decorator.
    """

    def test_cache_profile_not_enabled(self):
        """ If cache profile if not enabled return WSGI app
            without any decoration.
        """
        from wheezy.http.cacheprofile import CacheProfile
        from wheezy.http.cache import wsgi_cache

        profile = CacheProfile('none', enabled=False)
        assert 'app' == wsgi_cache(profile=profile)('app')

    def test_cache_profile(self):
        """ Ensure cache profile is set into environ.
        """
        from wheezy.http.cacheprofile import CacheProfile
        from wheezy.http.cache import wsgi_cache

        def wsgi_app(environ, start_response):
            return []

        profile = CacheProfile('none', enabled=True)
        app = wsgi_cache(profile=profile)(wsgi_app)
        environ = {}
        app(environ, None)
        assert profile == environ['wheezy.http.cache_profile']


class ETagTestCase(unittest.TestCase):
    """ Test the ETag builders.
    """

    def test_make_etag(self):
        """ Ensure valid ETag.
        """
        from wheezy.http.comp import b
        from wheezy.http.comp import md5
        from wheezy.http.cache import make_etag
        from wheezy.http.cache import etag_md5
        etag = make_etag(md5)

        buf = [b('test')] * 10
        assert '"44663634ef2148fa1ecc9419c33063e4"' == \
            etag(buf) == etag_md5(buf)

    def test_make_etag_crc32(self):
        """ Ensure valid ETag from crc32.
        """
        from wheezy.http.comp import b
        from wheezy.http.comp import md5
        from wheezy.http.cache import make_etag_crc32
        from wheezy.http.cache import etag_md5crc32
        etag = make_etag_crc32(md5)

        buf = [b('test')] * 10
        assert '"a57e3ecb"' == etag(buf) == etag_md5crc32(buf)


class NotModifiedResponseTestCase(unittest.TestCase):
    """ Test the ``NotModifiedResponse``.
    """

    def setUp(self):
        from wheezy.http.response import HTTPResponse
        self.response = HTTPResponse()
        self.response.write('test')

    def test_call_status_code(self):
        """ Ensure valid HTTP status code.
        """
        from wheezy.http.cache import NotModifiedResponse
        mock_start_response = Mock()
        self.response(mock_start_response)

        mock_start_response.reset_mock()
        not_modified_response = NotModifiedResponse(self.response)
        assert 304 == not_modified_response.status_code

        result = not_modified_response(mock_start_response)

        assert [] == result
        status, headers = mock_start_response.call_args[0]
        assert '304 Not Modified' == status


class CacheableResponseTestCase(unittest.TestCase):
    """ Test the ``CacheableResponse``.
    """

    def setUp(self):
        from wheezy.http.response import HTTPResponse
        self.response = HTTPResponse()
        self.response.write('test-1')
        self.response.write('test-2')

    def test_init_no_cache_policy(self):
        """ Ensure HTTP headers and response body are captured.
        """
        from wheezy.http.cache import CacheableResponse
        cacheable_response = CacheableResponse(self.response)

        assert 200 == cacheable_response.status_code
        assert None == cacheable_response.last_modified
        assert None == cacheable_response.etag
        assert self.response.headers == cacheable_response.headers
        assert tuple(self.response.buffer) == cacheable_response.buffer

    def test_init_cache_policy(self):
        """ Ensure HTTP cache policy values last_modified and etag
            are captured.
        """
        from datetime import datetime
        from wheezy.http.cache import CacheableResponse
        from wheezy.http.cachepolicy import HTTPCachePolicy
        cache_policy = HTTPCachePolicy('public')
        when = datetime(2012, 4, 13, 12, 55)
        cache_policy.last_modified(when)
        cache_policy.etag('4f87f242')
        self.response.cache_policy = cache_policy
        cacheable_response = CacheableResponse(self.response)

        assert when == cacheable_response.last_modified
        assert '4f87f242' == cacheable_response.etag

    def test_call_status_code(self):
        """ Ensure valid HTTP status code.
        """
        from wheezy.http.comp import b
        from wheezy.http.cache import CacheableResponse
        mock_start_response = Mock()
        self.response(mock_start_response)

        mock_start_response.reset_mock()
        cacheable_response = CacheableResponse(self.response)
        assert 200 == cacheable_response.status_code

        result = cacheable_response(mock_start_response)

        assert (b('test-1'), b('test-2')) == result
        status, headers = mock_start_response.call_args[0]
        assert '200 OK' == status
