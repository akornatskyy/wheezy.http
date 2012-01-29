
""" ``headers`` module.
"""


class HTTPRequestHeaders(object):
    """ Returns a header name from ``environ``
        for the variables started with ``HTTP_``.
        
        Variables corresponding to the client-supplied 
        HTTP request headers (i.e., variables whose names 
        begin with ``HTTP_``). The presence or absence of these 
        variables corresponds with the presence or 
        absence of the appropriate HTTP header in the request.

        Attributes correspond to appropriate HTTP headers
        in the request.

        See complete list of HTTP header fields in
        `rfc4229 <http://tools.ietf.org/html/rfc4229>`_.

        >>> environ = {'HTTP_ACCEPT': 'text/plain'}
        >>> h = HTTPRequestHeaders(environ)
        >>> h.ACCEPT
        'text/plain'
        >>> h['ACCEPT']
        'text/plain'
        >>> h['X']
    """

    def __init__(self, environ):
        self.environ = environ

    def __getitem__(self, name):
        try:
            return self.environ['HTTP_' + name]
        except KeyError:
            return None

    def __getattr__(self, name):
        val = self[name]
        setattr(self, name, val)
        return val


class HTTPResponseHeaders(dict):
    """ Intentially left empty for possible extension 
        in the future.
    """
