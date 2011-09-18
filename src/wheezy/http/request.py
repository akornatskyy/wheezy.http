
""" ``request`` module.
"""

from wheezy.http import config
from wheezy.http.headers import RequestHeaders
from wheezy.http.p2to3 import ustr
from wheezy.http.parser import parse_qs
from wheezy.http.parser import parse_multipart
from wheezy.http.parser import parse_cookie
from wheezy.http.utils import attribute


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
        >>> str(r.SERVER_NAME)
        'localhost'
        >>> str(r.PATH)
        '/abc/de'
        >>> str(r.QUERY['a'])
        '2'

        Return the originating host of the request
        using ``config.ENVIRON_HOST``.

        >>> r = HttpRequest(environ)
        >>> environ[config.ENVIRON_HOST] = 'example.com'
        >>> str(r.HOST)
        'example.com'

        If the host is behind multiple proxies, return
        the last one.

        >>> r = HttpRequest(environ)
        >>> environ[config.ENVIRON_HOST] = 'a, b, c'
        >>> str(r.HOST)
        'c'

        Return the originating ip address of the request
        using ``config.ENVIRON_REMOTE_ADDR``.

        >>> environ[config.ENVIRON_REMOTE_ADDR] = '7.1.3.2'
        >>> r.REMOTE_ADDR
        '7.1.3.2'

        If the remote client is behind multiple proxies,
        return the fist one.

        >>> r = HttpRequest(environ)
        >>> environ[config.ENVIRON_REMOTE_ADDR] = 'a, b, c'
        >>> r.REMOTE_ADDR
        'a'

        Http headers:

        >>> assert isinstance(r.HEADERS, RequestHeaders)

        Cookies:

        >>> environ['HTTP_COOKIE'] = 'ID=1234;PREF=abc'
        >>> cookies = r.COOKIES
        >>> cookies['ID']
        '1234'

        Check if http request is secure (HTTPS)

        >>> r.SECURE
        False
        >>> str(r.SCHEME)
        'http'
        >>> r = HttpRequest(environ)
        >>> environ[config.ENVIRON_HTTPS] = \\
        ...         config.ENVIRON_HTTPS_VALUE
        >>> r.SECURE
        True
        >>> str(r.SCHEME)
        'https'

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
        val = ustr(self.environ.get(name, ''), self.encoding)
        setattr(self, name, val)
        return val

    @attribute
    def HOST(self):
        host = self.environ[config.ENVIRON_HOST]
        if ',' in host:
            host = host.split(',')[-1].strip()
        return ustr(host, self.encoding)

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
        return RequestHeaders(self.environ)

    @attribute
    def QUERY(self):
        return parse_qs(self.QUERY_STRING)

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
            return ustr('https', self.encoding)
        else:
            return ustr('http', self.encoding)

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
            >>> str(r.FORM['greeting'])
            'Hallo Welt'
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
            qs = ustr(fp.read(icl), self.encoding)
            return parse_qs(qs), None
