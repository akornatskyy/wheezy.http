import unittest

from wheezy.http.parse import parse_cookie, parse_multipart, parse_qs
from wheezy.http.tests import sample


class ParseQSTestCase(unittest.TestCase):
    """Test the ``parse_qs``."""

    def test_parse(self):
        """Ensure query string is parsed correctly."""
        for s, e in (
            ("", {"": [""]}),
            ("&", {"": ["", ""]}),
            ("&&", {"": ["", "", ""]}),
            ("=", {"": [""]}),
            ("=a", {"": ["a"]}),
            ("a", {"a": [""]}),
            ("a=", {"a": [""]}),
            ("a=", {"a": [""]}),
            ("&a=b", {"": [""], "a": ["b"]}),
            ("a=a+b&b=b+c", {"a": ["a b"], "b": ["b c"]}),
            ("a=1&a=2", {"a": ["1", "2"]}),
            ("a+=", {"a ": [""]}),
            ("a%20=", {"a ": [""]}),
            ("a=a%20b", {"a": ["a b"]}),
            ("a=1,2,3", {"a": ["1", "2", "3"]}),
            ("a=1,2,", {"a": ["1", "2", ""]}),
            ("a=1%20,2%20,3%20", {"a": ["1 ", "2 ", "3 "]}),
            ("a=1%2C2%2C3", {"a": ["1,2,3"]}),
            ("a=1%2C2,3", {"a": ["1,2", "3"]}),
            ("a=1,2&b=3,4", {"a": ["1", "2"], "b": ["3", "4"]}),
        ):
            assert e == parse_qs(s)


class ParseMultiPartTestCase(unittest.TestCase):
    """Test the ``parse_multipart``."""

    def test_parse(self):
        """Ensure form and file data are parsed correctly."""
        environ = {}
        sample.multipart(environ)

        form, files = parse_multipart(
            environ["wsgi.input"],
            environ["CONTENT_TYPE"],
            environ["CONTENT_LENGTH"],
            "utf-8",
        )

        assert ["test"] == form["name"]
        f = files["file"][0]
        assert "file" == f.name
        assert "f.txt" == f.filename
        assert b"hello" == f.value


class ParseCookieTestCase(unittest.TestCase):
    """Test the ``parse_cookie``."""

    def test_parse(self):
        """Parses multiple well-formed cookies into a dictionary."""
        assert {"PREF": "abc", "ID": "1234"} == parse_cookie(
            "ID=1234; PREF=abc"
        )

    def test_none_cookie(self):
        """Returns empty dict when cookie header is None."""
        assert parse_cookie(None) == {}

    def test_empty_string(self):
        """Returns empty dict when cookie header is an empty string."""
        assert parse_cookie("") == {}

    def test_single_cookie(self):
        """Parses a single cookie pair correctly."""
        assert parse_cookie("a=1") == {"a": "1"}

    def test_multiple_cookies(self):
        """Parses multiple cookie pairs separated by semicolons."""
        assert parse_cookie("a=1; b=2; c=3") == {
            "a": "1",
            "b": "2",
            "c": "3",
        }

    def test_whitespace_handling(self):
        """Strips extra whitespace around names and values."""
        assert parse_cookie("  a=1  ;   b=2 ") == {
            "a": "1",
            "b": "2",
        }

    def test_value_with_equals(self):
        """Preserves '=' characters inside cookie values."""
        assert parse_cookie("token=abc=def==; a=1") == {
            "token": "abc=def==",
            "a": "1",
        }

    def test_missing_value(self):
        """Parses cookies with empty values as empty strings."""
        assert parse_cookie("a=") == {"a": ""}

    def test_missing_name(self):
        """Ignores cookie pairs with missing names."""
        assert parse_cookie("=value") == {}

    def test_malformed_pair_no_equals(self):
        """Ignores malformed cookie entries without '='."""
        assert parse_cookie("key_without_value") == {}

    def test_mixed_valid_and_malformed(self):
        """Parses valid pairs while ignoring malformed entries."""
        assert parse_cookie("a=1; malformed; b=2; =oops") == {
            "a": "1",
            "b": "2",
        }

    def test_trailing_semicolon(self):
        """Handles trailing semicolons without creating empty entries."""
        assert parse_cookie("a=1; b=2;") == {
            "a": "1",
            "b": "2",
        }

    def test_duplicate_keys_last_wins(self):
        """Uses last occurrence when duplicate cookie names are present."""
        assert parse_cookie("a=1; a=2") == {"a": "2"}
