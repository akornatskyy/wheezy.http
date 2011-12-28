
""" ``request`` module.
"""

from wheezy.core.config import Config
from wheezy.core.collections import defaultdict
from wheezy.core.descriptors import attribute
from wheezy.core.url import UrlParts

from wheezy.http import config
from wheezy.http.comp import bton
from wheezy.http.comp import parse_qs
from wheezy.http.headers import HTTPRequestHeaders
from wheezy.http.parse import parse_cookie
from wheezy.http.parse import parse_multipart


class HTTPRequest(object):
    """ Represent HTTP request. ``environ`` variables
        are accessable via attributes.

        >>> environ = {
        ...         'SCRIPT_NAME': '/abc',
        ...         'PATH_INFO': '/de',
        ...         'QUERY_STRING': 'a=1&a=2&b=3'
        ... }
        >>> from wheezy.core.collections import last_item_adapter
        >>> from wheezy.http import sample
        >>> sample.request(environ)
        >>> sample.request_headers(environ)
        >>> r = HTTPRequest(environ)
        >>> r.method
        'GET'
        >>> r.root_path
        '/abc/'
        >>> r.path
        '/abc/de'
        >>> r.query['a']
        ['1', '2']
        >>> query = last_item_adapter(r.query)
        >>> query['a']
        '2'

        Return the originating host of the request
        using ``config.ENVIRON_HOST``.

        >>> r = HTTPRequest(environ)
        >>> environ[r.config.ENVIRON_HOST] = 'example.com'
        >>> r.host
        'example.com'

        If the host is behind multiple proxies, return
        the last one.

        >>> r = HTTPRequest(environ)
        >>> environ[r.config.ENVIRON_HOST] = 'a, b, python.org'
        >>> r.host
        'python.org'

        Return the originating ip address of the request
        using ``config.ENVIRON_REMOTE_ADDR``.

        >>> environ[r.config.ENVIRON_REMOTE_ADDR] = '7.1.3.2'
        >>> r.remote_addr
        '7.1.3.2'

        If the remote client is behind multiple proxies,
        return the fist one.

        >>> r = HTTPRequest(environ)
        >>> environ[r.config.ENVIRON_REMOTE_ADDR] = 'a, b, c'
        >>> r.remote_addr
        'a'

        HTTP headers:

        >>> assert isinstance(r.headers, HTTPRequestHeaders)

        Cookies:

        >>> r.cookies
        {}
        >>> r = HTTPRequest(environ)
        >>> environ['HTTP_COOKIE'] = 'ID=1234;PREF=abc'
        >>> cookies = r.cookies
        >>> cookies['ID']
        '1234'

        Check if http request is secure (HTTPS)

        >>> r.secure
        False
        >>> r.scheme
        'http'
        >>> r = HTTPRequest(environ)
        >>> environ[r.config.ENVIRON_HTTPS] = \\
        ...         r.config.ENVIRON_HTTPS_VALUE
        >>> r.secure
        True
        >>> r.scheme
        'https'

        Check if http request is ajax request

        >>> r.ajax
        False
        >>> r = HTTPRequest(environ)
        >>> environ['HTTP_X_REQUESTED_WITH'] = 'XMLHTTPRequest'
        >>> r.ajax
        True

        >>> r = HTTPRequest(environ)
        >>> r.urlparts
        urlparts('https', 'python.org', '/abc/de', 'a=1&a=2&b=3', None)
        >>> r.urlparts.geturl()
        'https://python.org/abc/de?a=1&a=2&b=3'
    """

    def __init__(self, environ, encoding=None, options=None):
        self.environ = environ
        self.config = Config(options, master=config)
        self.method = environ['REQUEST_METHOD']
        self.encoding = encoding or self.config.ENCODING

    @attribute
    def host(self):
        host = self.environ[self.config.ENVIRON_HOST]
        if ',' in host:
            host = host.rsplit(',', 1)[-1].strip()
        return host

    @attribute
    def remote_addr(self):
        addr = self.environ[self.config.ENVIRON_REMOTE_ADDR]
        if ',' in addr:
            addr = addr.split(',', 1)[0].strip()
        return addr

    @attribute
    def root_path(self):
        return self.environ['SCRIPT_NAME'] + '/'

    @attribute
    def path(self):
        return self.environ['SCRIPT_NAME'] + self.environ['PATH_INFO']

    @attribute
    def headers(self):
        return HTTPRequestHeaders(self.environ)

    @attribute
    def query(self):
        return defaultdict(list, parse_qs(
            self.environ['QUERY_STRING'],
            encoding=self.encoding
        ))

    @attribute
    def form(self):
        form, self.files = self.load_body()
        return form

    @attribute
    def files(self):
        self.form, files = self.load_body()
        return files

    @attribute
    def cookies(self):
        try:
            return parse_cookie(self.environ['HTTP_COOKIE'])
        except:
            return {}

    @attribute
    def ajax(self):
        return self.environ.get(
                'HTTP_X_REQUESTED_WITH', None) == 'XMLHTTPRequest'

    @attribute
    def secure(self):
        return self.environ.get(self.config.ENVIRON_HTTPS) == \
                self.config.ENVIRON_HTTPS_VALUE

    @attribute
    def scheme(self):
        if (self.secure):
            return 'https'
        else:
            return 'http'

    @attribute
    def urlparts(self):
        return UrlParts((self.scheme, self.host,
            self.path, self.environ['QUERY_STRING'], None))

    def load_body(self):
        """ Load http request body and returns
            form data and files.

            >>> from wheezy.core.collections import last_item_adapter
            >>> from wheezy.http import sample
            >>> environ = {}
            >>> sample.request(environ)

            Load form as application/x-www-form-urlencoded

            >>> sample.request_urlencoded(environ)
            >>> r = HTTPRequest(environ)
            >>> assert len(r.form) == 2
            >>> r.form['greeting']
            ['Hello World', 'Hallo Welt']
            >>> form = last_item_adapter(r.form)
            >>> form['greeting']
            'Hallo Welt'
            >>> assert r.files is None

            Load form as multipart/form-data.

            >>> sample.request_multipart(environ)
            >>> r = HTTPRequest(environ)
            >>> assert len(r.form) == 1
            >>> assert len(r.files) == 1

            Load files first this time

            >>> sample.request_multipart(environ)
            >>> r = HTTPRequest(environ)
            >>> assert len(r.files) == 1
            >>> assert len(r.form) == 1

            Content-Length exceed maximum allowed

            >>> cl = r.config.MAX_CONTENT_LENGTH + 1
            >>> environ['CONTENT_LENGTH'] = str(cl)
            >>> r = HTTPRequest(environ)
            >>> r.load_body() # doctest: +ELLIPSIS
            Traceback (most recent call last):
                ...
            ValueError: ...
        """
        environ = self.environ
        cl = environ.get('CONTENT_LENGTH', '0')
        icl = int(cl)
        if (icl > self.config.MAX_CONTENT_LENGTH):
            raise ValueError('Maximum content length exceeded')
        fp = environ['wsgi.input']
        ct = environ['CONTENT_TYPE']
        if ct.startswith('m'):
            return parse_multipart(fp, ct, cl, self.encoding)
        else:
            qs = bton(fp.read(icl), self.encoding)
            return defaultdict(list, parse_qs(qs, self.encoding)), None
