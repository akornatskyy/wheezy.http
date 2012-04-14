
""" Unit tests for ``wheezy.http.config``.
"""

import unittest


class BootstrapHTTPDefaultsTestCase(unittest.TestCase):
    """ Test the ``bootstrap_http_defaults``.
    """

    def test_default_options(self):
        """ Ensure required keys exist.
        """
        from wheezy.http.config import bootstrap_http_defaults
        options = {}

        assert None == bootstrap_http_defaults(options)

        required_options = tuple(sorted(options.keys()))
        assert 10 == len(required_options)
        assert ('CONTENT_TYPE', 'ENCODING', 'ENVIRON_HOST',
                'ENVIRON_HTTPS', 'ENVIRON_HTTPS_VALUE',
                'ENVIRON_REMOTE_ADDR', 'HTTP_COOKIE_DOMAIN',
                'HTTP_COOKIE_HTTPONLY', 'HTTP_COOKIE_SECURE',
                'MAX_CONTENT_LENGTH') == required_options
