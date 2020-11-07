""" Unit tests for ``wheezy.http.response``.
"""

import unittest

from mock import patch


class ShortcutsTestCase(unittest.TestCase):
    """Test various response shortcuts."""

    def test_json_response(self):
        """json_response"""
        from wheezy.http import response
        from wheezy.http.response import json_response

        patcher = patch.object(response, "json_encode")
        mock_json_encode = patcher.start()
        mock_json_encode.return_value = "{}"

        response = json_response({})

        patcher.stop()
        assert "application/json; charset=UTF-8" == response.content_type
        assert [b"{}"] == response.buffer
        mock_json_encode.assert_called_once_with({})

        assert "200 OK" == response.get_status()
