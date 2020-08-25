""" Functional tests for ``guestbook`` applications.
"""

import unittest

from wheezy.http.functional import WSGIClient


class MainFunctionalTestCase(unittest.TestCase):
    """Functional tests for ``guestbook`` application."""

    def setUp(self):
        from guestbook import main

        self.client = WSGIClient(main)

    def tearDown(self):
        del self.client
        self.client = None

    def test_welcome(self):
        """Ensure welcome page is rendered."""
        assert 200 == self.client.get("/")
        assert "author" in self.client.content

    def test_favicon(self):
        """Resource not found."""
        assert 404 == self.client.get("/favicon.ico")

    def test_add(self):
        """Add page redirects to welcome."""
        from guestbook import greetings

        assert 200 == self.client.get("/")
        form = self.client.form
        form.author = "John"
        form.message = "Hi!"
        assert 302 == self.client.submit()
        assert 200 == self.client.follow()

        assert 1 == len(greetings)
        g = greetings[0]
        assert "John" == g.author
        assert "Hi!" == g.message
