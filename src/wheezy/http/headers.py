
""" ``headers`` module.
"""

from wheezy.http.comp import ntob


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

    def __init__(self, encoding='iso-8859-1'):
        self.encoding = encoding

    def __getitem__(self, header):
        return super(HttpResponseHeaders, self).__getitem__(
            ntob(header, self.encoding)
        )

    def __setitem__(self, header, value):
        """
            >>> h = HttpResponseHeaders()
            >>> h['Cache-Control'] = 'public'
            >>> v = h['Cache-Control']
            >>> assert ntob('public', h.encoding) == v
        """
        super(HttpResponseHeaders, self).__setitem__(
            ntob(header, self.encoding),
            ntob(value, self.encoding)
        )
