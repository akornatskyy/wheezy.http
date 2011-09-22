
""" ``response`` module.
"""


from wheezy.http import config
from wheezy.http.cachepolicy import HttpCachePolicy
from wheezy.http.headers import HttpResponseHeaders
from wheezy.http.p2to3 import bstr

# see http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html
HTTP_STATUS = (None,
    # Informational
    ('100 Continue', '101 Switching Protocols'),
    # Successful
    ('200 OK', '201 Created', '202 Accepted',
        '203 Non-Authoritative Information', '204 No Content',
        '205 Reset Content', '206 Partial Content'),
    # Redirection
    ('300 Multiple Choices', '301 Moved Permanently', '302 Found',
        '303 See Other',  '304 Not Modified', '305 Use Proxy', None,
        '307 Temporary Redirect'),
    # Client Error
    ('400 Bad Request', '401 Unauthorized', '402 Payment Required',
        '403 Forbidden', '404 Not Found', '405 Method Not Allowed',
        '406 Not Acceptable', '407 Proxy Authentication Required',
        '408 Request Timeout', '409 Conflict', '410 Gone',
        '411 Length Required', '412 Precondition Failed',
        '413 Request Entity Too Large', '414 Request-Uri Too Long',
        '415 Unsupported Media Type',
        '416 Requested Range Not Satisfiable', '417 Expectation Failed'),
    # Server Error
    ('500 Internal Server Error', '501 Not Implemented',
        '502 Bad Gateway', '503 Service Unavailable',
        '504 Gateway Timeout', '505 Http Version Not Supported')
)


class HttpResponse(object):
    """
    """

    def __init__(self, encoding=None):
        self.status_code = 200
        self.encoding = encoding or config.ENCODING
        self.headers = HttpResponseHeaders()
        self.buffer = []

    def get_status(self):
        """ Returns a string that describes the specified
            HTTP status code.

            >>> r = HttpResponse()
            >>> r.status
            '200 OK'
            >>> r.status_code = 301
            >>> r.status
            '301 Moved Permanently'
        """
        code = self.status_code
        return HTTP_STATUS[int(code / 100)][code % 100]

    status = property(get_status)

    def write(self, chunk):
        """ Append a chunk to response buffer

            >>> r = HttpResponse()
            >>> r.write('abc')
            >>> r.write('de')
            >>> list(map(lambda c: str(c.decode(r.encoding)), r.buffer))
            ['abc', 'de']
        """
        self.buffer.append(bstr(chunk, self.encoding))
