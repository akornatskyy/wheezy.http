
""" Functional tests for ``guestbook`` applications.
"""

import unittest


class FunctionalTestCase(unittest.TestCase):
    """ Functional tests for ``time`` application.
    """

    def go(self, path, expected_status='200 OK', method='POST'):
        """ Make a call to ``main`` function setting
            wsgi ``environ['PATH_INFO']`` to ``path``
            and validating expected http response
            status.
        """
        from guestbook import main

        def start_response(status, response_headers):
            assert expected_status == status

        environ = {
                'PATH_INFO': path,
                'REQUEST_METHOD': method
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
        self.go('/favicon.ico', '404 NotFound')

    def test_add(self):
        """ Add page redirects to welcome.
        """
        self.go('/add?author&message', '403 Found')

    def test_add_with_post(self):
        """ Add page redirects to welcome.
        """
        self.go('/add?author&message', '403 Found', method='POST')
