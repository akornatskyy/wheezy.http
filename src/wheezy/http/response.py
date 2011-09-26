
""" ``response`` module.
"""


from wheezy.http import config
from wheezy.http.cachepolicy import HttpCachePolicy
from wheezy.http.comp import copyitems
from wheezy.http.comp import ntob
from wheezy.http.headers import HttpResponseHeaders
from wheezy.http.utils import HttpDict

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


def redirect(absolute_url, permanent=False):
    """ Shortcut function to return redirect
        response.

        >>> r = redirect('/abc')
        >>> assert isinstance(r, HttpResponse)
        >>> r.status
        '302 Found'
    """
    response = HttpResponse()
    response.redirect(
        absolute_url=absolute_url,
        permanent=permanent
    )
    return response


class HttpResponse(object):
    """ HTTP response.

        Response headers Content-Length and Cache-Control
        must not be set by user code directly. Use
        ``HttpCachePolicy`` instead (``HttpResponse.cache``).
    """
    status_code = 200
    cache = None
    skip_body = False

    def __init__(self, content_type=None, encoding=None):
        """ Initializes HTTP response.

            Content type:

            >>> r = HttpResponse()
            >>> r.headers['Content-Type']
            'text/html; charset=utf-8'
            >>> r = HttpResponse(content_type='image/gif')
            >>> r.headers['Content-Type']
            'image/gif'

            Encoding:

            >>> r = HttpResponse(encoding='iso-8859-4')
            >>> r.headers['Content-Type']
            'text/html; charset=iso-8859-4'
        """
        self.encoding = encoding or config.ENCODING
        self.headers = HttpDict()
        self.headers['Content-Type'] = content_type or (
            config.CONTENT_TYPE + '; charset=' + self.encoding)
        self.buffer = []
        self.cookies = []

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

    def redirect(self, absolute_url, permanent=False):
        """ Redirect response to ``absolute_url``.

            >>> r = HttpResponse()
            >>> r.redirect('/')
            >>> r.status
            '302 Found'
            >>> r.headers['Location']
            '/'

            If ``permanent`` argument is ``True``,
            make permanent redirect.

            >>> r.redirect('/abc', permanent=True)
            >>> r.status
            '301 Moved Permanently'
            >>> r.headers['Location']
            '/abc'
        """
        if permanent:
            self.status_code = 301
        else:
            self.status_code = 302
        self.headers['Location'] = absolute_url

    def write(self, chunk):
        """ Append a chunk to response buffer

            >>> r = HttpResponse()
            >>> r.write('abc')
            >>> r.write('de')
            >>> assert r.buffer[0] == ntob('abc', r.encoding)
            >>> assert r.buffer[1] == ntob('de', r.encoding)
        """
        self.buffer.append(ntob(chunk, self.encoding))

    def __call__(self, start_response):
        """
        """
        headers = copyitems(self.headers)
        if self.cache:
            # TODO: headers are list
            self.cache.update(headers)
        else:
            headers.append(('Cache-Control', 'private'))
        if self.skip_body:
            buffer = []
            content_length = 0
        else:
            buffer = self.buffer
            content_length = sum((len(chunk) for chunk in buffer))
        headers.append(('Content-Length', str(content_length)))
        start_response(self.status, headers)
        return buffer
