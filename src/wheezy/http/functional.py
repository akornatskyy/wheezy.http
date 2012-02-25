
""" ``testing`` module.
"""

from wheezy.core.collections import defaultdict
from wheezy.core.comp import urlsplit
from wheezy.http.comp import BytesIO
from wheezy.http.comp import HTMLParser
from wheezy.http.comp import b
from wheezy.http.comp import bytes_type
from wheezy.http.comp import ntob
from wheezy.http.comp import urlencode
from wheezy.http.parse import parse_cookie


DEFAULT_ENVIRON = {
        'REQUEST_METHOD': 'GET',
        'REMOTE_HOST': 'localhost',
        'REMOTE_ADDR': '127.0.0.1',
        'SCRIPT_NAME': '',
        'PATH_INFO': '/',
        'QUERY_STRING': '',
        'GATEWAY_INTERFACE': 'CGI/1.1',
        'SERVER_PROTOCOL': 'HTTP/1.0',
        'SERVER_NAME': 'localhost',
        'SERVER_PORT': '8080',
        'CONTENT_TYPE': '',
        'CONTENT_LENGTH': '',

        'HTTP_HOST': 'localhost:8080',
        'HTTP_USER_AGENT': 'Mozilla/5.0 (X11; Linux i686)',
        'HTTP_ACCEPT': 'text/html,application/xhtml+xml,'
                    'application/xml;q=0.9,*/*;q=0.8',
        'HTTP_ACCEPT_LANGUAGE': 'en-us,en;q=0.5',
        'HTTP_ACCEPT_CHARSET': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',

        'wsgi.url_scheme': 'http',
        'wsgi.multithread': True,
        'wsgi.multiprocess': False,
        'wsgi.run_once': False,
        'wsgi.input': BytesIO(b(''))
}


class WSGIClient(object):
    """ WSGI client simulates WSGI requests in order to accomplish
        functional testing for any WSGI application.
    """

    def __init__(self, application, environ=None):
        self.application = application
        self.environ = dict(DEFAULT_ENVIRON)
        if environ is not None:
            self.environ.update(environ)
        self.cookies = {}

    @property
    def content(self):
        """ Return content of the response. Applies decodes response
            stream.
        """
        if not hasattr(self, '_WSGIClient__content'):
            self.__content = ''.join(map(
                lambda chunk: chunk.decode('utf-8'),
                self.response))
        return self.__content

    @property
    def forms(self):
        """ All forms found in content.
        """
        if not hasattr(self, '_WSGIClient__forms'):
            form_parser = FormParser()
            form_parser.feed(self.content)
            self.__forms = form_parser.forms
        return self.__forms

    @property
    def form(self):
        """ First form or empty one.
        """
        forms = self.forms
        if len(forms) > 0:
            return self.forms[0]
        else:
            return Form()

    def get(self, path=None, **kwargs):
        """ Issue GET HTTP request to WSGI application.
        """
        return self.go(path, method='GET', **kwargs)

    def head(self, path=None, **kwargs):
        """ Issue HEAD HTTP request to WSGI application.
        """
        return self.go(path, method='HEAD', **kwargs)

    def post(self, path=None, **kwargs):
        """ Issue POST HTTP request to WSGI application.
        """
        return self.go(path, method='POST', **kwargs)

    def submit(self, form=None, environ=None):
        """ Submits given form. Takes ``action`` and ``method``
            form attributes into account.
        """
        form = form or self.form
        path = form.attrs.get('action', None)
        method = form.attrs.get('method', 'GET').upper()
        return self.go(path, method, form.params, environ)

    def follow(self):
        """ Follows HTTP redirect (e.g. status code 302).
        """
        status_code = self.status_code
        assert status_code in [207, 301, 302, 303, 307]
        location = self.headers['Location'][0]
        scheme, netloc, path, query, fragment = urlsplit(location)
        environ = {
                'wsgi.url_scheme': scheme,
                'HTTP_HOST': netloc,
        }
        if query:
            environ['QUERY_STRING'] = query
        if status_code == 307:
            method = self.environ['REQUEST_METHOD']
        else:
            method = 'GET'
        return self.go(path, method, environ=environ)

    def go(self, path=None, method='GET', params=None, environ=None):
        """ Simulate valid request to WSGI application.
        """
        if environ:
            self.environ.update(environ)
        environ = self.environ
        if path:
            environ.update(parse_path(path))
        environ['REQUEST_METHOD'] = method
        if params is None:
            environ.update({
                'CONTENT_TYPE': '',
                'CONTENT_LENGTH': '',
                'wsgi.input': BytesIO(b(''))
            })
        else:
            params = [(k, v[0].encode('utf-8'))
                    for k, v in params.items()]
            content = urlencode(params)
            environ = dict(environ or {})
            environ.update({
                'CONTENT_TYPE': 'application/x-www-form-urlencoded',
                'CONTENT_LENGTH': str(len(content)),
                'wsgi.input': BytesIO(ntob(content, 'utf-8'))
            })

        environ['HTTP_COOKIE'] = '; '.join(
                '%s=%s' % cookie for cookie in self.cookies.items())

        if hasattr(self, '_WSGIClient__content'):
            del self.__content
        if hasattr(self, '_WSGIClient__forms'):
            del self.__forms
        self.status = ''
        self.status_code = 0
        self.headers = defaultdict(list)
        self.response = []

        def write(chunk):
            assert isinstance(chunk, bytes_type)
            self.response.append(chunk)

        def start_response(status, headers):
            self.status_code = int(status.split(' ', 1)[0])
            self.status = status
            for name, value in headers:
                self.headers[name].append(value)
            return write

        result = self.application(environ, start_response)
        try:
            for chunk in result:
                write(chunk)
        finally:
            if hasattr(result, 'close'):
                result.close()

        for cookie_string in self.headers['Set-Cookie']:
            for name, value in parse_cookie(cookie_string).items():
                if value:
                    self.cookies[name] = value
                elif name in self.cookies:
                    del self.cookies[name]

        return self.status_code


class Form(object):
    """ Form class represent HTML form. It stores form tag attributes,
        params that can be used in form submission as well as related
        HTML elements.
    """

    def __init__(self, attrs=None):
        self.__dict__['attrs'] = attrs or {}
        self.__dict__['params'] = defaultdict(list)
        self.__dict__['elements'] = defaultdict(dict)

    def __getitem__(self, name):
        return self.params[name]

    def __getattr__(self, name):
        return self.params[name][0]

    def __setattr__(self, name, value):
        self.params[name] = [value]

    def errors(self, css_class='error'):
        return [name for name, attrs in self.elements.items()
                if css_class in attrs.get('class', '')]

    def update(self, params):
        for name, value in params.items():
            if isinstance(value, list):
                self.params[name] = value
            else:
                self.params[name] = [value]


class FormParser(HTMLParser):
    """ FormParser finds forms and elements like input, select, etc.
    """

    def __init__(self):
        self.strict = True
        self.reset()
        self.forms = []
        self.pending = []

    def handle_starttag(self, tag, attrs):
        if tag == 'form':
            self.forms.append(Form(dict(attrs)))
        elif tag == 'select':
            attrs = dict(attrs)
            name = str(attrs.pop('name', ''))
            if name:
                form = self.forms[-1]
                form.elements[name] = attrs
                self.pending.append(name)
        elif tag == 'option':
            attrs = dict(attrs)
            if attrs.get('selected', '') == 'selected':
                name = self.pending[-1]
                form = self.forms[-1]
                form.params[name].append(attrs.pop('value', ''))

    def handle_endtag(self, tag):
        if tag == 'select':
            del self.pending[-1]

    def handle_startendtag(self, tag, attrs):
        if tag == 'input':
            attrs = dict(attrs)
            name = str(attrs.pop('name', ''))
            if name:
                form = self.forms[-1]
                form.elements[name] = attrs
                if attrs.get('type', '') == 'checkbox' \
                        and not attrs.get('checked', ''):
                    return
                form.params[name].append(attrs.pop('value', ''))


def parse_cookies(cookies):
    """
        >>> parse_cookies(['a=1;b=2'])
        {'a': '1', 'b': '2'}
    """
    result = {}
    for cookie in cookies:
        result.update(parse_cookie(cookie))
    return result


def parse_path(path):
    """
        >>> parse_path('abc?def')
        {'QUERY_STRING': 'def', 'PATH_INFO': 'abc'}
        >>> parse_path('abc')
        {'PATH_INFO': 'abc'}
    """
    if '?' in path:
        path, qs = path.split('?')
    else:
        qs = ''
    environ = {'PATH_INFO': path}
    if qs:
        environ['QUERY_STRING'] = qs
    return environ
