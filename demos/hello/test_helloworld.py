""" Functional tests for ``helloworld`` applications.
"""

import unittest

from wheezy.http.functional import WSGIClient


class HelloWorldTestCase(unittest.TestCase):
    def setUp(self):
        from helloworld import main

        self.client = WSGIClient(main)

    def tearDown(self):
        del self.client
        self.client = None

    def test_welcome(self):
        """Ensure welcome page is rendered."""
        assert 200 == self.client.get("/")
        assert "Hello" in self.client.content

    def test_not_found(self):
        """Ensure not found status code."""
        assert 404 == self.client.get("/x")
