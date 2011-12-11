
""" ``response`` module.
"""

from wheezy.core.config import Config

from wheezy.http import config
from wheezy.http.cachepolicy import HttpCachePolicy
from wheezy.http.comp import bytes_type
from wheezy.http.comp import str_type


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


HTTP_HEADER_CACHE_CONTROL_DEFAULT = ('Cache-Control', 'private')
HTTP_HEADER_CONTENT_LENGTH_ZERO = ('Content-Length', '0')


def redirect(absolute_url, permanent=False, options=None):
    """ Shortcut function to return redirect
        response.

        >>> r = redirect('/abc')
        >>> assert isinstance(r, HttpResponse)
        >>> r.status
        '302 Found'
        >>> r.skip_body
        True
    """
    response = HttpResponse(options=options)
    response.redirect(
        absolute_url=absolute_url,
        permanent=permanent
    )
    return response


bad_request = error400 = lambda o=None: client_error(400, o)
unauthorized = error401 = lambda o=None: client_error(401, o)
forbidden = error403 = lambda o=None: client_error(403, o)
not_found = error404 = lambda o=None: client_error(404, o)
method_not_allowed = error405 = lambda o=None: client_error(405, o)


def client_error(status_code, options=None):
    """ Shortcut function to return a response with
        given status code.

        >>> r = client_error(404)
        >>> assert isinstance(r, HttpResponse)
        >>> r.status
        '404 Not Found'
        >>> r.skip_body
        True
    """
    assert status_code >= 400 and status_code <= 417
    response = HttpResponse(options=options)
    response.status_code = status_code
    response.skip_body = True
    return response


class HttpResponse(object):
    """ HTTP response.

        Response headers Content-Length and Cache-Control
        must not be set by user code directly. Use
        ``HttpCachePolicy`` instead (``HttpResponse.cache``).

        Cookies. Append cookie ``pref`` to response.

        >>> from wheezy.http.cookie import HttpCookie
        >>> r = HttpResponse()
        >>> c = HttpCookie('pref', value='1', options=r.config)
        >>> r.cookies.append(c)

        Delete ``pref`` cookie.

        >>> r = HttpResponse()
        >>> r.cookies.append(HttpCookie.delete('pref'))
    """
    status_code = 200
    cache = None
    skip_body = False
    dependency = None

    def __init__(self, content_type=None, encoding=None, options=None):
        """ Initializes HTTP response.

            Content type:

            >>> r = HttpResponse()
            >>> r.headers
            [('Content-Type', 'text/html; charset=utf-8')]
            >>> r = HttpResponse(content_type='image/gif')
            >>> r.headers
            [('Content-Type', 'image/gif')]

            Encoding:

            >>> r = HttpResponse(encoding='iso-8859-4')
            >>> r.headers
            [('Content-Type', 'text/html; charset=iso-8859-4')]
        """
        self.config = Config(options, master=config)
        self.encoding = encoding or self.config.ENCODING
        self.headers = [('Content-Type', content_type or (
            self.config.CONTENT_TYPE + '; charset=' + self.encoding))]
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
            >>> r.headers # doctest: +NORMALIZE_WHITESPACE
            [('Content-Type', 'text/html; charset=utf-8'),
                    ('Location', '/')]

            If ``permanent`` argument is ``True``,
            make permanent redirect.

            >>> r = HttpResponse()
            >>> r.redirect('/abc', permanent=True)
            >>> r.status
            '301 Moved Permanently'
            >>> r.headers # doctest: +NORMALIZE_WHITESPACE
            [('Content-Type', 'text/html; charset=utf-8'),
                    ('Location', '/abc')]
        """
        if permanent:
            self.status_code = 301
        else:
            self.status_code = 302
        self.headers.append(('Location', absolute_url))
        self.skip_body = True

    def write(self, chunk):
        """ Append a chunk to response buffer

            ``chunk`` can be bytes

            >>> from wheezy.http.comp import b
            >>> r = HttpResponse()
            >>> b1 = b('abc')
            >>> b2 = b('de')
            >>> r.write(b1)
            >>> r.write(b2)
            >>> assert r.buffer[0] == b1
            >>> assert r.buffer[1] == b2

            or string

            >>> from wheezy.http.comp import u
            >>> r = HttpResponse()
            >>> r.write(u('abc'))
            >>> r.write(u('de'))
            >>> assert r.buffer[0] == b1
            >>> assert r.buffer[1] == b2

            otherwise raise TypeError

            >>> r.write(123) # doctest: +ELLIPSIS
            Traceback (most recent call last):
                ...
            TypeError: ...
        """
        if isinstance(chunk, bytes_type):
            self.buffer.append(chunk)
        elif isinstance(chunk, str_type):
            self.buffer.append(chunk.encode(self.encoding))
        else:
            raise TypeError('chunk must be string or bytes')

    def __call__(self, start_response):
        """
            >>> from wheezy.http.cookie import HttpCookie
            >>> status = None
            >>> headers = None
            >>> def start_response(s, h):
            ...     global status
            ...     global headers
            ...     headers = h
            ...     status = s
            >>> r = HttpResponse()
            >>> r.cache = HttpCachePolicy()
            >>> r.cookies.append(HttpCookie('pref', '1'))
            >>> result = r.__call__(start_response)
            >>> status
            '200 OK'
            >>> headers # doctest: +NORMALIZE_WHITESPACE
            [('Content-Type', 'text/html; charset=utf-8'),
            ('Cache-Control', 'private'),
            ('Set-Cookie', 'pref=1; path=/'),
            ('Content-Length', '0')]
            >>> assert r.buffer == result

            Skip body:

            >>> r = HttpResponse()
            >>> r.skip_body = True
            >>> r.__call__(start_response)
            []
        """
        headers = self.headers
        append = headers.append
        if self.cache:
            self.cache.extend(headers)
        else:
            append(HTTP_HEADER_CACHE_CONTROL_DEFAULT)
        if self.cookies:
            for cookie in self.cookies:
                append(('Set-Cookie', cookie.HTTP_SET_COOKIE))
        if self.skip_body:
            append(HTTP_HEADER_CONTENT_LENGTH_ZERO)
            start_response(self.status, headers)
            return []
        buffer = self.buffer
        content_length = sum((len(chunk) for chunk in buffer))
        append(('Content-Length', str(content_length)))
        start_response(self.status, headers)
        return buffer
