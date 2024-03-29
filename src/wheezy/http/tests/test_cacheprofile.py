""" Unit tests for ``wheezy.http.cacheprofile``.
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from wheezy.core.datetime import parse_http_datetime

from wheezy.http.cacheprofile import (  # isort:skip
    CACHEABILITY,
    CacheProfile,
    RequestVary,
    SUPPORTED,
)


class SupportedCacheabilityTestCase(unittest.TestCase):
    """Test the ``SUPPORTED``."""

    def test_supported_cacheability(self):
        """Ensure valid supported cacheability options."""
        assert "none" in SUPPORTED
        assert "server" in SUPPORTED
        assert "client" in SUPPORTED
        assert "both" in SUPPORTED
        assert "public" in SUPPORTED
        assert 5 == len(SUPPORTED)

    def test_mapping_between_profile_and_policy(self):
        """Ensure mapping between cache profile and
        HTTP cache policy is valid.
        """
        from wheezy.http.cachepolicy import SUPPORTED

        assert set(SUPPORTED) == set(CACHEABILITY.values())

    def test_not_supported(self):
        """Raise ``ValueError`` in cache policy is not supported."""
        self.assertRaises(AssertionError, lambda: CacheProfile("x"))


class CacheProfileTestCase(unittest.TestCase):
    """Test the ``CacheProfile`` class."""

    def test_not_enabled(self):
        """cache profile not enabled."""
        profile = CacheProfile("none", enabled=False)

        assert not profile.enabled
        assert profile.cache_policy() is None

    def test_location_none(self):
        """none cache profile."""
        profile = CacheProfile("none")

        assert not profile.request_vary
        policy = profile.cache_policy()
        headers = []
        policy.extend(headers)
        assert [
            ("Cache-Control", "no-cache"),
            ("Pragma", "no-cache"),
            ("Expires", "-1"),
        ] == headers

    def test_location_server(self):
        """server cache profile."""
        profile = CacheProfile("server", duration=100)

        assert profile.request_vary
        policy = profile.cache_policy()
        headers = []
        policy.extend(headers)
        assert [
            ("Cache-Control", "no-cache"),
            ("Pragma", "no-cache"),
            ("Expires", "-1"),
        ] == headers

    @patch(
        "wheezy.http.cacheprofile.RequestVary.__init__",
        Mock(return_value=None),
    )
    def test_request_vary(self):
        """request vary initialization."""
        vary_query = ["q1", "q2"]
        vary_form = ["f1", "f2"]
        vary_cookies = ["c1", "c2"]
        vary_environ = ["e1", "e2"]
        profile = CacheProfile(
            "server",
            duration=100,
            vary_query=vary_query,
            vary_form=vary_form,
            vary_cookies=vary_cookies,
            vary_environ=vary_environ,
        )

        request_vary = profile.request_vary
        request_vary.__init__.assert_called_once_with(
            query=vary_query,
            form=vary_form,
            cookies=vary_cookies,
            environ=vary_environ,
        )

    def test_location_client(self):
        """client cache profile."""
        profile = CacheProfile("client", duration=100)

        assert not profile.request_vary
        policy = profile.cache_policy()
        assert "private" == policy.cacheability
        assert 100 == policy.max_age_delta
        now = parse_http_datetime(policy.http_last_modified)
        assert now < datetime.utcnow()
        expires = now + timedelta(seconds=profile.duration)
        assert expires == parse_http_datetime(policy.http_expires)
        headers = []
        policy.extend(headers)
        assert [
            ("Cache-Control", "private, max-age=100"),
            ("Expires", policy.http_expires),
            ("Last-Modified", policy.http_last_modified),
        ] == headers

    def test_location_both(self):
        """both cache profile."""
        profile = CacheProfile("both", duration=100, http_vary=["Cookie"])

        assert profile.request_vary
        policy = profile.cache_policy()
        assert "private" == policy.cacheability
        assert 100 == policy.max_age_delta
        now = parse_http_datetime(policy.http_last_modified)
        assert now < datetime.utcnow()
        expires = now + timedelta(seconds=profile.duration)
        assert expires == parse_http_datetime(policy.http_expires)
        headers = []
        policy.extend(headers)
        assert [
            ("Cache-Control", "private, max-age=100"),
            ("Expires", policy.http_expires),
            ("Last-Modified", policy.http_last_modified),
            ("Vary", "Cookie"),
        ] == headers

    def test_location_public(self):
        """public cache profile."""
        profile = CacheProfile("public", duration=100)

        assert profile.request_vary
        policy = profile.cache_policy()
        assert "public" == policy.cacheability
        assert 100 == policy.max_age_delta
        now = parse_http_datetime(policy.http_last_modified)
        assert now < datetime.utcnow()
        expires = now + timedelta(seconds=profile.duration)
        assert expires == parse_http_datetime(policy.http_expires)
        headers = []
        policy.extend(headers)
        assert [
            ("Cache-Control", "public, max-age=100"),
            ("Expires", policy.http_expires),
            ("Last-Modified", policy.http_last_modified),
        ] == headers

    def test_no_store(self):
        """no_store."""
        for location in ["none", "server"]:
            profile = CacheProfile(location, no_store=True, duration=100)
            policy = profile.cache_policy()
            headers = []
            policy.extend(headers)
            assert [
                ("Cache-Control", "no-cache, no-store"),
                ("Pragma", "no-cache"),
                ("Expires", "-1"),
            ] == headers

        for location in ["client", "both"]:
            profile = CacheProfile(
                location, no_store=True, duration=100, http_max_age=60
            )
            policy = profile.cache_policy()
            headers = []
            policy.extend(headers)
            assert [
                ("Cache-Control", "private, no-store, max-age=60"),
                ("Expires", policy.http_expires),
                ("Last-Modified", policy.http_last_modified),
            ] == headers

        for location in ["public"]:
            profile = CacheProfile(
                location, no_store=True, duration=100, http_max_age=0
            )
            policy = profile.cache_policy()
            headers = []
            policy.extend(headers)
            assert [
                ("Cache-Control", "public, no-store, max-age=0"),
                ("Expires", policy.http_expires),
                ("Last-Modified", policy.http_last_modified),
            ] == headers

    def test_invalid_duration(self):
        """check invalid duration."""
        for location in ["server", "client", "both", "public"]:
            self.assertRaises(
                ValueError,
                lambda location=location: CacheProfile(location, duration=0),
            )

    def test_http_max_age(self):
        """check http max age."""
        for location in ["server", "client", "both", "public"]:
            p = CacheProfile(location, duration=10)
            assert 10 == p.http_max_age
            p = CacheProfile(location, duration=10, http_max_age=20)
            assert 20 == p.http_max_age
            p = CacheProfile(location, duration=10, http_max_age=0)
            assert 0 == p.http_max_age

        for location in ["client", "both", "public"]:
            p = CacheProfile(location, duration=10)
            policy = p.client_policy()
            assert policy
            assert isinstance(policy.modified, datetime)
            assert 10 == policy.max_age_delta
            p = CacheProfile(location, duration=10, http_max_age=0)
            policy = p.cache_policy()
            assert policy
            assert isinstance(policy.modified, datetime)
            assert policy.http_last_modified == policy.http_expires
            assert 0 == policy.max_age_delta


class RequestVaryTestCase(unittest.TestCase):
    """Test the ``RequestVary`` class."""

    def test_init_default_vary(self):
        """Default vary strategy is request_key."""
        request_vary = RequestVary()

        assert request_vary.request_key == request_vary.key

    def test_init_vary_parts(self):
        """Ensure each vary part (query, form, etc) is added to the
        vary part strategy.
        """
        query = ["q1", "q3", "q2"]
        form = ["f1", "f3", "f2"]
        cookies = ["c1", "c3", "c2"]
        environ = ["e1", "e3", "e2"]
        request_vary = RequestVary(
            query=query, form=form, cookies=cookies, environ=environ
        )

        assert 5 == len(request_vary.vary_parts)
        assert request_vary.request_key == request_vary.vary_parts[0]
        assert request_vary.key_query == request_vary.vary_parts[1]
        assert ("q1", "q2", "q3") == request_vary.query
        assert request_vary.key_form == request_vary.vary_parts[2]
        assert ("f1", "f2", "f3") == request_vary.form
        assert request_vary.key_cookies == request_vary.vary_parts[3]
        assert ("c1", "c2", "c3") == request_vary.cookies
        assert request_vary.key_environ == request_vary.vary_parts[4]
        assert ("e1", "e2", "e3") == request_vary.environ

    def test_key_default_vary(self):
        """Check key for default vary strategy."""
        request_vary = RequestVary()

        mock_request = Mock()
        mock_request.method = "GET"
        mock_request.environ = {"PATH_INFO": "/welcome"}
        assert "G/welcome" == request_vary.key(mock_request)

    def test_key_vary_parts(self):
        """Check key for vary part strategy."""
        query = ["q1", "q3", "q2"]
        form = ["f1", "f3", "f2"]
        cookies = ["c1", "c3", "c2"]
        environ = ["e1", "e3", "e2"]
        request_vary = RequestVary(
            query=query, form=form, cookies=cookies, environ=environ
        )

        mock_request = Mock()
        mock_request.method = "GET"
        mock_request.environ = {"PATH_INFO": "/welcome"}
        mock_request.query = {"q1": ["1"]}
        mock_request.form = {"f2": ["2"]}
        mock_request.cookies = {"c3": "3"}

        key = request_vary.key(mock_request)

        assert "G/welcomeQN1XXFXN2XCXXN3EXXX" == key
