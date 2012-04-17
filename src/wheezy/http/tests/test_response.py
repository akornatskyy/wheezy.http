
""" Unit tests for ``wheezy.http.response``.
"""

import unittest

from mock import Mock


class ShortcutsTestCase(unittest.TestCase):
    """ Test various response shortcuts.
    """

    def test_json_response(self):
        """ json_response
        """
        from wheezy.http import response
        from wheezy.http.comp import b
        from wheezy.http.response import json_response
        response.json_encode = Mock(return_value='{}')

        response = json_response({})

        assert 'application/json; charset=UTF-8' == response.content_type
        assert [b('{}')] == response.buffer
