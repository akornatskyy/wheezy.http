
""" Unit tests for ``wheezy.http.cache``.
"""

import unittest

from mock import Mock


class ResponseCacheDecoratorTestCase(unittest.TestCase):
    """ Test the ``response_cache`` decorator.
    """

    def test_cache_profile_not_enabled(self):
        """ If cache profile if not enabled return handler
            without any decoration.
        """
        from wheezy.http.cacheprofile import CacheProfile
        from wheezy.http.cache import response_cache
        profile = CacheProfile('none', enabled=False)

        handler = response_cache(profile)('handler')

        assert 'handler' == handler

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
        assert 'policy' == mock_response.cache_policy

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
        assert 'policy' == mock_response.cache_policy


class NotModifiedResponseTestCase(unittest.TestCase):
    """ Test the ``NotModifiedResponse``.
    """

    def setUp(self):
        from wheezy.http.response import HTTPResponse
        self.response = HTTPResponse()
        self.response.write('test')

    def test_init_content_length_header_is_zero(self):
        """ Content-Length HTTP response header must be zero.
        """
        from wheezy.http.cache import NotModifiedResponse
        mock_start_response = Mock()
        self.response(mock_start_response)

        def content_length(headers):
            return int([header[1] for header in headers
                if header[0] == 'Content-Length'][0])
        assert 4 == content_length(self.response.headers)

        not_modified_response = NotModifiedResponse(self.response)
        assert 0 == content_length(not_modified_response.headers)

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
