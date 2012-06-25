
""" ``response`` module.
"""

from wheezy.core.json import json_encode


# see http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html
# see http://en.wikipedia.org/wiki/List_of_HTTP_status_codes
HTTP_STATUS = (
    None,
    # Informational
    ('100 Continue', '101 Switching Protocols'),
    # Successful
    ('200 OK', '201 Created', '202 Accepted',
     '203 Non-Authoritative Information', '204 No Content',
     '205 Reset Content', '206 Partial Content', '207 Multi-Status'),
    # Redirection
    ('300 Multiple Choices', '301 Moved Permanently', '302 Found',
     '303 See Other', '304 Not Modified', '305 Use Proxy', None,
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


def permanent_redirect(absolute_url):
    """ Shortcut function to return permanent redirect response.

        The HTTP response status code 301 Moved Permanently is used for
        permanent redirection.

        >>> r = permanent_redirect('/abc')
        >>> assert isinstance(r, HTTPResponse)
        >>> r.status
        '301 Moved Permanently'
        >>> r.skip_body
        True
    """
    response = HTTPResponse()
    response.redirect(absolute_url, 301)
    return response


def redirect(absolute_url):
    """ Shortcut function to return redirect response.

        The HTTP response status code 302 Found is a common way of
        performing a redirection.

        >>> r = redirect('/abc')
        >>> assert isinstance(r, HTTPResponse)
        >>> r.status
        '302 Found'
        >>> r.skip_body
        True
        >>> assert found == redirect
    """
    response = HTTPResponse()
    response.redirect(absolute_url, 302)
    return response

found = redirect


def see_other(absolute_url):
    """ Shortcut function to return see other redirect response.

        The HTTP response status code 303 See Other is the correct manner
        in which to redirect web applications to a new URI, particularly
        after an HTTP POST has been performed.

        This response indicates that the correct response can be found
        under a different URI and should be retrieved using a GET method.
        The specified URI is not a substitute reference for the original
        resource.

        >>> r = see_other('/abc')
        >>> assert isinstance(r, HTTPResponse)
        >>> r.status
        '303 See Other'
        >>> r.skip_body
        True
    """
    response = HTTPResponse()
    response.redirect(absolute_url, 303)
    return response


def temporary_redirect(absolute_url):
    """ Shortcut function to return temporary redirect response.

        In this occasion, the request should be repeated with another
        URI, but future requests can still use the original URI.
        In contrast to 303, the request method should not be changed
        when reissuing the original request. For instance, a POST
        request must be repeated using another POST request.

        >>> r = temporary_redirect('/abc')
        >>> assert isinstance(r, HTTPResponse)
        >>> r.status
        '307 Temporary Redirect'
        >>> r.skip_body
        True
    """
    response = HTTPResponse()
    response.redirect(absolute_url, 307)
    return response


def ajax_redirect(absolute_url):
    """ Shortcut function to return ajax redirect response.

        Browsers incorrectly handle redirect response to ajax
        request, so we return status code 207 that javascript
        is capable to receive and process browser redirect.

        Here is an example for jQuery::

            $.ajax({
                // ...
                success: function(data, textStatus, jqXHR) {
                    if (jqXHR.status == 207) {
                        window.location.replace(
                            jqXHR.getResponseHeader('Location'));
                    } else {
                        // ...
                    }
                }
            });
    """
    response = HTTPResponse()
    response.redirect(absolute_url, 207)
    return response


bad_request = error400 = lambda: http_error(400)
unauthorized = error401 = lambda: http_error(401)
forbidden = error403 = lambda: http_error(403)
not_found = error404 = lambda: http_error(404)
method_not_allowed = error405 = lambda: http_error(405)
internal_error = error500 = lambda: http_error(500)


def http_error(status_code):
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
    response = HTTPResponse()
    response.status_code = status_code
    response.skip_body = True
    return response


def json_response(obj, encoding='UTF-8'):
    """ Returns json response.
    """
    response = HTTPResponse(
        'application/json; charset=' + encoding,
        encoding)
    response.write_bytes(json_encode(obj).encode(encoding))
    return response


class HTTPResponse(object):
    """ HTTP response.

        Response headers Content-Length and Cache-Control
        must not be set by user code directly. Use
        ``HTTPCachePolicy`` instead (``HTTPResponse.cache``).

        Cookies. Append cookie ``pref`` to response.

        >>> from wheezy.http.cookie import HTTPCookie
        >>> from wheezy.http.config import bootstrap_http_defaults
        >>> options = {}
        >>> bootstrap_http_defaults(options)
        >>> r = HTTPResponse()
        >>> c = HTTPCookie('pref', value='1', options=options)
        >>> r.cookies.append(c)

        Delete ``pref`` cookie.

        >>> r = HTTPResponse()
        >>> r.cookies.append(HTTPCookie.delete('pref', options=options))
    """
    status_code = 200
    cache_policy = None
    cache_profile = None
    skip_body = False
    dependency = None

    def __init__(self, content_type='text/html; charset=UTF-8',
                 encoding='UTF-8'):
        """ Initializes HTTP response.

            Content type:

            >>> r = HTTPResponse()
            >>> r.headers
            [('Content-Type', 'text/html; charset=UTF-8')]
            >>> r = HTTPResponse(content_type='image/gif')
            >>> r.headers
            [('Content-Type', 'image/gif')]
        """
        self.content_type = content_type
        self.encoding = encoding
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

    def redirect(self, absolute_url, status_code=302):
        """ Redirect response to ``absolute_url`` and sets ``status_code``.

            >>> r = HTTPResponse()
            >>> r.redirect('/')
            >>> r.status
            '302 Found'
            >>> r.headers # doctest: +NORMALIZE_WHITESPACE
            [('Content-Type', 'text/html; charset=UTF-8'),
                    ('Location', '/')]

            Make permanent redirect.

            >>> r = HTTPResponse()
            >>> r.redirect('/abc', status_code=301)
            >>> r.status
            '301 Moved Permanently'
            >>> r.headers # doctest: +NORMALIZE_WHITESPACE
            [('Content-Type', 'text/html; charset=UTF-8'),
                    ('Location', '/abc')]
        """
        self.status_code = status_code
        self.headers.append(('Location', absolute_url))
        self.skip_body = True

    def write(self, chunk):
        """ Applies encoding to ``chunk`` and append it to response
            buffer.

            >>> from wheezy.http.comp import b
            >>> from wheezy.core.comp import u
            >>> r = HTTPResponse()
            >>> r.write(u('abc'))
            >>> r.write(u('de'))
            >>> assert r.buffer[0] == b('abc')
            >>> assert r.buffer[1] == b('de')

            or anything that has ``encode(encoding)`` method,
            otherwise raise ``AttributeError``.

            >>> r.write(123) # doctest: +ELLIPSIS
            Traceback (most recent call last):
                ...
            AttributeError: ...
        """
        self.buffer.append(chunk.encode(self.encoding))

    def write_bytes(self, chunk):
        """ Appends chunk it to response buffer. No special checks performed.
            It must be valid object for WSGI response.

            >>> from wheezy.http.comp import b
            >>> r = HTTPResponse()
            >>> b1 = b('abc')
            >>> b2 = b('de')
            >>> r.write_bytes(b1)
            >>> r.write_bytes(b2)
            >>> assert r.buffer[0] == b1
            >>> assert r.buffer[1] == b2
        """
        self.buffer.append(chunk)

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
            >>> from wheezy.http.cachepolicy import HTTPCachePolicy
            >>> r.cache = HTTPCachePolicy()
            >>> from wheezy.http.config import bootstrap_http_defaults
            >>> options = {}
            >>> bootstrap_http_defaults(options)
            >>> r.cookies.append(HTTPCookie('pref', '1', options=options))
            >>> result = r.__call__(start_response)
            >>> status
            '200 OK'
            >>> headers # doctest: +NORMALIZE_WHITESPACE
            [('Content-Type', 'text/html; charset=UTF-8'),
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
        cache_policy = self.cache_policy
        if cache_policy:
            cache_policy.extend(headers)
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
        content_length = sum([len(chunk) for chunk in buffer])
        append(('Content-Length', str(content_length)))
        start_response(self.status, headers)
        return buffer
