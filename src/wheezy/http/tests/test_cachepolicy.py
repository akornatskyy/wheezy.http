""" Unit tests for ``wheezy.http.cachepolicy``.
"""

import unittest


class SupportedCacheabilityTestCase(unittest.TestCase):
    """Test the ``SUPPORTED``."""

    def test_supported_cacheability(self):
        """Ensure valid supported cacheability options."""
        from wheezy.http.cachepolicy import SUPPORTED

        assert "no-cache" in SUPPORTED
        assert "private" in SUPPORTED
        assert "public" in SUPPORTED
        assert 3 == len(SUPPORTED)

    def test_not_supported(self):
        """Raise ``AssertionError`` in cache policy is not supported."""
        from wheezy.http.cachepolicy import HTTPCachePolicy

        self.assertRaises(AssertionError, lambda: HTTPCachePolicy("x"))


class NoCachePolicyTestCase(unittest.TestCase):
    """Test the ``HTTPCachePolicy`` initialized with no-cache
    cacheability.
    """

    def setUp(self):
        from wheezy.http.cachepolicy import HTTPCachePolicy

        self.policy = HTTPCachePolicy("no-cache")

    def test_init(self):
        """Check default values for no-cache cacheability."""
        assert self.policy.is_no_cache
        assert not self.policy.is_public
        assert "no-cache" == self.policy.http_pragma
        assert "-1" == self.policy.http_expires

    def test_fail_no_cache(self):
        """Raise ``AssertionError``."""
        self.assertRaises(
            AssertionError, lambda: self.policy.fail_no_cache("x")
        )

    def test_assert_public(self):
        """Raise ``AssertionError``."""
        self.assertRaises(
            AssertionError, lambda: self.policy.assert_public("x")
        )


class PrivatePolicyTestCase(unittest.TestCase):
    """Test the ``HTTPCachePolicy`` initialized with private
    cacheability.
    """

    def setUp(self):
        from wheezy.http.cachepolicy import HTTPCachePolicy

        self.policy = HTTPCachePolicy("private")

    def test_init(self):
        """Check default values for no-cache cacheability."""
        assert not self.policy.is_no_cache
        assert not self.policy.is_public
        assert self.policy.http_pragma is None
        assert self.policy.http_expires is None

    def test_fail_no_cache(self):
        """``AssertionError`` not raised."""
        self.policy.fail_no_cache("x")

    def test_assert_public(self):
        """Raise ``AssertionError``."""
        self.assertRaises(
            AssertionError, lambda: self.policy.assert_public("x")
        )


class PublicPolicyTestCase(unittest.TestCase):
    """Test the ``HTTPCachePolicy`` initialized with public
    cacheability.
    """

    def setUp(self):
        from wheezy.http.cachepolicy import HTTPCachePolicy

        self.policy = HTTPCachePolicy("public")

    def test_init(self):
        """Check default values for no-cache cacheability."""
        assert not self.policy.is_no_cache
        assert self.policy.is_public
        assert self.policy.http_pragma is None
        assert self.policy.http_expires is None

    def test_fail_no_cache(self):
        """``AssertionError`` not raised."""
        self.policy.fail_no_cache("x")

    def test_assert_public(self):
        """Raise ``AssertionError``."""
        self.policy.assert_public("x")


class HTTPCacheControlTestCase(unittest.TestCase):
    """Test the ``HTTPCachePolicy.http_cache_control``."""

    def test_default(self):
        """Check default."""
        from wheezy.http.cachepolicy import SUPPORTED, HTTPCachePolicy

        for cacheability in SUPPORTED:
            policy = HTTPCachePolicy(cacheability)
            header = policy.http_cache_control()[1]
            assert cacheability == header

    def test_private(self):
        """private fields."""
        from wheezy.http.cachepolicy import HTTPCachePolicy

        for cacheability in ["public"]:
            policy = HTTPCachePolicy(cacheability)
            policy.private("a", "b")
            header = policy.http_cache_control()[1]
            assert 'public, private="a, b"' == header
        for cacheability in ["no-cache", "private"]:
            policy = HTTPCachePolicy(cacheability)
            self.assertRaises(AssertionError, lambda: policy.private("a", "b"))

    def test_no_cache(self):
        """no-cache fields."""
        from wheezy.http.cachepolicy import HTTPCachePolicy

        for cacheability in ["private", "public"]:
            policy = HTTPCachePolicy(cacheability)
            policy.no_cache("a", "b")
            header = policy.http_cache_control()[1]
            assert 'no-cache="a, b"' in header
        for cacheability in ["no-cache"]:
            policy = HTTPCachePolicy(cacheability)
            self.assertRaises(AssertionError, lambda: policy.private("a", "b"))

    def test_no_store(self):
        """no-store."""
        from wheezy.http.cachepolicy import SUPPORTED, HTTPCachePolicy

        for cacheability in SUPPORTED:
            policy = HTTPCachePolicy(cacheability)
            policy.no_store()
            header = policy.http_cache_control()[1]
            assert "no-store" in header

    def test_must_revalidate(self):
        """must-revalidate."""
        from wheezy.http.cachepolicy import SUPPORTED, HTTPCachePolicy

        for cacheability in SUPPORTED:
            policy = HTTPCachePolicy(cacheability)
            policy.must_revalidate()
            header = policy.http_cache_control()[1]
            assert "must-revalidate" in header

    def test_must_revalidate_fails(self):
        """must-revalidate fails if proxy-revalidate has been
        set already.
        """
        from wheezy.http.cachepolicy import SUPPORTED, HTTPCachePolicy

        for cacheability in SUPPORTED:
            policy = HTTPCachePolicy(cacheability)
            policy.proxy_revalidate()
            self.assertRaises(AssertionError, lambda: policy.must_revalidate())

    def test_proxy_revalidate(self):
        """proxy-revalidate."""
        from wheezy.http.cachepolicy import SUPPORTED, HTTPCachePolicy

        for cacheability in SUPPORTED:
            policy = HTTPCachePolicy(cacheability)
            policy.proxy_revalidate()
            header = policy.http_cache_control()[1]
            assert "proxy-revalidate" in header

    def test_proxy_revalidate_fails(self):
        """proxy-revalidate fails if must-revalidate has been
        set already.
        """
        from wheezy.http.cachepolicy import SUPPORTED, HTTPCachePolicy

        for cacheability in SUPPORTED:
            policy = HTTPCachePolicy(cacheability)
            policy.must_revalidate()
            self.assertRaises(
                AssertionError, lambda: policy.proxy_revalidate()
            )

    def test_no_transform(self):
        """no-transform."""
        from wheezy.http.cachepolicy import SUPPORTED, HTTPCachePolicy

        for cacheability in SUPPORTED:
            policy = HTTPCachePolicy(cacheability)
            policy.no_transform()
            header = policy.http_cache_control()[1]
            assert "no-transform" in header

    def test_append_extension(self):
        """extensions."""
        from wheezy.http.cachepolicy import SUPPORTED, HTTPCachePolicy

        for cacheability in SUPPORTED:
            policy = HTTPCachePolicy(cacheability)
            policy.append_extension("x1")
            policy.append_extension("x2")
            header = policy.http_cache_control()[1]
            assert "x1, x2" in header

    def test_max_age(self):
        """max-age."""
        from wheezy.http.cachepolicy import HTTPCachePolicy

        for cacheability in ["private", "public"]:
            policy = HTTPCachePolicy(cacheability)
            policy.max_age(100)
            header = policy.http_cache_control()[1]
            assert " max-age=100" in header
        for cacheability in ["no-cache"]:
            policy = HTTPCachePolicy(cacheability)
            self.assertRaises(AssertionError, lambda: policy.max_age(100))

    def test_smax_age(self):
        """smax-age."""
        from wheezy.http.cachepolicy import HTTPCachePolicy

        for cacheability in ["private", "public"]:
            policy = HTTPCachePolicy(cacheability)
            policy.smax_age(100)
            header = policy.http_cache_control()[1]
            assert " smax-age=100" in header
        for cacheability in ["no-cache"]:
            policy = HTTPCachePolicy(cacheability)
            self.assertRaises(AssertionError, lambda: policy.smax_age(100))


class HTTPCachePolicyExtendHeadersTestCase(unittest.TestCase):
    """Test the ``HTTPCachePolicy.extend``."""

    def test_no_cache_headers(self):
        """Pragma and Expires headers in no-cache."""
        from wheezy.http.cachepolicy import HTTPCachePolicy

        policy = HTTPCachePolicy("no-cache")
        headers = []
        policy.extend(headers)
        assert [
            ("Cache-Control", "no-cache"),
            ("Pragma", "no-cache"),
            ("Expires", "-1"),
        ] == headers

    def test_expires(self):
        """expires."""
        from datetime import datetime

        from wheezy.core.datetime import UTC
        from wheezy.http.cachepolicy import HTTPCachePolicy

        when = datetime(2012, 4, 13, 14, 57, tzinfo=UTC)
        for cacheability in ["private", "public"]:
            policy = HTTPCachePolicy(cacheability)
            policy.expires(when)
            headers = []
            policy.extend(headers)
            assert [
                ("Cache-Control", cacheability),
                ("Expires", "Fri, 13 Apr 2012 14:57:00 GMT"),
            ] == headers
        for cacheability in ["no-cache"]:
            policy = HTTPCachePolicy(cacheability)
            self.assertRaises(AssertionError, lambda: policy.expires(when))

    def test_last_modified(self):
        """last_modified."""
        from datetime import datetime

        from wheezy.core.datetime import UTC
        from wheezy.http.cachepolicy import HTTPCachePolicy

        when = datetime(2012, 4, 13, 15, 2, tzinfo=UTC)
        for cacheability in ["private", "public"]:
            policy = HTTPCachePolicy(cacheability)
            policy.last_modified(when)
            headers = []
            policy.extend(headers)
            assert [
                ("Cache-Control", cacheability),
                ("Last-Modified", "Fri, 13 Apr 2012 15:02:00 GMT"),
            ] == headers
        for cacheability in ["no-cache"]:
            policy = HTTPCachePolicy(cacheability)
            self.assertRaises(
                AssertionError, lambda: policy.last_modified(when)
            )

    def test_etag(self):
        """etag."""
        from wheezy.http.cachepolicy import HTTPCachePolicy

        tag = '"3d8b39ae74"'
        for cacheability in ["public", "private"]:
            policy = HTTPCachePolicy(cacheability)
            policy.etag(tag)
            headers = []
            policy.extend(headers)
            assert [("Cache-Control", cacheability), ("ETag", tag)] == headers
        policy = HTTPCachePolicy("no-cache")
        self.assertRaises(AssertionError, lambda: policy.etag(tag))

    def test_vary_star(self):
        """vary *."""
        from wheezy.http.cachepolicy import HTTPCachePolicy

        for cacheability in ["public", "private"]:
            policy = HTTPCachePolicy(cacheability)
            policy.vary()
            headers = []
            policy.extend(headers)
            assert [("Cache-Control", cacheability), ("Vary", "*")] == headers
        for cacheability in ["no-cache"]:
            policy = HTTPCachePolicy(cacheability)
            self.assertRaises(AssertionError, lambda: policy.vary())

    def test_vary_header(self):
        """vary by specific headers."""
        from wheezy.http.cachepolicy import HTTPCachePolicy

        for cacheability in ["public", "private"]:
            policy = HTTPCachePolicy(cacheability)
            policy.vary("Accept-Encoding", "Accept-Language")
            headers = []
            policy.extend(headers)
            assert [
                ("Cache-Control", cacheability),
                ("Vary", "Accept-Encoding, Accept-Language"),
            ] == headers
        for cacheability in ["no-cache"]:
            policy = HTTPCachePolicy(cacheability)
            self.assertRaises(AssertionError, lambda: policy.vary())
