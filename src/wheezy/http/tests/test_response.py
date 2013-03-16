
""" Unit tests for ``wheezy.http.response``.
"""

import unittest

from mock import patch


class ShortcutsTestCase(unittest.TestCase):
    """ Test various response shortcuts.
    """

    def test_json_response(self):
        """ json_response
        """
        from wheezy.http import response
        from wheezy.http.comp import b
        from wheezy.http.response import json_response

        patcher = patch.object(response, 'json_encode')
        mock_json_encode = patcher.start()
        mock_json_encode.return_value = '{}'

        response = json_response({})

        patcher.stop()
        assert 'application/json; charset=UTF-8' == response.content_type
        assert [b('{}')] == response.buffer
        mock_json_encode.assert_called_once_with({})


try:
    from warnings import catch_warnings
except ImportError:
    pass
else:

    class LooksLikeTestCase(unittest.TestCase):

        def setUp(self):
            import warnings
            warnings.simplefilter("default", DeprecationWarning)
            self.ctx = catch_warnings(record=True)
            self.w = self.ctx.__enter__()

        def tearDown(self):
            self.ctx.__exit__(None, None, None)

        def assert_warning(self, msg):
            assert len(self.w) == 1
            self.assertEquals(msg, str(self.w[-1].message))

        def test_get_dependency_key(self):
            from wheezy.http.response import HTTPResponse
            assert None == HTTPResponse().dependency_key
            self.assert_warning('Use cache_dependency instead.')

        def test_set_dependency_key(self):
            from wheezy.http.response import HTTPResponse
            HTTPResponse().dependency_key = 'key'
            self.assert_warning('Use cache_dependency instead.')
