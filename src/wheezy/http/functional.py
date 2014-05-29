
""" ``functional`` module.
"""
import re

from wheezy.core.benchmark import Benchmark
from wheezy.core.benchmark import Timer
from wheezy.core.collections import attrdict
from wheezy.core.collections import defaultdict
from wheezy.core.comp import json_loads
from wheezy.core.comp import urlsplit
from wheezy.http.comp import BytesIO
from wheezy.http.comp import PY3
from wheezy.http.comp import SimpleCookie
from wheezy.http.comp import b
from wheezy.http.comp import ntob
from wheezy.http.comp import urlencode


RE_FORMS = re.compile(r'<form.*?</form>', re.DOTALL)
DEFAULT_ENVIRON = {
    'REMOTE_ADDR': '127.0.0.1',
    'SCRIPT_NAME': '',
    'SERVER_NAME': 'localhost',
    'SERVER_PORT': '8080',

    'HTTP_HOST': 'localhost:8080',
    'HTTP_USER_AGENT': 'Mozilla/5.0 (X11; Linux i686)',
    'HTTP_ACCEPT': 'text/html,application/xhtml+xml,'
    'application/xml;q=0.9,*/*;q=0.8',
    'HTTP_ACCEPT_LANGUAGE': 'en-us,en;q=0.5',
    'HTTP_ACCEPT_CHARSET': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',

    'wsgi.url_scheme': 'http'
}


class PageMixin(object):
    """ Page form submit use case.
    """

    def form(self):
        """ Concrete page can override this method to provide
            form location.
        """
        return self.client.form

    def submit(self, **kwargs):
        """ Submits page with given `kwargs` as form params.

            Returns any form errors found. If form is not found
            returns None.
        """
        form = self.form()
        form.update(kwargs)
        self.client.submit(form)
        form = self.form()
        if form is None:
            return None
        return form.errors()

    def ajax_submit(self, **kwargs):
        """ Submits page via AJAX with given `kwargs` as form params.

            Returns HTTP status code.
        """
        form = self.form()
        form.update(kwargs)
        return self.client.ajax_submit(form)


class BenchmarkMixin(object):  # pragma: nocover
    """ Benchmark test case helper.
    """

    def benchmark(self, targets, number=1000):
        """ Setup benchmark for given `targets` with timing set
            at WSGI application entry point.
        """
        return Benchmark(targets, number,
                         timer=Timer(self.client, 'application'))


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
        self.__content = None
        self.__forms = None
        self.__json = None

    @property
    def content(self):
        """ Return content of the response. Applies decodes response
            stream.
        """
        if self.__content is None:
            self.__content = (b('').join(
                [c for c in self.response])).decode('utf-8')
        return self.__content

    @property
    def json(self):
        """ Returns a json response.
        """
        if self.__json is None:
            assert 'application/json' in self.headers['Content-Type'][0]
            self.__json = json_loads(self.content, object_hook=attrdict)
        return self.__json

    @property
    def forms(self):
        """ All forms found in content.
        """
        if self.__forms is None:
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
        return self.forms and self.forms[0] or Form()

    def form_by(self, predicate=None, **kwargs):
        """ Search a form by `predicate` or
            form attribute exact match::

                client.form_by(action='/en/signin')
                client.form_by(lambda attrs:
                               'signin' in attrs.get('action', ''))
        """
        if not predicate:
            def predicate(attrs):
                for name in kwargs:
                    if kwargs[name] == attrs.get(name):
                        return True
                return False
        for form in self.forms:
            if predicate(form.attrs):
                return form
        return None

    def get(self, path=None, **kwargs):
        """ Issue GET HTTP request to WSGI application.
        """
        return self.go(path, method='GET', **kwargs)

    def ajax_get(self, path=None, **kwargs):
        """ Issue GET HTTP AJAX request to WSGI application.
        """
        return self.ajax_go(path, method='GET', **kwargs)

    def head(self, path=None, **kwargs):
        """ Issue HEAD HTTP request to WSGI application.
        """
        return self.go(path, method='HEAD', **kwargs)

    def post(self, path=None, **kwargs):
        """ Issue POST HTTP request to WSGI application.
        """
        return self.go(path, method='POST', **kwargs)

    def ajax_post(self, path=None, **kwargs):
        """ Issue POST HTTP AJAX request to WSGI application.
        """
        return self.ajax_go(path, method='POST', **kwargs)

    def submit(self, form=None, environ=None):
        """ Submits given form. Takes ``action`` and ``method``
            form attributes into account.
        """
        form = form or self.form
        path = form.attrs.get('action')
        method = form.attrs.get('method', 'GET').upper()
        return self.go(path, method, form.params, environ)

    def ajax_submit(self, form=None, environ=None):
        """ Submits given form. Takes ``action`` and ``method``
            form attributes into account.
        """
        environ = environ or {}
        environ['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        return self.submit(form, environ)

    def follow(self):
        """ Follows HTTP redirect (e.g. status code 302).
        """
        sc = self.status_code
        assert sc in [207, 301, 302, 303, 307]
        location = self.headers['Location'][0]
        scheme, netloc, path, query, fragment = urlsplit(location)
        environ = {
            'wsgi.url_scheme': scheme,
            'HTTP_HOST': netloc,
            'PATH_INFO': path,
            'QUERY_STRING': query
        }
        method = sc == 307 and self.environ['REQUEST_METHOD'] or 'GET'
        return self.go(None, method, None, environ)

    def ajax_go(self, path=None, method='GET', params=None, environ=None):
        environ = environ or {}
        environ['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        return self.go(path, method, params, environ)

    def go(self, path=None, method='GET', params=None, environ=None):
        """ Simulate valid request to WSGI application.
        """
        environ = environ and dict(self.environ, **environ) or self.environ
        environ.update({
            'REQUEST_METHOD': method,
            'CONTENT_TYPE': '',
            'CONTENT_LENGTH': '',
            'wsgi.input': BytesIO(b(''))
        })
        path and environ.update(parse_path(path))
        if params:
            content = urlencode([(k, v.encode('utf-8'))
                                 for k in params for v in params[k]])
            if method == 'GET':
                environ['QUERY_STRING'] = '&'.join((
                    content, environ['QUERY_STRING']))
            else:
                environ.update({
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

        self.__content = None
        self.__forms = None
        self.__json = None
        self.status_code = 0
        self.headers = defaultdict(list)
        self.response = []

        def start_response(status, headers):
            self.status_code = int(status.split(' ', 1)[0])
            h = self.headers
            for name, value in headers:
                h[name].append(value)
            return self.response.append

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
            if 'name' in attrs:
                element_type = attrs.get('type')
                if element_type == 'submit':
                    return
                name = attrs.pop('name')
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
            if 'name' in attrs:
                name = attrs.pop('name')
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
        from HTMLParser import HTMLParser  # noqa

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
    """ Splits `path` into a PATH_INFO and QUERY_STRING.
    """
    if '?' in path:
        path, qs = path.split('?')
        return {'PATH_INFO': path, 'QUERY_STRING': qs}
    else:
        return {'PATH_INFO': path, 'QUERY_STRING': ''}
