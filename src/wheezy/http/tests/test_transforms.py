""" Unit tests for ``wheezy.http.cache``.
"""

import unittest
from unittest.mock import Mock

from wheezy.http.transforms import gzip_transform, response_transforms


class GzipTransformTestCase(unittest.TestCase):
    """Test the ``gzip_transform`` decorator."""

    def test_too_small_content(self):
        """Content length is less than min_length."""
        mock_request = Mock()
        mock_response = Mock()
        mock_response.buffer = ["x"]

        transform = gzip_transform()
        response = transform(mock_request, mock_response)

        assert response == mock_response

    def test_unsupported_protocol(self):
        """Server protocol is not HTTP/1.1"""
        mock_request = Mock()
        mock_request.environ = {"SERVER_PROTOCOL": "HTTP/1.0"}
        mock_response = Mock()
        mock_response.buffer = ["test"]

        transform = gzip_transform(min_length=4)
        response = transform(mock_request, mock_response)

        assert response == mock_response

    def test_unsupported_content_type(self):
        """Response content type is not valid for gzip."""
        mock_request = Mock()
        mock_request.environ = {"SERVER_PROTOCOL": "HTTP/1.1"}
        mock_response = Mock()
        mock_response.buffer = ["test"]
        mock_response.content_type = "image/png"

        transform = gzip_transform(min_length=4)
        response = transform(mock_request, mock_response)

        assert response == mock_response

    def test_browser_not_accepting(self):
        """gzip is not is browser supported encoding."""
        mock_request = Mock()
        mock_request.environ = {
            "SERVER_PROTOCOL": "HTTP/1.1",
            "HTTP_ACCEPT_ENCODING": "deflate",
        }
        mock_response = Mock()
        mock_response.buffer = ["test"]
        mock_response.content_type = "text/css"

        transform = gzip_transform(min_length=4)
        response = transform(mock_request, mock_response)

        assert response == mock_response

    def test_compress(self):
        """compress"""
        for content_type in (
            "text/css",
            "text/html",
            "application/json",
            "application/x-javascript",
        ):
            mock_request = Mock()
            mock_request.environ = {
                "SERVER_PROTOCOL": "HTTP/1.1",
                "HTTP_ACCEPT_ENCODING": "gzip, deflate",
            }
            mock_response = Mock()
            mock_response.buffer = [b"test"]
            mock_response.content_type = content_type

            transform = gzip_transform(min_length=4)
            response = transform(mock_request, mock_response)

            assert response == mock_response
            response.headers.append.assert_called_once_with(
                ("Content-Encoding", "gzip")
            )

    def test_compress_and_vary(self):
        """compress and vary"""
        mock_request = Mock()
        mock_request.environ = {
            "SERVER_PROTOCOL": "HTTP/1.1",
            "HTTP_ACCEPT_ENCODING": "gzip, deflate",
        }
        mock_response = Mock()
        mock_response.buffer = [b"test"]
        mock_response.content_type = "text/css"
        mock_cache_policy = Mock()
        mock_cache_policy.is_public = True
        mock_response.cache_policy = mock_cache_policy

        transform = gzip_transform(min_length=4, vary=True)
        transform(mock_request, mock_response)

        mock_cache_policy.vary.assert_called_once_with("Accept-Encoding")


class ResponseTransformsTestCase(unittest.TestCase):
    """Test the ``response_transforms`` decorator."""

    def test_transforms_is_empty(self):
        """Raises AssertionError."""
        self.assertRaises(AssertionError, lambda: response_transforms())

    def test_single_transform(self):
        """single transform strategy."""

        def transform(request, response):
            return response + "-transform"

        mock_factory = Mock(return_value="response")
        mock_request = Mock()
        handler = response_transforms(transform)(mock_factory)

        assert "response-transform" == handler(mock_request)

    def test_multi_transform(self):
        """multi transform strategy."""

        def transform1(request, response):
            return response + "-1"

        def transform2(request, response):
            return response + "-2"

        mock_factory = Mock(return_value="response")
        mock_request = Mock()
        handler = response_transforms(transform1, transform2)(mock_factory)

        assert "response-1-2" == handler(mock_request)
