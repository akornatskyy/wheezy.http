
""" ``cacheprofile`` module.
"""

from datetime import timedelta
from datetime import datetime

from wheezy.http.cachepolicy import HttpCachePolicy
from wheezy.http.cachepolicy import SUPPORTED


CACHEABILITY = {
        'none': 'no-cache',
        'server': 'no-cache',
        'client': 'private',
        'both': 'private',  # server and client
        'public': 'public',
}

assert set(SUPPORTED) == set(CACHEABILITY.values())
SUPPORTED = CACHEABILITY.keys()


class CacheProfile(object):

    def __init__(self, location, duration=0, no_store=False,
            vary_headers=None, vary_params=None, enabled=True):
        """
            ``location`` must fall into one of acceptable
            values as defined by ``SUPPORTED``.
            >>> p = CacheProfile('none')

            Otherwise raise ``ValueError``.

            >>> p = CacheProfile('x') # doctest: +ELLIPSIS
            Traceback (most recent call last):
                ...
            ValueError: Invalid location.

            ``duration`` is required for certain locations

            >>> p = CacheProfile('client', duration=900)
            >>> p = CacheProfile('client',
            ...         duration=timedelta(minutes=15))
            >>> p = CacheProfile('client') # doctest: +ELLIPSIS
            Traceback (most recent call last):
                ...
            ValueError: Invalid duration.
        """
        if location not in SUPPORTED:
            raise ValueError('Invalid location.')
        if not isinstance(duration, timedelta):
            duration = timedelta(duration)
        if enabled:
            if location in ('none', 'server'):
                self.cache_policy = self.no_client_policy
            else:
                if duration <= timedelta(0):
                    raise ValueError('Invalid duration.')
                self.cache_policy = self.client_policy
        self.location = location
        self.duration = duration
        self.no_store = no_store
        self.vary_headers = vary_headers or []
        self.vary_params = vary_params or []
        self.enabled = enabled

    def cache_policy(self):
        """
            >>> p = CacheProfile('none', enabled=False)
            >>> p.cache_policy()
        """
        return None

    def no_client_policy(self):
        """
            >>> p = CacheProfile('none', no_store=True)
            >>> assert p.no_client_policy == p.cache_policy
            >>> policy = p.cache_policy()
        """
        policy = HttpCachePolicy(
                CACHEABILITY[self.location]
        )
        if self.no_store:
            policy.no_store()
        policy.vary_headers = list(self.vary_headers)
        policy.vary_params = list(self.vary_params)
        return policy

    def client_policy(self):
        """
            >>> p = CacheProfile('both', duration=15)
            >>> assert p.client_policy == p.cache_policy
            >>> policy = p.cache_policy()
        """
        policy = self.no_client_policy()
        now = datetime.utcnow()
        policy.expires(now + self.duration)
        policy.max_age(self.duration)
        policy.last_modified(now)
        return policy
