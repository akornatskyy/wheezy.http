
""" ``request`` module.
"""

from wheezy.http import config
from wheezy.http.headers import HttpRequestHeaders
from wheezy.http.p2to3 import ntou
from wheezy.http.p2to3 import parse_qs
from wheezy.http.parser import parse_multipart
from wheezy.http.parser import parse_cookie
from wheezy.http.utils import attribute
from wheezy.http.utils import HttpDict


class HttpRequest(object):
    """ Represent HTTP request. ``environ`` variables
        are accessable via attributes.

        >>> environ = {
        ...         'SCRIPT_NAME': '/abc',
        ...         'PATH_INFO': '/de',
        ...         'QUERY_STRING': 'a=1&a=2&b=3'
        ... }
        >>> from wheezy.http import sample
        >>> sample.request(environ)
        >>> sample.request_headers(environ)
        >>> r = HttpRequest(environ)
        >>> r.METHOD
        'GET'
        >>> assert r.SERVER_NAME == ntou('localhost', r.encoding)
        >>> assert r.PATH == ntou('/abc/de', r.encoding)
        >>> assert r.QUERY['a'] == ntou('2', r.encoding)

        Return the originating host of the request
        using ``config.ENVIRON_HOST``.

        >>> r = HttpRequest(environ)
        >>> environ[config.ENVIRON_HOST] = 'example.com'
        >>> assert r.HOST == ntou('example.com', r.encoding)

        If the host is behind multiple proxies, return
        the last one.

        >>> r = HttpRequest(environ)
        >>> environ[config.ENVIRON_HOST] = 'a, b, c'
        >>> assert r.HOST == ntou('c', r.encoding)

        Return the originating ip address of the request
        using ``config.ENVIRON_REMOTE_ADDR``.

        >>> environ[config.ENVIRON_REMOTE_ADDR] = '7.1.3.2'
        >>> assert r.REMOTE_ADDR == ntou('7.1.3.2', r.encoding)

        If the remote client is behind multiple proxies,
        return the fist one.

        >>> r = HttpRequest(environ)
        >>> environ[config.ENVIRON_REMOTE_ADDR] = 'a, b, c'
        >>> assert r.REMOTE_ADDR == ntou('a', r.encoding)

        Http headers:

        >>> assert isinstance(r.HEADERS, HttpRequestHeaders)

        Cookies:

        >>> environ['HTTP_COOKIE'] = 'ID=1234;PREF=abc'
        >>> cookies = r.COOKIES
        >>> assert cookies['ID'] == ntou('1234', r.encoding)

        Check if http request is secure (HTTPS)

        >>> r.SECURE
        False
        >>> assert r.SCHEME == ntou('http', r.encoding)
        >>> r = HttpRequest(environ)
        >>> environ[config.ENVIRON_HTTPS] = \\
        ...         config.ENVIRON_HTTPS_VALUE
        >>> r.SECURE
        True
        >>> assert r.SCHEME == ntou('https', r.encoding)

        Check if http request is ajax request

        >>> r.AJAX
        False
        >>> r = HttpRequest(environ)
        >>> environ['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        >>> r.AJAX
        True
    """

    def __init__(self, environ, encoding=None):
        self.environ = environ
        self.METHOD = environ['REQUEST_METHOD']
        self.encoding = encoding or config.ENCODING

    def __getattr__(self, name):
        val = ntou(self.environ.get(name, ''), self.encoding)
        setattr(self, name, val)
        return val

    @attribute
    def HOST(self):
        host = self.environ[config.ENVIRON_HOST]
        if ',' in host:
            host = host.split(',')[-1].strip()
        return ntou(host, self.encoding)

    @attribute
    def REMOTE_ADDR(self):
        addr = self.environ[config.ENVIRON_REMOTE_ADDR]
        if ',' in addr:
            addr = addr.split(',')[0].strip()
        return addr

    @attribute
    def PATH(self):
        return self.SCRIPT_NAME + self.PATH_INFO

    @attribute
    def HEADERS(self):
        return HttpRequestHeaders(self.environ)

    @attribute
    def QUERY(self):
        return HttpDict(parse_qs(
            self.QUERY_STRING,
            encoding = self.encoding
        ))

    @attribute
    def FORM(self):
        form, self.FILES = self.load_body()
        return form

    @attribute
    def FILES(self):
        self.FORM, files = self.load_body()
        return files

    @attribute
    def COOKIES(self):
        return parse_cookie(self.HEADERS.COOKIE)

    @attribute
    def AJAX(self):
        return self.HEADERS.X_REQUESTED_WITH == 'XMLHttpRequest'

    @attribute
    def SECURE(self):
        return self.environ.get(config.ENVIRON_HTTPS) == \
                config.ENVIRON_HTTPS_VALUE

    @attribute
    def SCHEME(self):
        if (self.SECURE):
            return 'https'
        else:
            return 'http'

    def load_body(self):
        """ Load http request body and returns
            form data and files.

            >>> from wheezy.http import sample
            >>> environ = {}
            >>> sample.request(environ)

            Load FROM as application/x-www-form-urlencoded

            >>> sample.request_urlencoded(environ)
            >>> r = HttpRequest(environ)
            >>> assert len(r.FORM) == 2
            >>> assert r.FORM['greeting'] == ntou('Hallo Welt',
            ...     r.encoding)
            >>> assert r.FILES is None

            Load FORM as multipart/form-data.

            >>> sample.request_multipart(environ)
            >>> r = HttpRequest(environ)
            >>> assert len(r.FORM) == 1
            >>> assert len(r.FILES) == 1

            Load FILES first this time

            >>> sample.request_multipart(environ)
            >>> r = HttpRequest(environ)
            >>> assert len(r.FILES) == 1
            >>> assert len(r.FORM) == 1

            Content-Length exceed maximum allowed

            >>> cl = config.MAX_CONTENT_LENGTH + 1
            >>> environ['CONTENT_LENGTH'] = str(cl)
            >>> r = HttpRequest(environ)
            >>> r.load_body() # doctest: +ELLIPSIS
            Traceback (most recent call last):
                ...
            ValueError: ...
        """
        cl = self.CONTENT_LENGTH
        icl = int(cl)
        if (icl > config.MAX_CONTENT_LENGTH):
            raise ValueError('Maximum content length exceeded')
        fp = self.environ['wsgi.input']
        ct = self.CONTENT_TYPE
        if ct.startswith('m'):
            return parse_multipart(fp, ct, cl, self.encoding)
        else:
            qs = fp.read(icl).decode(self.encoding)
            return HttpDict(parse_qs(qs, self.encoding)), None
