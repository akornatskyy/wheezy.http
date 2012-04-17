
""" Unit tests for ``wheezy.http.request``.
"""

import unittest


class HTTPRequestHeadersTestCase(unittest.TestCase):
    """ Test the ``HTTPRequestHeaders`` class.
    """

    def test_get_item(self):
        """ Returns an item from environ by key prefixed with 'HTTP_'
        """
        from wheezy.http.request import HTTPRequestHeaders

        headers = HTTPRequestHeaders(environ={
            'HTTP_ACCEPT': 'text/plain'
        })

        assert 'text/plain' == headers['ACCEPT']

    def test_get_item_not_found(self):
        """ If header not found returns None.
        """
        from wheezy.http.request import HTTPRequestHeaders

        headers = HTTPRequestHeaders(environ={
        })

        assert None == headers['ACCEPT']

    def test_get_attr(self):
        """ Returns an item from environ by name prefixed with 'HTTP_'
        """
        from wheezy.http.request import HTTPRequestHeaders

        headers = HTTPRequestHeaders(environ={
            'HTTP_ACCEPT': 'text/plain'
        })

        assert 'text/plain' == headers.ACCEPT

    def test_get_attr_not_found(self):
        """ If header not found returns None.
        """
        from wheezy.http.request import HTTPRequestHeaders

        headers = HTTPRequestHeaders(environ={
        })

        assert None == headers.ACCEPT
