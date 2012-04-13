
""" Unit tests for ``wheezy.http.application``.
"""

import unittest

from mock import Mock


class ResponseCacheDecoratorTestCase(unittest.TestCase):
    """ Test the ``response_cache`` decorator.
    """

    def test_cache_profile_not_enabled(self):
        """ If cache profile if not enabled return handler
            without any decoration.
        """
        from wheezy.http.cacheprofile import CacheProfile
        from wheezy.http.cache import response_cache
        profile = CacheProfile('none', enabled=False)

        handler = response_cache(profile)('handler')

        assert 'handler' == handler

    def test_cache_strategy(self):
        """ If cache profile has defined `request_vary`
            than response.cache_profile needs to be set.

            Must not override cache_policy if it has been
            set already.
        """
        from wheezy.http.cacheprofile import CacheProfile
        from wheezy.http.cache import response_cache
        profile = CacheProfile('server')
        policy = profile.cache_policy()
        mock_response = Mock()
        mock_handler = Mock(return_value=mock_response)

        handler = response_cache(profile)(mock_handler)

        # cache_policy is not set by handler
        mock_response.cache_policy = None
        response = handler('request')

        assert mock_response == response
        mock_handler.assert_called_once_with('request')
        assert profile == mock_response.cache_profile
        assert policy == mock_response.cache_policy

        # cache_policy is set by handler
        mock_response.reset_mock()
        mock_response.cache_policy = 'policy'
        response = handler('request')

        assert profile == mock_response.cache_profile
        assert 'policy' == mock_response.cache_policy

    def test_no_cache_strategy(self):
        """ If cache profile has not defined `request_vary`
            than proceed with no cache strategy.

            Must not override cache_policy if it has been
            set already.
        """
        from wheezy.http.cacheprofile import CacheProfile
        from wheezy.http.cache import response_cache
        profile = CacheProfile('none')
        policy = profile.cache_policy()
        mock_response = Mock()
        mock_response.cache_profile = None
        mock_handler = Mock(return_value=mock_response)

        handler = response_cache(profile)(mock_handler)

        # cache_policy is not set by handler
        mock_response.cache_policy = None
        response = handler('request')

        assert mock_response == response
        mock_handler.assert_called_once_with('request')
        assert None == mock_response.cache_profile
        assert policy == mock_response.cache_policy

        # cache_policy is set by handler
        mock_response.reset_mock()
        mock_response.cache_policy = 'policy'
        response = handler('request')

        assert None == mock_response.cache_profile
        assert 'policy' == mock_response.cache_policy
