
""" Unit tests for ``wheezy.http.response``.
"""

import unittest

from mock import patch


class ShortcutsTestCase(unittest.TestCase):
    """ Test various response shortcuts.
    """

    @patch('wheezy.core.json.json_encode')
    def test_json_response(self, mock_json_encode):
        """
        """
        from wheezy.http.response import json_response
        mock_json_encode.return_value = '{}'

        response = json_response({})

        assert 'application/json; charset=UTF-8' == response.content_type
        assert 1 == len(response.buffer)
