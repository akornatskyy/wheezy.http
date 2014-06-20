
""" Unit tests for ``wheezy.http.functional``.
"""

import unittest

from mock import Mock
from mock import patch


class DefaultEnvironTestCase(unittest.TestCase):
    """ Test the ``DEFAULT_ENVIRON``.
    """

    def test_default_options(self):
        """ Ensure required keys exist.
        """
        from wheezy.http.functional import DEFAULT_ENVIRON

        required = tuple(sorted(DEFAULT_ENVIRON.keys()))
        assert 10 == len(required)
        assert ('HTTP_ACCEPT', 'HTTP_ACCEPT_CHARSET', 'HTTP_ACCEPT_LANGUAGE',
                'HTTP_HOST', 'HTTP_USER_AGENT', 'REMOTE_ADDR', 'SCRIPT_NAME',
                'SERVER_NAME', 'SERVER_PORT', 'wsgi.url_scheme') == required


class WSGIClientInitTestCase(unittest.TestCase):
    """ Test the ``WSGIClient.__init__``.
    """

    def test_default(self):
        """ Only required args passed.
        """
        from wheezy.http.functional import WSGIClient

        client = WSGIClient('app')

        assert 'app' == client.application
        assert len(client.environ) > 0
        assert {} == client.cookies

    def test_override_environ(self):
        """ Overriding environ.
        """
        from wheezy.http.functional import WSGIClient

        client = WSGIClient('app', environ={
            'REQUEST_METHOD': 'POST'
        })

        assert 'POST' == client.environ['REQUEST_METHOD']


class WSGIClientTestCase(unittest.TestCase):
    """ Test the ``WSGIClient`` class.
    """

    def setup_client(self, response=None):
        from wheezy.http.application import WSGIApplication
        from wheezy.http.config import bootstrap_http_defaults
        from wheezy.http.functional import WSGIClient
        from wheezy.http.response import HTTPResponse

        self.mock_middleware = Mock(return_value=response or HTTPResponse())
        return WSGIClient(WSGIApplication(middleware=[
            bootstrap_http_defaults,
            Mock(return_value=self.mock_middleware)
        ], options={}))

    def test_content(self):
        """ content
        """
        from wheezy.http.response import HTTPResponse

        response = HTTPResponse()
        response.write('te')
        response.write('st')
        client = self.setup_client(response)

        assert 200 == client.get('/abc')
        assert 'test' == client.content

    def test_json(self):
        """ json response
        """
        from wheezy.http import response
        from wheezy.http import functional
        from wheezy.http.response import json_response

        patcher = patch.object(response, 'json_encode')
        mock_json_encode = patcher.start()
        mock_json_encode.return_value = '{}'

        obj = {'a': 1, 'b': 'x'}
        response = json_response(obj)
        client = self.setup_client(response)

        assert 200 == client.get('/abc')
        patcher.stop()

        patcher = patch.object(functional, 'json_loads')
        mock_json_encode = patcher.start()
        mock_json_encode.return_value = obj
        assert obj == client.json
        patcher.stop()

    def test_assert_json(self):
        """ Expecting json response but content type is not valid.
        """
        from wheezy.http.response import HTTPResponse

        response = HTTPResponse()
        client = self.setup_client(response)

        assert 200 == client.get('/abc')
        self.assertRaises(AssertionError, lambda: client.json)

    def test_forms(self):
        """ forms
        """
        from wheezy.http.response import HTTPResponse
        response = HTTPResponse()
        response.write("""
            <form action='/test' method='POST'>
            </form>
        """)
        client = self.setup_client(response)

        assert 200 == client.get('/abc')
        assert 1 == len(client.forms)

    def test_form(self):
        """ forms
        """
        from wheezy.http.response import HTTPResponse
        response = HTTPResponse()
        response.write("""
            <form action='/test' method='POST'>
            </form>
        """)
        client = self.setup_client(response)

        assert 200 == client.get('/abc')
        form = client.form
        assert '/test' == form.attrs['action']
        assert 'POST' == form.attrs['method']

    def test_form_by_attribute(self):
        """ forms
        """
        from wheezy.http.response import HTTPResponse
        response = HTTPResponse()
        response.write("""
            <form id='test' action='/test1'>
            </form>
            <form action='/test2' method='POST'>
            </form>
        """)
        client = self.setup_client(response)

        assert 200 == client.get('/abc')
        form = client.form_by(id='test')
        assert '/test1' == form.attrs['action']

        form = client.form_by(action='/test1')
        assert '/test1' == form.attrs['action']

        assert not client.form_by(action='x')

    def test_form_by_predicate(self):
        """ forms
        """
        from wheezy.http.response import HTTPResponse
        response = HTTPResponse()
        response.write("""
            <form id='test' action='/test1'>
            </form>
            <form action='/test2' method='POST'>
            </form>
        """)
        client = self.setup_client(response)

        assert 200 == client.get('/abc')
        form = client.form_by(
            lambda attrs: 'test2' in attrs.get('action', ''))
        assert '/test2' == form.attrs['action']
        assert 'POST' == form.attrs['method']

        assert not client.form_by(
            lambda attrs: 'x' in attrs.get('action', ''))

    def test_default_form(self):
        """ form
        """
        client = self.setup_client()

        assert 200 == client.get('/abc')
        assert client.form

    def test_get(self):
        """ get
        """
        client = self.setup_client()

        assert 200 == client.get('/abc')
        request, following = self.mock_middleware.call_args[0]
        assert 'GET' == request.method

    def test_get_with_query_string(self):
        """ get
        """
        client = self.setup_client()

        assert 200 == client.get('/abc?x=1')
        request, following = self.mock_middleware.call_args[0]
        assert '/abc' == request.path
        assert {'x': ['1']} == request.query

    def test_ajax_get(self):
        """ ajax get
        """
        client = self.setup_client()

        assert 200 == client.ajax_get('/abc')
        request, following = self.mock_middleware.call_args[0]
        assert 'GET' == request.method
        assert 'XMLHttpRequest' == request.environ['HTTP_X_REQUESTED_WITH']

    def test_head(self):
        """ head
        """
        client = self.setup_client()

        assert 200 == client.head('/abc')
        request, following = self.mock_middleware.call_args[0]
        assert 'HEAD' == request.method

    def test_post(self):
        """ post
        """
        client = self.setup_client()

        assert 200 == client.post('/abc')
        request, following = self.mock_middleware.call_args[0]
        assert 'POST' == request.method

    def test_ajax_post(self):
        """ ajax post
        """
        client = self.setup_client()

        assert 200 == client.ajax_post('/abc')
        request, following = self.mock_middleware.call_args[0]
        assert 'POST' == request.method
        assert 'XMLHttpRequest' == request.environ['HTTP_X_REQUESTED_WITH']

    def test_post_content(self):
        """ post content
        """
        from wheezy.http import request
        patcher = patch.object(request, 'json_loads')
        mock_json_encode = patcher.start()
        mock_json_encode.return_value = {'x': 1}
        client = self.setup_client()

        assert 200 == client.post(
            '/abc',
            content_type='application/json',
            content='{"x": 1}')
        patcher.stop()
        request, following = self.mock_middleware.call_args[0]
        assert 'POST' == request.method
        assert mock_json_encode.return_value == request.form

    def test_post_stream(self):
        """ post stream
        """
        from wheezy.http.comp import BytesIO
        from wheezy.http import request
        patcher = patch.object(request, 'json_loads')
        mock_json_encode = patcher.start()
        mock_json_encode.return_value = {'x': 1}
        client = self.setup_client()

        assert 200 == client.post(
            '/abc',
            content_type='application/json',
            stream=BytesIO('{"x": 1}'.encode('ascii')))
        patcher.stop()
        request, following = self.mock_middleware.call_args[0]
        assert 'POST' == request.method
        assert mock_json_encode.return_value == request.form

    def test_submit_with_get(self):
        """ get
        """
        from wheezy.http.functional import Form
        client = self.setup_client()

        values = {'a': ['a1', 'a2'], 'b': ['b1']}
        form = Form({
            'action': '/abc',
            'method': 'get'
        })
        form.update(values)
        assert 200 == client.submit(form)

        request, following = self.mock_middleware.call_args[0]
        assert '/abc' == request.path
        assert 'GET' == request.method
        assert values == request.query

    def test_ajax_submit(self):
        """ ajax get
        """
        from wheezy.http.functional import Form
        client = self.setup_client()

        values = {'a': ['a1', 'a2'], 'b': ['b1']}
        form = Form({
            'action': '/abc',
            'method': 'get'
        })
        form.update(values)
        assert 200 == client.ajax_submit(form)

        request, following = self.mock_middleware.call_args[0]
        assert '/abc' == request.path
        assert 'GET' == request.method
        assert values == request.query
        assert 'XMLHttpRequest' == request.environ['HTTP_X_REQUESTED_WITH']

    def test_submit_with_get_and_path_query(self):
        """ get
        """
        from wheezy.http.functional import Form
        client = self.setup_client()

        values = {'b': ['b1']}
        form = Form({
            'action': '/abc?a=a1&a=a2',
            'method': 'get'
        })
        form.update(values)
        assert 200 == client.submit(form)

        request, following = self.mock_middleware.call_args[0]
        assert '/abc' == request.path
        assert 'GET' == request.method
        assert {'a': ['a1', 'a2'], 'b': ['b1']} == request.query

    def test_submit_with_post(self):
        """ post
        """
        from wheezy.http.functional import Form
        client = self.setup_client()

        values = {'a': ['a1', 'a2'], 'b': ['b1']}
        form = Form({
            'action': '/abc',
            'method': 'post'
        })
        form.update(values)
        assert 200 == client.submit(form)

        request, following = self.mock_middleware.call_args[0]
        assert '/abc' == request.path
        assert 'POST' == request.method
        assert values == request.form

    def test_follow(self):
        """ follow
        """
        from wheezy.http.response import found
        client = self.setup_client(response=found('/http302'))
        assert 302 == client.get('/abc')
        assert '/http302' == client.headers['Location'][0]

        from wheezy.http.response import see_other
        self.mock_middleware.return_value = see_other('/http303')
        assert 303 == client.follow()
        assert '/http303' == client.headers['Location'][0]

        from wheezy.http.response import permanent_redirect
        self.mock_middleware.return_value = permanent_redirect('/http301')
        assert 301 == client.follow()
        assert '/http301' == client.headers['Location'][0]

        from wheezy.http.response import temporary_redirect
        self.mock_middleware.return_value = temporary_redirect('/http307')
        assert 307 == client.follow()
        assert '/http307' == client.headers['Location'][0]

        from wheezy.http.response import ajax_redirect
        self.mock_middleware.return_value = ajax_redirect('/http207')
        assert 207 == client.follow()
        assert '/http207' == client.headers['Location'][0]

    def test_follow_with_query(self):
        """ follow when url has query string.
        """
        from wheezy.http.response import found
        client = self.setup_client(response=found('/http302?x=1'))
        assert 302 == client.get('/abc')
        assert '/http302?x=1' == client.headers['Location'][0]

        assert 302 == client.follow()

        request, following = self.mock_middleware.call_args[0]
        assert '/http302' == request.path
        assert {'x': ['1']} == request.query

    def test_set_cookie(self):
        """ process Set-Cookie HTTP response headers.
        """
        from wheezy.http.cookie import HTTPCookie
        from wheezy.http.response import HTTPResponse
        options = {
            'HTTP_COOKIE_DOMAIN': None,
            'HTTP_COOKIE_SECURE': True,
            'HTTP_COOKIE_HTTPONLY': True
        }
        cookie = HTTPCookie('c1', value='12345', options=options)
        response = HTTPResponse()
        response.cookies.append(cookie)
        cookie = HTTPCookie('c2', value='23456', options=options)
        response.cookies.append(cookie)
        client = self.setup_client()
        self.mock_middleware.return_value = response

        assert 200 == client.get('/abc')
        assert 2 == len(client.cookies)
        assert '12345' == client.cookies['c1']
        assert '23456' == client.cookies['c2']

        # Cookies remain accross requests.
        response.cookies = []
        assert 200 == client.get('/abc')
        assert 2 == len(client.cookies)
        request, following = self.mock_middleware.call_args[0]
        assert {'c1': '12345', 'c2': '23456'} == request.cookies

        # Cookie removed.
        cookie = HTTPCookie.delete('c2', options=options)
        response.cookies.append(cookie)
        assert 200 == client.get('/abc')
        assert 1 == len(client.cookies)
        assert '12345' == client.cookies['c1']

        # All cookies removed.
        cookie = HTTPCookie.delete('c1', options=options)
        response.cookies.append(cookie)
        assert 200 == client.get('/abc')
        assert 0 == len(client.cookies)
        assert 'HTTP_COOKIE' in client.environ
        assert 200 == client.get('/abc')
        assert 'HTTP_COOKIE' not in client.environ

    def test_pagemixin_form(self):
        """ PageMixin submit
        """
        from wheezy.http.response import HTTPResponse
        from wheezy.http.functional import PageMixin
        response = HTTPResponse()
        response.write("""
            <form action='/test1'>
            </form>
        """)
        client = self.setup_client(response)

        assert 200 == client.get('/abc')
        page = PageMixin()
        page.client = client
        form = page.form()

        assert '/test1' == form.attrs['action']

    def test_pagemixin_submit_form_not_found(self):
        """ PageMixin submit, form is not found.
        """
        from wheezy.http.response import HTTPResponse
        from wheezy.http.functional import PageMixin
        response = HTTPResponse()
        client = self.setup_client(response)

        assert 200 == client.get('/abc')
        forms = [None, client.form]
        page = PageMixin()
        page.form = lambda: forms.pop()
        page.client = client
        assert None == page.submit()
        assert not forms

    def test_pagemixin_submit(self):
        """ PageMixin submit.
        """
        from wheezy.http.response import HTTPResponse
        from wheezy.http.functional import PageMixin
        from wheezy.http.functional import Form
        response = HTTPResponse()
        client = self.setup_client(response)

        values = {'a': ['a1', 'a2'], 'b': ['b1']}
        form = Form({
            'action': '/abc',
            'method': 'post'
        })

        assert 200 == client.get('/abc')
        page = PageMixin()
        page.form = lambda: form
        page.client = client
        assert [] == page.submit(**values)

        request, following = self.mock_middleware.call_args[0]
        assert '/abc' == request.path
        assert 'POST' == request.method
        assert values == request.form

    def test_pagemixin_ajax_submit(self):
        """ PageMixin AJAX submit.
        """
        from wheezy.http.response import HTTPResponse
        from wheezy.http.functional import PageMixin
        from wheezy.http.functional import Form
        response = HTTPResponse()
        client = self.setup_client(response)

        values = {'a': ['a1', 'a2'], 'b': ['b1']}
        form = Form({
            'action': '/abc',
            'method': 'post'
        })

        assert 200 == client.get('/abc')
        page = PageMixin()
        page.form = lambda: form
        page.client = client
        assert 200 == page.ajax_submit(**values)

        request, following = self.mock_middleware.call_args[0]
        assert '/abc' == request.path
        assert 'POST' == request.method
        assert values == request.form


class FormTestCase(unittest.TestCase):
    """ Test the ``Form`` class.
    """

    def test_params(self):
        """ Manipulation with form params.
        """
        from wheezy.http.functional import Form

        form = Form()
        form.update({'a': ['1', '2'], 'b': '3'})
        form.c = '4'

        assert '1' == form.a
        assert ['1', '2'] == form['a']
        assert '3' == form.b
        assert ['3'] == form['b']
        assert '4' == form.c
        assert ['4'] == form['c']

    def test_errors(self):
        """ Take form errors.
        """
        from wheezy.http.functional import Form

        form = Form()
        form.elements['a'] = {'class': 'error'}
        form.elements['b'] = {'class': 'x y'}
        form.elements['c'] = {'class': 'x error y'}

        assert ['a', 'c'] == form.errors()


class FormTargetTestCase(unittest.TestCase):
    """ Test the ``FormTarget`` class.
    """

    def setUp(self):
        from wheezy.http.functional import FormTarget
        from wheezy.http.functional import HTMLParserAdapter
        self.target = FormTarget()
        self.parser = HTMLParserAdapter(self.target)

    def test_form_tag(self):
        """ Parse HTML form tag.
        """
        self.parser.feed("""
            <form action="/test" method="post">
            </form>
        """)

        assert 1 == len(self.target.forms)
        form = self.target.forms[0]
        assert '/test' == form.attrs['action']
        assert 'post' == form.attrs['method']

    def test_select_tag(self):
        """ Parse HTML select tag.
        """
        self.parser.feed("""
            <form action="/test" method="post">
                <select name="answer">
                    <option selected="selected" value="-">---</option>
                    <option value="y">Yes</option>
                    <option value="n">No</option>
                </select>
            </form>
        """)

        form = self.target.forms[0]
        assert ['-'] == form.params['answer']
        assert '-' == form.answer

    def test_select_multiple_tag(self):
        """ Parse HTML select multiple tag.
        """
        self.parser.feed("""
            <form action="/test" method="post">
                <select name="color" multiple="multiple">
                    <option value="g">Green</option>
                    <option selected="selected" value="r">Red</option>
                    <option selected="selected" value="y">Yellow</option>
                </select>
            </form>
        """)

        form = self.target.forms[0]
        assert ['r', 'y'] == form.params['color']
        assert 'r' == form.color

    def test_select_tag_no_selection(self):
        """ Parse HTML select tag bu there is no option selected.
        """
        self.parser.feed("""
            <form action="/test" method="post">
                <select name="answer">
                    <option value="y">Yes</option>
                    <option value="n">No</option>
                </select>
            </form>
        """)

        form = self.target.forms[0]
        assert [] == form.params['answer']
        assert '' == form.answer

    def test_textarea_tag(self):
        """ Parse HTML textarea tag.
        """
        self.parser.feed("""
            <form action="/test" method="post">
                <textarea name="text">welcome!</textarea>
            </form>
        """)

        form = self.target.forms[0]
        assert 'welcome!' == form.text

    def test_textarea_tag_empty(self):
        """ Parse HTML textarea tag with empty data.
        """
        self.parser.feed("""
            <form action="/test" method="post">
                <textarea name="text"></textarea>
            </form>
        """)

        form = self.target.forms[0]
        assert [] == form.params['text']
        assert '' == form.text

    def test_input_tag_type_text(self):
        """ Parse HTML input[type="text"] tag.
        """
        self.parser.feed("""
            <form action="/test" method="post">
                <input id="user-id" name="user_id" type="text"
                    value="john" autocomplete="off" />
            </form>
        """)

        form = self.target.forms[0]
        assert 'john' == form.user_id
        assert {
            'autocomplete': 'off',
            'id': 'user-id',
            'type': 'text'
        } == form.elements['user_id']

    def test_input_tag_type_submit(self):
        """ Parse HTML input[type="submit"] tag.
        """
        self.parser.feed("""
            <form action="/test" method="post">
                <input name="update" type="submit" value="Update" />
            </form>
        """)

        form = self.target.forms[0]
        assert 0 == len(form.params)

    def test_input_tag_type_checkbox(self):
        """ Parse HTML input[type="checkbox"] tag.
        """
        self.parser.feed("""
            <form action="/test" method="post">
                <input name="remember_me" type="checkbox" value="1"
                   checked="checked" />
            </form>
        """)

        form = self.target.forms[0]
        assert '1' == form.remember_me

    def test_input_tag_type_checkbox_unchecked(self):
        """ Parse HTML input[type="checkbox"] tag not checked.
        """
        self.parser.feed("""
            <form action="/test" method="post">
                <input name="remember_me" type="checkbox" value="1" />
            </form>
        """)

        form = self.target.forms[0]
        assert 'remember_me' not in form.params
