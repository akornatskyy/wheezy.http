
""" ``headers`` module.
"""

from wheezy.http.p2to3 import bstr


class HttpRequestHeaders(object):
    """ Returns a header name from ``environ``
        for the keys started with HTTP_.

        Attributes corresponds to those names.

        http://tools.ietf.org/html/rfc4229

        >>> environ = {'HTTP_ACCEPT': 'text/plain'}
        >>> h = HttpRequestHeaders(environ)
        >>> h.ACCEPT
        'text/plain'

        >>> from wheezy.http import sample
        >>> environ = {}
        >>> sample.request_headers(environ)
        >>> h = HttpRequestHeaders(environ)
        >>> h.HOST
        'localhost:8080'
    """

    def __init__(self, environ):
        self.environ = environ

    def __getattr__(self, name):
        """
        """
        val = self.environ.get('HTTP_' + name, None)
        setattr(self, name, val)
        return val


class HttpResponseHeaders(dict):
    """ Any headers added are encoded to bytes.
        http://www.python.org/dev/peps/pep-3333/#unicode-issues
        http://www.faqs.org/rfcs/rfc2616.html
    """

    def __getitem__(self, header):
        return super(HttpResponseHeaders, self).__getitem__(
            bstr(header, 'iso-8859-1')
        )

    def __setitem__(self, header, value):
        """
            >>> from wheezy.http.p2to3 import ustr
            >>> h = HttpResponseHeaders()
            >>> h['Cache-Control'] = ustr('public', 'utf-8')
            >>> v = h['Cache-Control']
            >>> assert bstr('public', 'utf-8') == v
        """
        super(HttpResponseHeaders, self).__setitem__(
            bstr(header, 'iso-8859-1'),
            bstr(value, 'iso-8859-1')
        )
