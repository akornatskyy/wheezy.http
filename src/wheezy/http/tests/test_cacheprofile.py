
""" Unit tests for ``wheezy.http.cacheprofile``.
"""

import unittest

from mock import Mock
from mock import patch


class SupportedCacheabilityTestCase(unittest.TestCase):
    """ Test the ``SUPPORTED``.
    """

    def test_supported_cacheability(self):
        """ Ensure valid supported cacheability options.
        """
        from wheezy.http.cacheprofile import SUPPORTED

        assert 'none' in SUPPORTED
        assert 'server' in SUPPORTED
        assert 'client' in SUPPORTED
        assert 'both' in SUPPORTED
        assert 'public' in SUPPORTED
        assert 5 == len(SUPPORTED)

    def test_mapping_between_profile_and_policy(self):
        """ Ensure mapping between cache profile and
            HTTP cache policy is valid.
        """
        from wheezy.http.cachepolicy import SUPPORTED
        from wheezy.http.cacheprofile import CACHEABILITY

        assert set(SUPPORTED) == set(CACHEABILITY.values())

    def test_not_supported(self):
        """ Raise ``ValueError`` in cache policy is not supported.
        """
        from wheezy.http.cacheprofile import CacheProfile
        self.assertRaises(AssertionError, lambda: CacheProfile('x'))


class CacheProfileTestCase(unittest.TestCase):
    """ Test the ``CacheProfile`` class.
    """

    def test_not_enabled(self):
        """ cache profile not enabled.
        """
        from wheezy.http.cacheprofile import CacheProfile

        profile = CacheProfile('none', enabled=False)

        assert not profile.enabled
        assert None == profile.cache_policy()

    def test_location_none(self):
        """ none cache profile.
        """
        from wheezy.http.cacheprofile import CacheProfile

        profile = CacheProfile('none')

        assert not profile.request_vary
        policy = profile.cache_policy()
        headers = []
        policy.extend(headers)
        assert [('Cache-Control', 'no-cache'),
                ('Pragma', 'no-cache'),
                ('Expires', '-1')] == headers

    def test_location_server(self):
        """ server cache profile.
        """
        from wheezy.http.cacheprofile import CacheProfile

        profile = CacheProfile('server', duration=100)

        assert profile.request_vary
        policy = profile.cache_policy()
        headers = []
        policy.extend(headers)
        assert [('Cache-Control', 'no-cache'),
                ('Pragma', 'no-cache'),
                ('Expires', '-1')] == headers

    @patch('wheezy.http.cacheprofile.RequestVary.__init__',
            Mock(return_value=None))
    def test_request_vary(self):
        """ request vary initialization.
        """
        from wheezy.http.cacheprofile import CacheProfile

        vary_query = ['q1', 'q2']
        vary_form = ['f1', 'f2']
        vary_cookies = ['c1', 'c2']
        vary_environ = ['e1', 'e2']
        profile = CacheProfile('server', duration=100,
                vary_query=vary_query,
                vary_form=vary_form,
                vary_cookies=vary_cookies,
                vary_environ=vary_environ)

        request_vary = profile.request_vary
        request_vary.__init__.assert_called_once_with(
                query=vary_query,
                form=vary_form,
                cookies=vary_cookies,
                environ=vary_environ)

    def test_location_client(self):
        """ client cache profile.
        """
        from datetime import datetime
        from datetime import timedelta
        from wheezy.core.datetime import parse_http_datetime
        from wheezy.http.cacheprofile import CacheProfile

        profile = CacheProfile('client', duration=100)

        assert not profile.request_vary
        policy = profile.cache_policy()
        assert 'private' == policy.cacheability
        assert 100 == policy.max_age_delta
        now = parse_http_datetime(policy.http_last_modified)
        assert now < datetime.utcnow()
        expires = now + timedelta(seconds=profile.duration)
        assert expires == parse_http_datetime(policy.http_expires)
        headers = []
        policy.extend(headers)
        assert [('Cache-Control', 'private, max-age=100'),
                ('Expires', policy.http_expires),
                ('Last-Modified', policy.http_last_modified)] == headers

    def test_location_both(self):
        """ both cache profile.
        """
        from datetime import datetime
        from datetime import timedelta
        from wheezy.core.datetime import parse_http_datetime
        from wheezy.http.cacheprofile import CacheProfile

        profile = CacheProfile('both', duration=100)

        assert profile.request_vary
        policy = profile.cache_policy()
        assert 'private' == policy.cacheability
        assert 100 == policy.max_age_delta
        now = parse_http_datetime(policy.http_last_modified)
        assert now < datetime.utcnow()
        expires = now + timedelta(seconds=profile.duration)
        assert expires == parse_http_datetime(policy.http_expires)
        headers = []
        policy.extend(headers)
        assert [('Cache-Control', 'private, max-age=100'),
                ('Expires', policy.http_expires),
                ('Last-Modified', policy.http_last_modified)] == headers

    def test_location_public(self):
        """ public cache profile.
        """
        from datetime import datetime
        from datetime import timedelta
        from wheezy.core.datetime import parse_http_datetime
        from wheezy.http.cacheprofile import CacheProfile

        profile = CacheProfile('public', duration=100)

        assert profile.request_vary
        policy = profile.cache_policy()
        assert 'public' == policy.cacheability
        assert 100 == policy.max_age_delta
        now = parse_http_datetime(policy.http_last_modified)
        assert now < datetime.utcnow()
        expires = now + timedelta(seconds=profile.duration)
        assert expires == parse_http_datetime(policy.http_expires)
        headers = []
        policy.extend(headers)
        assert [('Cache-Control', 'public, max-age=100'),
                ('Expires', policy.http_expires),
                ('Last-Modified', policy.http_last_modified)] == headers

    def test_no_store(self):
        """ no_store.
        """
        from wheezy.http.cacheprofile import CacheProfile

        for location in ['none', 'server']:
            profile = CacheProfile(location, no_store=True, duration=100)
            policy = profile.cache_policy()
            headers = []
            policy.extend(headers)
            assert [('Cache-Control', 'no-cache, no-store'),
                    ('Pragma', 'no-cache'),
                    ('Expires', '-1')] == headers

        for location in ['client', 'both']:
            profile = CacheProfile(location, no_store=True, duration=100)
            policy = profile.cache_policy()
            headers = []
            policy.extend(headers)
            assert [('Cache-Control', 'private, no-store, max-age=100'),
                    ('Expires', policy.http_expires),
                    ('Last-Modified', policy.http_last_modified)] == headers

        for location in ['public']:
            profile = CacheProfile(location, no_store=True, duration=100)
            policy = profile.cache_policy()
            headers = []
            policy.extend(headers)
            assert [('Cache-Control', 'public, no-store, max-age=100'),
                    ('Expires', policy.http_expires),
                    ('Last-Modified', policy.http_last_modified)] == headers

    def test_invalid_duration(self):
        """ check invalid duration.
        """
        from wheezy.http.cacheprofile import CacheProfile

        for location in ['server', 'client', 'both', 'public']:
            self.assertRaises(ValueError, lambda:
                    CacheProfile(location, duration=0))


class RequestVaryTestCase(unittest.TestCase):
    """ Test the ``RequestVary`` class.
    """

    def test_init_default_vary(self):
        """ Default vary strategy is request_key.
        """
        from wheezy.http.cacheprofile import RequestVary
        request_vary = RequestVary()

        assert request_vary.request_key == request_vary.key

    def test_init_vary_parts(self):
        """ Ensure each vary part (query, form, etc) is added to the
            vary part strategy.
        """
        from wheezy.http.cacheprofile import RequestVary
        query = ['q1', 'q3', 'q2']
        form = ['f1', 'f3', 'f2']
        cookies = ['c1', 'c3', 'c2']
        environ = ['e1', 'e3', 'e2']
        request_vary = RequestVary(
                query=query,
                form=form,
                cookies=cookies,
                environ=environ)

        assert 5 == len(request_vary.vary_parts)
        assert request_vary.request_key == request_vary.vary_parts[0]
        assert request_vary.key_query == request_vary.vary_parts[1]
        assert ('q1', 'q2', 'q3') == request_vary.query
        assert request_vary.key_form == request_vary.vary_parts[2]
        assert ('f1', 'f2', 'f3') == request_vary.form
        assert request_vary.key_cookies == request_vary.vary_parts[3]
        assert ('c1', 'c2', 'c3') == request_vary.cookies
        assert request_vary.key_environ == request_vary.vary_parts[4]
        assert ('e1', 'e2', 'e3') == request_vary.environ

    def test_key_default_vary(self):
        """ Check key for default vary strategy.
        """
        from wheezy.http.cacheprofile import RequestVary
        request_vary = RequestVary()

        mock_request = Mock()
        mock_request.method = 'GET'
        mock_request.environ = {'PATH_INFO': '/welcome'}
        assert 'G/welcome' == request_vary.key(mock_request)

    def test_key_vary_parts(self):
        """ Check key for vary part strategy.
        """
        from wheezy.http.cacheprofile import RequestVary
        query = ['q1', 'q3', 'q2']
        form = ['f1', 'f3', 'f2']
        cookies = ['c1', 'c3', 'c2']
        environ = ['e1', 'e3', 'e2']
        request_vary = RequestVary(
                query=query,
                form=form,
                cookies=cookies,
                environ=environ)

        mock_request = Mock()
        mock_request.method = 'GET'
        mock_request.environ = {'PATH_INFO': '/welcome'}
        mock_request.query = {'q1': ['1']}
        mock_request.form = {'f2': ['2']}
        mock_request.cookies = {'c3': '3'}

        key = request_vary.key(mock_request)

        assert 'G/welcomeQN1XXFXN2XCXXN3EXXX' == key
