
""" ``cacheprofile`` module.
"""

from datetime import datetime
from datetime import timedelta

from wheezy.core.datetime import total_seconds
from wheezy.http.cachepolicy import HTTPCachePolicy
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
    """ Combines a number of setting applicable to http cache policy
        as well as server side cache.

        ``no-cache`` http cache policy.

        >>> p = CacheProfile('none', no_store=True)
        >>> policy = p.cache_policy()
        >>> policy.cacheability
        'no-cache'
    """

    def __init__(self, location, duration=0, no_store=False,
            vary_query=None, vary_form=None, vary_environ=None,
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
                    query=vary_query,
                    form=vary_form,
                    environ=vary_environ
            )
        if enabled:
            cacheability = CACHEABILITY[location]
            if location in ('none', 'server'):
                policy = HTTPCachePolicy(
                        cacheability
                )
                if no_store:
                    policy.no_store()
                self.cache_policy = lambda: policy
            else:
                if not duration > 0:
                    raise ValueError('Invalid duration.')
                self.cache_policy = self.client_policy
                self.cacheability = cacheability
                self.no_store = no_store
        self.enabled = enabled
        self.duration = duration

    def cache_policy(self):
        """ Returns cache policy according to this cache profile.
            Defaults to ``None`` and substituted depending on profile
            strategy.

            >>> p = CacheProfile('none', enabled=False)
            >>> p.cache_policy()
        """
        return None

    def client_policy(self):
        """ Returns ``private`` or ``public`` http cache policy
            depending on cache profile selected.

            >>> p = CacheProfile('both', duration=15, no_store=True)
            >>> assert p.client_policy == p.cache_policy
            >>> policy = p.cache_policy()
            >>> policy.cacheability
            'private'
        """
        policy = HTTPCachePolicy(
                self.cacheability
        )
        if self.no_store:
            policy.no_store()
        now = datetime.utcnow()
        policy.expires(now + timedelta(seconds=self.duration))
        policy.max_age(self.duration)
        policy.last_modified(now)
        return policy


class RequestVary(object):
    """ Designed to compose a key depending on number of values, including:
        query, form, environ.
    """

    def __init__(self, query=None, form=None, environ=None):
        parts = []
        if query:
            self.query = tuple(sorted(query))
            parts.append(self.key_query)
        if form:
            self.form = tuple(sorted(form))
            parts.append(self.key_form)
        if environ:
            self.environ = tuple(sorted(environ))
            parts.append(self.key_environ)
        if parts:
            parts.insert(0, self.request_key)
            self.vary_parts = tuple(parts)
        else:
            self.key = self.request_key

    def request_key(self, request):
        """
            >>> from wheezy.core.collections import attrdict
            >>> request = attrdict(method='GET', environ={'PATH_INFO':'/abc'})
            >>> request_vary = RequestVary()
            >>> request_vary.request_key(request)
            'G/abc'
        """
        return request.method[:1] + request.environ['PATH_INFO']

    def key_query(self, request):
        """
            >>> from wheezy.core.collections import attrdict
            >>> request = attrdict(query={
            ...     'a': ['a1', 'a2'], 'b': ['b1'], 'c': [], 'd': ['d1']
            ... })
            >>> request_vary = RequestVary(query=['a'])
            >>> request_vary.key_query(request)
            'Qa1,a2'
            >>> request_vary = RequestVary(query=['b', 'a'])
            >>> request_vary.key_query(request)
            'Qa1,a2Qb1'
            >>> request_vary = RequestVary(query=['c', 'a', 'b'])
            >>> request_vary.key_query(request)
            'Qa1,a2Qb1Q'

            Key is missed.

            >>> request_vary = RequestVary(query=['b', '_'])
            >>> request_vary.key_query(request)
            'Qb1'
        """
        query = request.query
        return 'Q' + 'Q'.join([','.join(query[name])
            for name in self.query if name in query])

    def key_form(self, request):
        """
            >>> from wheezy.core.collections import attrdict
            >>> request = attrdict(form={
            ...     'a': ['a1', 'a2'], 'b': ['b1'], 'c': [], 'd': ['d1']
            ... })
            >>> request_vary = RequestVary(form=['a'])
            >>> request_vary.key_form(request)
            'Fa1,a2'
            >>> request_vary = RequestVary(form=['b', 'a'])
            >>> request_vary.key_form(request)
            'Fa1,a2Fb1'
            >>> request_vary = RequestVary(form=['c', 'b', 'a'])
            >>> request_vary.key_form(request)
            'Fa1,a2Fb1F'

            Key is missed

            >>> request_vary = RequestVary(form=['b', '_'])
            >>> request_vary.key_form(request)
            'Fb1'
        """
        form = request.form
        return 'F' + 'F'.join([','.join(form[name])
            for name in self.form if name in form])

    def key_environ(self, request):
        """
            >>> from wheezy.core.collections import attrdict
            >>> request = attrdict(environ={
            ...     'a': 'a1', 'b': 'b1', 'c': None, 'd': 'd1'
            ... })
            >>> request_vary = RequestVary(environ=['a'])
            >>> request_vary.key_environ(request)
            'Ea1'
            >>> request_vary = RequestVary(environ=['b', 'a'])
            >>> request_vary.key_environ(request)
            'Ea1Eb1'
            >>> request_vary = RequestVary(environ=['c', 'b', 'a'])
            >>> request_vary.key_environ(request)
            'Ea1Eb1E'

            Key is missed

            >>> request_vary = RequestVary(environ=['b', '_'])
            >>> request_vary.key_environ(request)
            'Eb1'
        """
        environ = request.environ
        return 'E' + 'E'.join([environ[name] or ''
            for name in self.environ if name in environ])

    def key(self, request):
        """
            >>> from wheezy.core.collections import attrdict
            >>> request = attrdict(method='GET',
            ...        environ={'PATH_INFO': '/abc'},
            ...        query={'a': ['3'], 'b': []},
            ...        form={'a': ['4', '5'], 'b': ['6']}
            ... )
            >>> request_vary = RequestVary()
            >>> request_vary.key(request)
            'G/abc'
            >>> request_vary = RequestVary(
            ...         query=['b', 'a'], form=['a', 'b'])
            >>> request_vary.key(request)
            'G/abcQ3QF4,5F6'
        """
        return ''.join([vary(request) for vary in self.vary_parts])
