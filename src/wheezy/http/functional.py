
""" ``testing`` module.
"""
import re

from wheezy.core.collections import defaultdict
from wheezy.core.comp import urlsplit
from wheezy.http.comp import BytesIO
from wheezy.http.comp import PY3
from wheezy.http.comp import SimpleCookie
from wheezy.http.comp import b
from wheezy.http.comp import bytes_type
from wheezy.http.comp import ntob
from wheezy.http.comp import urlencode


RE_FORMS = re.compile(r'<form.*?</form>', re.DOTALL)
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
            form_target = FormTarget()
            html_parser = HTMLParserAdapter(form_target)
            for form in RE_FORMS.findall(self.content):
                html_parser.feed(form)
            self.__forms = form_target.forms
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
            'PATH_INFO': path,
            'QUERY_STRING': query
        }
        if status_code == 307:
            method = self.environ['REQUEST_METHOD']
        else:
            method = 'GET'
        return self.go(None, method, None, environ)

    def go(self, path=None, method='GET', params=None, environ=None):
        """ Simulate valid request to WSGI application.
        """
        if environ:
            environ = dict(self.environ, **environ)
        else:
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
            params = [(k, v.encode('utf-8'))
                      for k in params for v in params[k]]
            content = urlencode(params)
            if method == 'GET':
                path_query = environ['QUERY_STRING']
                if path_query:
                    content = path_query + '&' + content
                environ.update({
                    'QUERY_STRING': content,
                    'CONTENT_TYPE': '',
                    'CONTENT_LENGTH': '',
                    'wsgi.input': BytesIO(b(''))
                })
            else:
                environ = dict(environ, **{
                    'CONTENT_TYPE': 'application/x-www-form-urlencoded',
                    'CONTENT_LENGTH': str(len(content)),
                    'wsgi.input': BytesIO(ntob(content, 'utf-8'))
                })

        if self.cookies:
            environ['HTTP_COOKIE'] = '; '.join(
                '%s=%s' % cookie for cookie in self.cookies.items())
        else:
            if 'HTTP_COOKIE' in environ:
                del environ['HTTP_COOKIE']

        if hasattr(self, '_WSGIClient__content'):
            del self.__content  # pragma: nocover
        if hasattr(self, '_WSGIClient__forms'):
            del self.__forms  # pragma: nocover
        self.status = ''
        self.status_code = 0
        self.headers = defaultdict(list)
        self.response = []

        def write(chunk):  # pragma: nocover
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
            self.response.extend(result)
        finally:
            if hasattr(result, 'close'):  # pragma: nocover
                result.close()

        for cookie_string in self.headers['Set-Cookie']:
            cookies = SimpleCookie(cookie_string)
            for name in cookies:
                value = cookies[name].value
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
        value = self.params[name]
        return value and value[0] or ''

    def __setattr__(self, name, value):
        self.params[name] = [value]

    def errors(self, css_class='error'):
        elements = self.elements
        return [name for name in sorted(elements.keys())
                if css_class in elements[name].get('class', '')]

    def update(self, params):
        for name, value in params.items():
            if isinstance(value, list):
                self.params[name] = value
            else:
                self.params[name] = [value]


class FormTarget(object):
    """ FormTarget finds forms and elements like input, select, etc.
    """

    def __init__(self):
        self.forms = []
        self.pending = []
        self.lasttag = None

    def handle_starttag(self, tag, attrs):
        self.lasttag = tag
        if tag == 'input':
            attrs = dict(attrs)
            name = attrs.pop('name', '')
            if name:
                element_type = attrs.get('type', '')
                if element_type == 'submit':
                    return
                form = self.forms[-1]
                form.elements[name] = attrs
                if element_type == 'checkbox' and 'checked' not in attrs:
                    return
                form.params[name].append(attrs.pop('value', ''))
        elif tag == 'option':
            attrs = dict(attrs)
            if 'selected' in attrs:
                name = self.pending[-1]
                self.forms[-1].params[name].append(attrs.pop('value', ''))
        elif tag == 'form':
            self.forms.append(Form(dict(attrs)))
        elif tag in ('select', 'textarea'):
            attrs = dict(attrs)
            name = attrs.pop('name', '')
            if name:
                self.forms[-1].elements[name] = attrs
                self.pending.append(name)

    def handle_endtag(self, tag):
        if self.pending and tag in ('select', 'textarea'):
            del self.pending[-1]

    def handle_data(self, data):
        if self.pending and self.lasttag == 'textarea':
            form = self.forms[-1]
            name = self.pending.pop()
            form.params[name].append(data)


try:  # pragma: nocover
    from lxml.etree import HTMLParser
    from lxml.etree import fromstring

    class HTMLParserAdapter(object):

        def __init__(self, target):
            self.start = target.handle_starttag
            self.end = target.handle_endtag
            self.data = target.handle_data
            self.parser = HTMLParser(target=self)

        def comment(self, text):
            pass

        def close(self):
            pass

        def feed(self, content):
            fromstring(content, parser=self.parser)

except ImportError:  # pragma: nocover

    if PY3:  # pragma: nocover
        from html.parser import HTMLParser
    else:  # pragma: nocover
        from HTMLParser import HTMLParser

    class HTMLParserAdapter(HTMLParser):

        def __init__(self, target):
            self.strict = True
            self.reset()
            self.target = target
            self.handle_starttag = target.handle_starttag
            self.handle_endtag = target.handle_endtag
            self.handle_startendtag = target.handle_starttag
            self.handle_data = target.handle_data


def parse_path(path):
    """
        >>> sorted(parse_path('abc?def').items())
        [('PATH_INFO', 'abc'), ('QUERY_STRING', 'def')]

        >>> sorted(parse_path('abc').items())
        [('PATH_INFO', 'abc'), ('QUERY_STRING', '')]
    """
    if '?' in path:
        path, qs = path.split('?')
        return {'PATH_INFO': path, 'QUERY_STRING': qs}
    else:
        return {'PATH_INFO': path, 'QUERY_STRING': ''}
