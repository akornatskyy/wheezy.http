import re
import unittest
from datetime import datetime, timedelta, timezone

from wheezy.core.datetime import parse_http_datetime

from wheezy.http.config import bootstrap_http_defaults
from wheezy.http.cookie import HTTPCookie

UTC = timezone.utc


class HTTPCookieTestCase(unittest.TestCase):
    """Test the ``HTTPCookie``."""

    def setUp(self):
        self.options = options = {}
        bootstrap_http_defaults(options)

    def test_default_init(self):
        """Check Set-Cookie HTTP header with defaults."""
        cookie = HTTPCookie("x", options=self.options)
        header = cookie.http_set_cookie("UTF-8")[1]
        assert "x=; path=/" == header

    def test_value(self):
        """Check value option."""
        cookie = HTTPCookie("x", value="1", options=self.options)
        header = cookie.http_set_cookie("UTF-8")[1]
        assert "x=1; path=/" == header

    def test_path(self):
        """Check path option."""
        cookie = HTTPCookie("x", path="/welcome", options=self.options)
        header = cookie.http_set_cookie("UTF-8")[1]
        assert "x=; path=/welcome" == header

    def test_max_age(self):
        """Check max_age option."""
        cookie = HTTPCookie("x", max_age=100, options=self.options)
        header = cookie.http_set_cookie("UTF-8")[1]
        http_expires = re.match(r"x=; expires=(.*); path=/", header).group(1)
        expires = parse_http_datetime(http_expires).replace(tzinfo=UTC)
        assert expires > datetime.now(UTC) - timedelta(seconds=1)
        assert expires < datetime.now(UTC) + timedelta(seconds=100)

    def test_domain_from_options(self):
        """Check domain from options."""
        options = self.options
        options["HTTP_COOKIE_DOMAIN"] = ".python.org"
        cookie = HTTPCookie("x", options=options)
        header = cookie.http_set_cookie("UTF-8")[1]
        assert "x=; domain=.python.org; path=/" == header

    def test_domain(self):
        """Check domain option."""
        cookie = HTTPCookie("x", domain=".python.org", options=self.options)
        header = cookie.http_set_cookie("UTF-8")[1]
        assert "x=; domain=.python.org; path=/" == header

    def test_samesite_from_options(self):
        """Check samesite from options."""
        options = self.options
        options["HTTP_COOKIE_SAMESITE"] = "strict"
        cookie = HTTPCookie("x", options=options)
        header = cookie.http_set_cookie("UTF-8")[1]
        assert "x=; path=/; samesite=strict" == header

    def test_samesite(self):
        """Check samesite option."""
        cookie = HTTPCookie("x", samesite="lax", options=self.options)
        header = cookie.http_set_cookie("UTF-8")[1]
        assert "x=; path=/; samesite=lax" == header

    def test_secure_from_options(self):
        """Check secure from options."""
        options = self.options
        options["HTTP_COOKIE_SECURE"] = True
        cookie = HTTPCookie("x", options=options)
        header = cookie.http_set_cookie("UTF-8")[1]
        assert "x=; path=/; secure" == header

    def test_secure(self):
        """Check secure option."""
        cookie = HTTPCookie("x", secure=True, options=self.options)
        header = cookie.http_set_cookie("UTF-8")[1]
        assert "x=; path=/; secure" == header

    def test_httponly_from_options(self):
        """Check httponly from options."""
        options = self.options
        options["HTTP_COOKIE_HTTPONLY"] = True
        cookie = HTTPCookie("x", options=options)
        header = cookie.http_set_cookie("UTF-8")[1]
        assert "x=; path=/; httponly" == header

    def test_httponly(self):
        """Check httponly option."""
        cookie = HTTPCookie("x", httponly=True, options=self.options)
        header = cookie.http_set_cookie("UTF-8")[1]
        assert "x=; path=/; httponly" == header

    def test_delete(self):
        """Check delete method."""
        cookie = HTTPCookie.delete("x", options=self.options)
        header = cookie.http_set_cookie("UTF-8")[1]
        assert "x=; expires=Sat, 01 Jan 2000 00:00:01 GMT; path=/" == header

    def test_delete_by_path(self):
        """Check delete method by passing path."""
        cookie = HTTPCookie.delete("x", path="/a", options=self.options)
        header = cookie.http_set_cookie("UTF-8")[1]
        assert "x=; expires=Sat, 01 Jan 2000 00:00:01 GMT; path=/a" == header

    def test_delete_by_domain(self):
        """Check delete method by passing domain."""
        cookie = HTTPCookie.delete(
            "x", domain=".python.org", options=self.options
        )
        header = cookie.http_set_cookie("UTF-8")[1]
        assert (
            "x=; domain=.python.org; "
            "expires=Sat, 01 Jan 2000 00:00:01 GMT; path=/" == header
        )

    def test_delete_by_domain_from_options(self):
        """Check delete method by passing domain."""
        options = self.options
        options["HTTP_COOKIE_DOMAIN"] = ".python.org"
        cookie = HTTPCookie.delete("x", options=options)
        header = cookie.http_set_cookie("UTF-8")[1]
        assert (
            "x=; domain=.python.org; "
            "expires=Sat, 01 Jan 2000 00:00:01 GMT; path=/" == header
        )
