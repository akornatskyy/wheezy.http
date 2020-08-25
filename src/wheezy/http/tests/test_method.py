""" Unit tests for ``wheezy.http.method``.
"""

import unittest

from mock import Mock


class AcceptMethodTestCase(unittest.TestCase):
    """Test the ``accept_method`` decorator."""

    def test_exact_strategy(self):
        """A single HTTP method constraint check."""
        from wheezy.http.method import accept_method
        from wheezy.http.response import HTTPResponse

        mock_request = Mock()
        mock_handler = Mock(return_value=HTTPResponse())

        for method in ["GET", "HEAD", "POST", "PUT"]:
            mock_request.reset_mock()
            mock_request.method = method
            handler = accept_method(method)(mock_handler)
            response = handler(mock_request)
            assert 200 == response.status_code

        for method in ["HEAD", "POST", "PUT"]:
            mock_request.reset_mock()
            mock_request.method = method
            handler = accept_method("GET")(mock_handler)
            response = handler(mock_request)
            assert 405 == response.status_code

    def test_one_of_strategy(self):
        """Multiple HTTP methods constraint check."""
        from wheezy.http.method import accept_method
        from wheezy.http.response import HTTPResponse

        mock_request = Mock()
        mock_handler = Mock(return_value=HTTPResponse())

        for method in ["GET", "HEAD"]:
            mock_request.reset_mock()
            mock_request.method = method
            handler = accept_method(("GET", "HEAD"))(mock_handler)
            response = handler(mock_request)
            assert 200 == response.status_code

        for method in ["POST", "PUT"]:
            mock_request.reset_mock()
            mock_request.method = method
            handler = accept_method(("GET", "HEAD"))(mock_handler)
            response = handler(mock_request)
            assert 405 == response.status_code
