
""" Functional tests for ``guestbook`` applications.
"""

import unittest


class FunctionalTestCase(unittest.TestCase):
    """ Functional tests for ``time`` application.
    """

    def go(self, path, expected_status='200 OK', method='GET'):
        """ Make a call to ``main`` function setting
            wsgi ``environ['PATH_INFO']`` to ``path``
            and validating expected http response
            status.
        """
        from guestbook import main

        def start_response(status, response_headers):
            assert expected_status == status

        if '?' in path:
            path, qs = path.split('?')
        else:
            qs = ''
        environ = {
                'REQUEST_METHOD': method,
                'PATH_INFO': path,
                'SCRIPT_NAME': '',
                'QUERY_STRING': qs,
                'HTTP_HOST': 'localhost:8080'
        }
        return ''.join(map(lambda chunk: chunk.decode('utf-8'),
            main(environ, start_response)))


class MainFunctionalTestCase(FunctionalTestCase):
    """ Functional tests for ``guestbook`` application.
    """

    def test_welcome(self):
        """ Ensure welcome page is rendered.
        """
        response = self.go('/')

        assert 'author' in response

    def test_favicon(self):
        """ Resource not found.
        """
        self.go('/favicon.ico', '404 Not Found')

    def test_add(self):
        """ Add page redirects to welcome.
        """
        from guestbook import greetings

        self.go('/add?author=a&message=m', '302 Found')

        assert 1 == len(greetings)
        g = greetings[0]
        assert 'a' == g.author
        assert 'm' == g.message
