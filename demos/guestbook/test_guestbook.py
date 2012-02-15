
""" Functional tests for ``guestbook`` applications.
"""

import unittest

from wheezy.http.functional import WSGIClient


class FunctionalTestCase(unittest.TestCase):
    """ Functional tests for ``time`` application.
    """

    def get(self, path, expected_status=200):
        """ Make a call to ``main`` function setting
            wsgi ``environ['PATH_INFO']`` to ``path``
            and validating expected http response
            status.
        """
        from guestbook import main

        client = WSGIClient(main)
        assert expected_status == client.get(path)
        return client.content


class MainFunctionalTestCase(FunctionalTestCase):
    """ Functional tests for ``guestbook`` application.
    """

    def test_welcome(self):
        """ Ensure welcome page is rendered.
        """
        response = self.get('/')

        assert 'author' in response

    def test_favicon(self):
        """ Resource not found.
        """
        self.get('/favicon.ico', 404)

    def test_add(self):
        """ Add page redirects to welcome.
        """
        from guestbook import greetings

        self.get('/add?author=a&message=m', 302)

        assert 1 == len(greetings)
        g = greetings[0]
        assert 'a' == g.author
        assert 'm' == g.message
