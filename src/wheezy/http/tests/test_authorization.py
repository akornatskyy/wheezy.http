"""
"""

import unittest
from unittest.mock import Mock

from wheezy.http.authorization import secure


class SecureTestCase(unittest.TestCase):
    """Test the ``secure``."""

    def test_check_not_secure(self):
        """Check if request is not secure.

        @secure
        def my_view(request):
            ...
        """
        mock_request = Mock()
        mock_request.secure = False
        mock_request.urlparts = (
            "http",
            "localhost:8080",
            "/en/signin",
            None,
            None,
        )
        mock_method = Mock()
        handler = secure()(mock_method)
        response = handler(mock_request)
        assert 301 == response.status_code
        location = dict(response.headers)["Location"]
        assert "https://localhost:8080/en/signin" == location

    def test_check_secure(self):
        """Check if request is secure."""
        mock_request = Mock()
        mock_request.secure = True
        mock_method = Mock(return_value="response")
        handler = secure()(mock_method)
        assert "response" == handler(mock_request)

    def test_check_not_enabled(self):
        """Check if request is secure."""
        mock_request = Mock()
        mock_method = Mock(return_value="response")
        handler = secure(enabled=False)(mock_method)
        assert "response" == handler(mock_request)

    def test_wrapped(self):
        """Check decorators"""
        mock_request = Mock()
        mock_request.secure = True

        @secure
        def my_view(self):
            return "response"

        assert "response" == my_view(mock_request)
