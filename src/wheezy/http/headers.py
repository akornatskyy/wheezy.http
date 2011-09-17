
""" ``headers`` module.
"""


class RequestHeaders(object):
    """
        http://tools.ietf.org/html/rfc4229

        >>> from wheezy.http import sample
        >>> environ = {}
        >>> sample.request_headers(environ)
        >>> h = RequestHeaders(environ)
        >>> h.ACCEPT
        'text/plain'
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
