
""" ``cacheprofile`` module.
"""

from datetime import datetime
from datetime import timedelta

from wheezy.core.datetime import total_seconds
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
            vary_headers=None, vary_query=None, vary_form=None,
            enabled=True):
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
        duration = total_seconds(duration)
        if location == 'none':
            self.request_vary = None
        else:
            self.request_vary = RequestVary(
                    headers=vary_headers,
                    query=vary_query,
                    form=vary_form
            )
        if enabled:
            if location in ('none', 'server'):
                self.cache_policy = self.no_client_policy
            else:
                if not duration > 0:
                    raise ValueError('Invalid duration.')
                self.cache_policy = self.client_policy
        self.location = location
        self.duration = duration
        self.no_store = no_store
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
        return policy

    def client_policy(self):
        """
            >>> p = CacheProfile('both', duration=15)
            >>> assert p.client_policy == p.cache_policy
            >>> policy = p.cache_policy()
        """
        policy = self.no_client_policy()
        now = datetime.utcnow()
        policy.expires(now + timedelta(seconds=self.duration))
        policy.max_age(self.duration)
        policy.last_modified(now)
        return policy


class RequestVary(object):

    def __init__(self, headers=None, query=None, form=None):
        parts = []
        if headers:
            self.headers = tuple(headers)
            parts.append(self.key_headers)
        if query:
            self.query = tuple(query)
            parts.append(self.key_query)
        if form:
            self.form = tuple(form)
            parts.append(self.key_form)
        if parts:
            parts.insert(0, self.request_key)
            self.vary_parts = tuple(parts)
        else:
            self.key = self.request_key

    def request_key(self, request):
        """
            >>> from wheezy.core.collections import attrdict
            >>> request = attrdict(METHOD='GET', PATH='/abc')
            >>> request_vary = RequestVary(headers=['a'])
            >>> request_vary.request_key(request)
            'G/abc'
        """
        return request.METHOD[:1] + request.PATH

    def key_headers(self, request):
        """
            >>> from wheezy.core.collections import attrdict
            >>> request = attrdict(HEADERS={
            ...     'a': '1', 'b': '2', 'c': None, 'd': '4'
            ... })
            >>> request_vary = RequestVary(headers=['a'])
            >>> request_vary.key_headers(request)
            'H1'
            >>> request_vary = RequestVary(headers=['a', 'b'])
            >>> request_vary.key_headers(request)
            'H1H2'
            >>> request_vary = RequestVary(headers=['a', 'b', 'c'])
            >>> request_vary.key_headers(request)
            'H1H2H'
        """
        headers = request.HEADERS
        return 'H' + 'H'.join([headers[name] or ''
            for name in self.headers])

    def key_query(self, request):
        """
            >>> from wheezy.core.collections import attrdict
            >>> request = attrdict(QUERY={
            ...     'a': ['a1', 'a2'], 'b': ['b1'], 'c': [], 'd': ['d1']
            ... })
            >>> request_vary = RequestVary(query=['a'])
            >>> request_vary.key_query(request)
            'Qa1,a2'
            >>> request_vary = RequestVary(query=['a', 'b'])
            >>> request_vary.key_query(request)
            'Qa1,a2Qb1'
            >>> request_vary = RequestVary(query=['a', 'b', 'c'])
            >>> request_vary.key_query(request)
            'Qa1,a2Qb1Q'
        """
        query = request.QUERY
        return 'Q' + 'Q'.join([','.join(query[name] or [])
            for name in self.query])

    def key_form(self, request):
        """
            >>> from wheezy.core.collections import attrdict
            >>> request = attrdict(FORM={
            ...     'a': ['a1', 'a2'], 'b': ['b1'], 'c': [], 'd': ['d1']
            ... })
            >>> request_vary = RequestVary(form=['a'])
            >>> request_vary.key_form(request)
            'Fa1,a2'
            >>> request_vary = RequestVary(form=['a', 'b'])
            >>> request_vary.key_form(request)
            'Fa1,a2Fb1'
            >>> request_vary = RequestVary(form=['a', 'b', 'c'])
            >>> request_vary.key_form(request)
            'Fa1,a2Fb1F'
        """
        form = request.FORM
        return 'F' + 'F'.join([','.join(form[name] or [])
            for name in self.form])

    def key(self, request):
        """
            >>> from wheezy.core.collections import attrdict
            >>> request = attrdict(METHOD='GET', PATH='/abc',
            ...        HEADERS={'a': '1', 'b': '2'},
            ...        QUERY={'a': ['3'], 'b': []},
            ...        FORM={'a': ['4', '5'], 'b': ['6']}
            ... )
            >>> request_vary = RequestVary()
            >>> request_vary.key(request)
            'G/abc'
            >>> request_vary = RequestVary(
            ...         headers=['a'], query=['a', 'b'], form=['a', 'b'])
            >>> request_vary.key(request)
            'G/abcH1Q3QF4,5F6'
        """
        return ''.join([vary(request) for vary in self.vary_parts])
