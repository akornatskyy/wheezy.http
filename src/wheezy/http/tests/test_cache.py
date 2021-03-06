""" Unit tests for ``wheezy.http.cache``.
"""

import unittest
from datetime import datetime
from hashlib import md5
from unittest.mock import Mock

from wheezy.http.cache import (
    CacheableResponse,
    NotModifiedResponse,
    SurfaceResponse,
    etag_md5,
    etag_md5crc32,
    make_etag,
    make_etag_crc32,
    response_cache,
    wsgi_cache,
)
from wheezy.http.cachepolicy import HTTPCachePolicy
from wheezy.http.cacheprofile import CacheProfile
from wheezy.http.response import HTTPResponse


class ResponseCacheDecoratorTestCase(unittest.TestCase):
    """Test the ``response_cache`` decorator."""

    def test_none_cache_profile(self):
        """If cache profile is not set use none_cache_profile."""
        mock_response = Mock()
        mock_response.cache_profile = None
        mock_handler = Mock(return_value=mock_response)

        handler = response_cache()(mock_handler)

        mock_response.cache_profile = "x"
        # cache_policy is not set by handler
        mock_response.cache_policy = None
        response = handler("request")
        assert not response.cache_profile
        assert response.cache_policy

    def test_cache_profile_not_enabled(self):
        """If cache profile if not enabled return handler
        without any decoration.
        """
        profile = CacheProfile("none", enabled=False)

        handler = response_cache(profile)("handler")

        assert "handler" == handler

    def test_etag_strategy(self):
        """If cache profile has defined `request_vary`
        than response.cache_profile needs to be set.

        With etag_func set apply it to response buffer
        and set cache policy etag.

        Must not override cache_policy if it has been
        set already.
        """
        profile = CacheProfile("both", duration=100, etag_func=etag_md5crc32)
        mock_response = Mock()
        mock_response.buffer = [b"test"]
        mock_handler = Mock(return_value=mock_response)

        handler = response_cache(profile)(mock_handler)

        # cache_policy is not set by handler
        mock_response.cache_policy = None
        response = handler("request")

        assert mock_response == response
        mock_handler.assert_called_once_with("request")
        assert profile == mock_response.cache_profile
        assert '"fece0556"' == response.cache_policy.http_etag

        # cache_policy is set by handler
        mock_response.reset_mock()
        mock_response.cache_policy = "policy"
        response = handler("request")

        assert profile == mock_response.cache_profile
        assert "policy" != mock_response.cache_policy

    def test_cache_strategy(self):
        """If cache profile has defined `request_vary`
        than response.cache_profile needs to be set.

        Must not override cache_policy if it has been
        set already.
        """
        profile = CacheProfile("server", duration=100)
        policy = profile.cache_policy()
        mock_response = Mock()
        mock_handler = Mock(return_value=mock_response)

        handler = response_cache(profile)(mock_handler)

        # cache_policy is not set by handler
        mock_response.cache_policy = None
        response = handler("request")

        assert mock_response == response
        mock_handler.assert_called_once_with("request")
        assert profile == mock_response.cache_profile
        assert policy == mock_response.cache_policy

        # cache_policy is set by handler
        mock_response.reset_mock()
        mock_response.cache_policy = "policy"
        response = handler("request")

        assert profile == mock_response.cache_profile
        assert policy == mock_response.cache_policy

    def test_no_cache_strategy(self):
        """If cache profile has not defined `request_vary`
        than proceed with no cache strategy.

        Must not override cache_policy if it has been
        set already.
        """
        profile = CacheProfile("none")
        policy = profile.cache_policy()
        mock_response = Mock()
        mock_response.cache_profile = None
        mock_handler = Mock(return_value=mock_response)

        handler = response_cache(profile)(mock_handler)

        # cache_policy is not set by handler
        mock_response.cache_policy = None
        response = handler("request")

        assert mock_response == response
        mock_handler.assert_called_once_with("request")
        assert mock_response.cache_profile is None
        assert policy == mock_response.cache_policy

        # cache_policy is set by handler
        mock_response.reset_mock()
        mock_response.cache_policy = "policy"
        response = handler("request")

        assert mock_response.cache_profile is None
        assert policy == mock_response.cache_policy


class WSGICacheDecoratorTestCase(unittest.TestCase):
    """Test the ``wsgi_cache`` decorator."""

    def test_cache_profile_not_enabled(self):
        """If cache profile if not enabled return WSGI app
        without any decoration.
        """
        profile = CacheProfile("none", enabled=False)
        assert "app" == wsgi_cache(profile)("app")

    def test_cache_profile(self):
        """Ensure cache profile is set into environ."""

        def wsgi_app(environ, start_response):
            return []

        profile = CacheProfile("none", enabled=True)
        app = wsgi_cache(profile)(wsgi_app)
        environ = {}
        app(environ, None)
        assert profile == environ["wheezy.http.cache_profile"]


class ETagTestCase(unittest.TestCase):
    """Test the ETag builders."""

    def test_make_etag(self):
        """Ensure valid ETag."""

        etag = make_etag(md5)

        buf = [b"test"] * 10
        assert (
            '"44663634ef2148fa1ecc9419c33063e4"' == etag(buf) == etag_md5(buf)
        )

    def test_make_etag_crc32(self):
        """Ensure valid ETag from crc32."""
        etag = make_etag_crc32(md5)

        buf = [b"test"] * 10
        assert '"a57e3ecb"' == etag(buf) == etag_md5crc32(buf)


class SurfaceResponseTestCase(unittest.TestCase):
    """Test the ``SurfaceResponse``."""

    def test_call_status_code(self):
        """Ensure valid HTTP status code."""
        self.response = HTTPResponse()
        self.response.write("test")
        mock_start_response = Mock()
        self.response(mock_start_response)

        mock_start_response.reset_mock()
        r = SurfaceResponse(self.response)

        result = r(mock_start_response)

        assert result == self.response.buffer
        status, headers = mock_start_response.call_args[0]
        assert "200 OK" == status
        assert headers == self.response.headers
        assert 3 == len(headers)


class NotModifiedResponseTestCase(unittest.TestCase):
    """Test the ``NotModifiedResponse``."""

    def setUp(self):
        self.response = HTTPResponse()
        self.response.write("test")

    def test_call_status_code(self):
        """Ensure valid HTTP status code."""
        mock_start_response = Mock()
        self.response(mock_start_response)

        mock_start_response.reset_mock()
        not_modified_response = NotModifiedResponse(self.response)
        assert 304 == not_modified_response.status_code

        result = not_modified_response(mock_start_response)

        assert [] == result
        status, headers = mock_start_response.call_args[0]
        assert "304 Not Modified" == status
        assert 2 == len(headers)

    def test_filter_content_length(self):
        """Ensure Content-Length HTTP header is filtered out"""
        mock_start_response = Mock()

        not_modified_response = NotModifiedResponse(self.response)
        not_modified_response(mock_start_response)

        status, headers = mock_start_response.call_args[0]
        assert "304 Not Modified" == status
        assert not [n for n, v in headers if n == "Content-Length"]


class CacheableResponseTestCase(unittest.TestCase):
    """Test the ``CacheableResponse``."""

    def setUp(self):
        self.response = HTTPResponse()
        self.response.write("test-1")
        self.response.write("test-2")

    def test_init_no_cache_policy(self):
        """Ensure HTTP headers and response body are captured."""
        cacheable_response = CacheableResponse(self.response)

        assert 200 == cacheable_response.status_code
        assert cacheable_response.last_modified is None
        assert cacheable_response.etag is None
        assert self.response.headers == cacheable_response.headers
        assert tuple(self.response.buffer) == cacheable_response.buffer

    def test_init_cache_policy(self):
        """Ensure HTTP cache policy values last_modified and etag
        are captured.
        """
        cache_policy = HTTPCachePolicy("public")
        when = datetime(2012, 4, 13, 12, 55)
        cache_policy.last_modified(when)
        cache_policy.etag("4f87f242")
        self.response.cache_policy = cache_policy
        cacheable_response = CacheableResponse(self.response)

        assert when == cacheable_response.last_modified
        assert "4f87f242" == cacheable_response.etag

    def test_call_status_code(self):
        """Ensure valid HTTP status code."""
        mock_start_response = Mock()

        cacheable_response = CacheableResponse(self.response)
        assert 200 == cacheable_response.status_code

        result = cacheable_response(mock_start_response)

        assert (b"test-1", b"test-2") == result
        status, headers = mock_start_response.call_args[0]
        assert "200 OK" == status
        assert 3 == len(headers)

    def test_filter_set_cookie(self):
        """Ensure Set-Cookie HTTP headers are filtered out"""
        mock_start_response = Mock()

        self.response.headers.append(("Set-Cookie", ""))
        cacheable_response = CacheableResponse(self.response)
        assert 200 == cacheable_response.status_code

        cacheable_response(mock_start_response)

        status, headers = mock_start_response.call_args[0]
        assert "200 OK" == status
        assert not [n for n, v in headers if n == "Set-Cookie"]
