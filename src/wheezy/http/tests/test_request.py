
""" Unit tests for ``wheezy.http.request``.
"""

import unittest


class HTTPRequestTestCase(unittest.TestCase):
    """ Test the ``HTTPRequest`` class.
    """

    def setUp(self):
        from wheezy.http.request import HTTPRequest
        self.options = {
            'MAX_CONTENT_LENGTH': 1024
        }
        self.environ = {
            'HTTP_COOKIE': 'ID=1234; PREF=abc',
            'REMOTE_ADDR': '1.1.1.1, 2.2.2.2',
            'HTTP_HOST': 'proxy.net, python.org',
            'wsgi.url_scheme': 'https',
            'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest',
            'PATH_INFO': '/welcome',
            'QUERY_STRING': 'q=x&c=1',
            'REQUEST_METHOD': 'GET',
            'SCRIPT_NAME': 'my_site'
        }
        self.request = HTTPRequest(
            self.environ, 'UTF-8', options=self.options)

    def test_host(self):
        """ Ensure returns last host.
        """
        assert 'python.org' == self.request.host

    def test_remote_addr(self):
        """ Ensure returns first ip.
        """
        assert '1.1.1.1' == self.request.remote_addr

    def test_root_path(self):
        """ Ensure returns a root path of deployed application.
        """
        assert 'my_site/' == self.request.root_path

    def test_path(self):
        """ Ensure returns a full path of incoming request.
        """
        assert 'my_site/welcome' == self.request.path

    def test_query(self):
        """ Ensure returns a dict of query values.
        """
        assert {'c': ['1'], 'q': ['x']} == self.request.query

    def test_form_multipart(self):
        """ Ensure returns a dict of form values.
        """
        from wheezy.http.tests import sample
        sample.multipart(self.environ)
        assert {'name': ['test']} == self.request.form

    def test_form_urlencoded(self):
        """ Ensure returns a dict of form values.
        """
        from wheezy.http.tests import sample
        sample.urlencoded(self.environ)
        assert [('greeting', ['Hello World', 'Hallo Welt']),
                ('lang', ['en'])] == sorted(self.request.form.items())

    def test_form_json(self):
        """ Ensure returns a dict of form values.
        """
        from mock import patch
        from wheezy.http import request
        from wheezy.http.tests import sample

        patcher = patch.object(request, 'json_loads')
        mock_json_decode = patcher.start()
        mock_json_decode.return_value = {}

        sample.json(self.environ)
        assert {} == self.request.form

        patcher.stop()

    def test_form_unknown(self):
        """ Ensure returns None.
        """
        from wheezy.http.tests import sample
        sample.unknown(self.environ)
        assert not self.request.form

    def test_file(self):
        """ Ensure returns a dict of file values.
        """
        from wheezy.http.tests import sample
        sample.multipart(self.environ)

        files = self.request.files

        assert 1 == len(files)
        f = files['file'][0]
        assert 'f.txt' == f.filename

    def test_content_length_limit(self):
        """ Raises ValueError is content length is greater than
            allowed.
        """
        self.environ['CONTENT_LENGTH'] = '2048'
        self.assertRaises(ValueError, lambda: self.request.form)

    def test_cookies(self):
        """ Ensure returns a dict of cookie values.
        """
        assert {
            'PREF': 'abc',
            'ID': '1234'
        } == self.request.cookies

    def test_no_cookies(self):
        """ Returns empty dict.
        """
        del self.environ['HTTP_COOKIE']
        assert {} == self.request.cookies

    def test_ajax(self):
        """ Returns True if HTTP request is ajax request.
        """
        assert True == self.request.ajax

    def test_not_ajax(self):
        """ Returns False if HTTP request is not ajax request.
        """
        del self.environ['HTTP_X_REQUESTED_WITH']
        assert False == self.request.ajax

    def test_secure(self):
        """ secure.
        """
        assert True == self.request.secure
        assert 'https' == self.request.scheme

    def test_not_secure(self):
        """ not secure.
        """
        self.environ['wsgi.url_scheme'] = 'http'
        assert False == self.request.secure
        assert 'http' == self.request.scheme

    def test_urlparts(self):
        """ urlparts.
        """
        assert (
            'https', 'python.org', 'my_site/welcome', 'q=x&c=1', None
        ) == self.request.urlparts

    def test_content_type(self):
        """ Ensure returns content type.
        """
        from wheezy.http.tests import sample
        sample.urlencoded(self.environ)
        assert 'application/x-www-form-urlencoded' == \
            self.request.content_type

    def test_content_length(self):
        """ Ensure returns content length.
        """
        from wheezy.http.tests import sample
        sample.urlencoded(self.environ)
        assert 48 == self.request.content_length

    def test_stream(self):
        """ Ensure returns input stream.
        """
        from wheezy.http.tests import sample
        sample.urlencoded(self.environ)
        assert 48 == len(self.request.stream.read())
