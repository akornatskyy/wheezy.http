
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
        assert 5 == len(required_options)
        assert ('ENCODING', 'HTTP_COOKIE_DOMAIN',
                'HTTP_COOKIE_HTTPONLY', 'HTTP_COOKIE_SECURE',
                'MAX_CONTENT_LENGTH') == required_options
