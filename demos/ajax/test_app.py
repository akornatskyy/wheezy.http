import unittest
from io import BytesIO
from json import dumps as json_dumps

from wheezy.http.functional import WSGIClient


class WelcomeTestCase(unittest.TestCase):
    d = {"name": ["John"]}

    def setUp(self):
        from app import main

        self.client = WSGIClient(main)

    def tearDown(self):
        del self.client
        self.client = None

    def test_form_url_encoded(self):
        if has_json:
            assert 200 == self.client.ajax_post("/", params=self.d)
            assert "John" in self.client.json.message

    def test_content(self):
        if has_json:
            assert 200 == self.client.ajax_post(
                "/",
                content_type="application/json",
                content=json_dumps(self.d),
            )
            assert "John" in self.client.json.message

    def test_stream(self):
        if has_json:
            assert 200 == self.client.ajax_post(
                "/",
                content_type="application/json",
                stream=BytesIO(json_dumps(self.d).encode("utf-8")),
            )
            assert "John" in self.client.json.message

    def test_method_not_allowed(self):
        """Ensure method not allowed status code."""
        assert 405 == self.client.get("/")

    def test_not_found(self):
        """Ensure not found status code."""
        assert 404 == self.client.get("/x")


try:
    json_dumps({})
except NotImplementedError:
    has_json = False
else:
    has_json = True
