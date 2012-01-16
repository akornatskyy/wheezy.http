
""" ``response`` module.
"""

from wheezy.core.config import Config

from wheezy.http import config
from wheezy.http.cachepolicy import HTTPCachePolicy
from wheezy.http.comp import bytes_type


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
        >>> assert isinstance(r, HTTPResponse)
        >>> r.status
        '302 Found'
        >>> r.skip_body
        True
    """
    response = HTTPResponse(options=options)
    response.redirect(
        absolute_url=absolute_url,
        permanent=permanent
    )
    return response


bad_request = error400 = lambda o=None: http_error(400, o)
unauthorized = error401 = lambda o=None: http_error(401, o)
forbidden = error403 = lambda o=None: http_error(403, o)
not_found = error404 = lambda o=None: http_error(404, o)
method_not_allowed = error405 = lambda o=None: http_error(405, o)
internal_error = error500 = lambda o=None: http_error(500, o)


def http_error(status_code, options=None):
    """ Shortcut function to return a response with
        given status code.

        >>> r = http_error(404)
        >>> assert isinstance(r, HTTPResponse)
        >>> r.status
        '404 Not Found'
        >>> r.skip_body
        True
    """
    assert status_code >= 400 and status_code <= 505
    response = HTTPResponse(options=options)
    response.status_code = status_code
    response.skip_body = True
    return response


class HTTPResponse(object):
    """ HTTP response.

        Response headers Content-Length and Cache-Control
        must not be set by user code directly. Use
        ``HTTPCachePolicy`` instead (``HTTPResponse.cache``).

        Cookies. Append cookie ``pref`` to response.

        >>> from wheezy.http.cookie import HTTPCookie
        >>> r = HTTPResponse()
        >>> c = HTTPCookie('pref', value='1', options=r.config)
        >>> r.cookies.append(c)

        Delete ``pref`` cookie.

        >>> r = HTTPResponse()
        >>> r.cookies.append(HTTPCookie.delete('pref'))
    """
    status_code = 200
    cache = None
    skip_body = False
    dependency = None

    def __init__(self, content_type=None, encoding=None, options=None):
        """ Initializes HTTP response.

            Content type:

            >>> r = HTTPResponse()
            >>> r.headers
            [('Content-Type', 'text/html; charset=utf-8')]
            >>> r = HTTPResponse(content_type='image/gif')
            >>> r.headers
            [('Content-Type', 'image/gif')]

            Encoding:

            >>> r = HTTPResponse(encoding='iso-8859-4')
            >>> r.headers
            [('Content-Type', 'text/html; charset=iso-8859-4')]
        """
        self.config = Config(options, master=config)
        self.encoding = encoding or self.config.ENCODING
        if content_type is None:
            content_type = (self.config.CONTENT_TYPE +
                    '; charset=' + self.encoding)
        self.content_type = content_type
        self.headers = [('Content-Type', content_type)]
        self.buffer = []
        self.cookies = []

    def get_status(self):
        """ Returns a string that describes the specified
            HTTP status code.

            >>> r = HTTPResponse()
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

            >>> r = HTTPResponse()
            >>> r.redirect('/')
            >>> r.status
            '302 Found'
            >>> r.headers # doctest: +NORMALIZE_WHITESPACE
            [('Content-Type', 'text/html; charset=utf-8'),
                    ('Location', '/')]

            If ``permanent`` argument is ``True``,
            make permanent redirect.

            >>> r = HTTPResponse()
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
            >>> r = HTTPResponse()
            >>> b1 = b('abc')
            >>> b2 = b('de')
            >>> r.write(b1)
            >>> r.write(b2)
            >>> assert r.buffer[0] == b1
            >>> assert r.buffer[1] == b2

            or string

            >>> from wheezy.core.comp import u
            >>> r = HTTPResponse()
            >>> r.write(u('abc'))
            >>> r.write(u('de'))
            >>> assert r.buffer[0] == b1
            >>> assert r.buffer[1] == b2

            or anything that has encode(encoding) method,
            otherwise raise AttributeError

            >>> r.write(123) # doctest: +ELLIPSIS
            Traceback (most recent call last):
                ...
            AttributeError: ...
        """
        if isinstance(chunk, bytes_type):
            self.buffer.append(chunk)
        else:
            self.buffer.append(chunk.encode(self.encoding))

    def __call__(self, start_response):
        """
            >>> from wheezy.http.cookie import HTTPCookie
            >>> status = None
            >>> headers = None
            >>> def start_response(s, h):
            ...     global status
            ...     global headers
            ...     headers = h
            ...     status = s
            >>> r = HTTPResponse()
            >>> r.cache = HTTPCachePolicy()
            >>> r.cookies.append(HTTPCookie('pref', '1'))
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

            >>> r = HTTPResponse()
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
            encoding = self.encoding
            for cookie in self.cookies:
                append(cookie.http_set_cookie(encoding))
        if self.skip_body:
            append(HTTP_HEADER_CONTENT_LENGTH_ZERO)
            start_response(self.status, headers)
            return []
        buffer = self.buffer
        content_length = sum((len(chunk) for chunk in buffer))
        append(('Content-Length', str(content_length)))
        start_response(self.status, headers)
        return buffer
