import unittest
from unittest.mock import patch

from wheezy.http import response
from wheezy.http.response import json_response


class ShortcutsTestCase(unittest.TestCase):
    """Test various response shortcuts."""

    def test_json_response(self):
        """json_response"""
        patcher = patch.object(response, "json_encode")
        mock_json_encode = patcher.start()
        mock_json_encode.return_value = "{}"

        res = json_response({})

        patcher.stop()
        assert "application/json; charset=UTF-8" == res.content_type
        assert [b"{}"] == res.buffer
        mock_json_encode.assert_called_once_with({})

        assert "200 OK" == res.get_status()
