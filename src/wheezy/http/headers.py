
""" ``headers`` module.
"""

from wheezy.http.comp import ntob


class HTTPRequestHeaders(object):
    """ Returns a header name from ``environ``
        for the keys started with HTTP_.

        Attributes corresponds to those names.

        http://tools.ietf.org/html/rfc4229

        >>> environ = {'HTTP_ACCEPT': 'text/plain'}
        >>> h = HTTPRequestHeaders(environ)
        >>> h.ACCEPT
        'text/plain'
        >>> h['ACCEPT']
        'text/plain'
        >>> h['X']

        >>> from wheezy.http import sample
        >>> environ = {}
        >>> sample.request_headers(environ)
        >>> h = HTTPRequestHeaders(environ)
        >>> h.HOST
        'localhost:8080'
    """

    def __init__(self, environ):
        self.environ = environ

    def __getitem__(self, name):
        try:
            return self.environ['HTTP_' + name]
        except KeyError:
            return None

    def __getattr__(self, name):
        """
        """
        val = self[name]
        setattr(self, name, val)
        return val


class HTTPResponseHeaders(dict):
    """
    """
