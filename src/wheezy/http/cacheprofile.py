
""" ``cacheprofile`` module.
"""

from datetime import datetime
from time import time

from wheezy.core.datetime import total_seconds
from wheezy.http.cachepolicy import HTTPCachePolicy


CACHEABILITY = {
    'none': 'no-cache',
    'server': 'no-cache',
    'client': 'private',
    'both': 'private',  # server and client
    'public': 'public',
}

SUPPORTED = CACHEABILITY.keys()
utcfromtimestamp = datetime.utcfromtimestamp


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
                 vary_cookies=None, http_vary=None, http_max_age=None,
                 etag_func=None, namespace=None, enabled=True):
        """
            ``location`` must fall into one of acceptable
            values as defined by ``SUPPORTED``.
            >>> p = CacheProfile('none')

            Otherwise raise ``ValueError``.

            >>> p = CacheProfile('x') # doctest: +ELLIPSIS
            Traceback (most recent call last):
                ...
            AssertionError...

            ``duration`` is required for certain locations

            >>> from datetime import timedelta
            >>> p = CacheProfile('client', duration=900)
            >>> p = CacheProfile('client',
            ...         duration=timedelta(minutes=15))
            >>> p = CacheProfile('client') # doctest: +ELLIPSIS
            Traceback (most recent call last):
                ...
            ValueError: Invalid duration.
        """
        assert location in SUPPORTED
        if enabled:
            if location in ('none', 'client'):
                self.request_vary = None
            else:
                self.namespace = namespace
                self.request_vary = RequestVary(
                    query=vary_query,
                    form=vary_form,
                    cookies=vary_cookies,
                    environ=vary_environ
                )
            cacheability = CACHEABILITY[location]
            if location in ('none', 'server'):
                policy = HTTPCachePolicy(
                    cacheability
                )
                if no_store:
                    policy.no_store()
                self.etag_func = None
                self.cache_policy = lambda: policy
            else:
                self.etag_func = etag_func
                self.http_vary = http_vary
                self.cache_policy = self.client_policy
                self.cacheability = cacheability
                self.no_store = no_store
            if location != 'none':
                duration = total_seconds(duration)
                if not duration > 0:
                    raise ValueError('Invalid duration.')
                self.duration = duration
                if http_max_age is None:
                    self.http_max_age = duration
                else:
                    self.http_max_age = total_seconds(http_max_age)
        self.enabled = enabled

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

            >>> p = CacheProfile('both', duration=15, http_max_age=0,
            ...                  no_store=True)
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
        now = int(time())
        if self.http_max_age:
            policy.last_modified(utcfromtimestamp(now))
            policy.expires(utcfromtimestamp(now + self.http_max_age))
            policy.max_age(self.http_max_age)
        else:
            now = utcfromtimestamp(now)
            policy.last_modified(now)
            policy.expires(now)
            policy.max_age(0)
        if self.http_vary is not None:
            policy.vary(*self.http_vary)
        return policy


class RequestVary(object):
    """ Designed to compose a key depending on number of values, including:
        query, form, environ.
    """

    def __init__(self, query=None, form=None, cookies=None, environ=None):
        parts = []
        if query:
            self.query = tuple(sorted(query))
            parts.append(self.key_query)
        if form:
            self.form = tuple(sorted(form))
            parts.append(self.key_form)
        if cookies:
            self.cookies = tuple(sorted(cookies))
            parts.append(self.key_cookies)
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
            ...     'a': ['1', '2'], 'b': ['3', ''], 'c': []
            ... })
            >>> request_vary = RequestVary(query=['a', 'b'])
            >>> request_vary.key_query(request)
            'QN1;2N3;'
            >>> request_vary = RequestVary(query=['a'])
            >>> request_vary.key_query(request)
            'QN1;2'
            >>> request_vary = RequestVary(query=['c'])
            >>> request_vary.key_query(request)
            'QN'

            Key is missing.

            >>> request_vary = RequestVary(query=['d'])
            >>> request_vary.key_query(request)
            'QX'
        """
        query = request.query
        return 'Q' + ''.join([
            (name in query) and ('N' + ';'.join(query[name])) or 'X'
            for name in self.query])

    def key_form(self, request):
        """
            >>> from wheezy.core.collections import attrdict
            >>> request = attrdict(form={
            ...     'a': ['1', '2'], 'b': ['3', ''], 'c': []
            ... })
            >>> request_vary = RequestVary(form=['a', 'b'])
            >>> request_vary.key_form(request)
            'FN1;2N3;'
            >>> request_vary = RequestVary(form=['a'])
            >>> request_vary.key_form(request)
            'FN1;2'
            >>> request_vary = RequestVary(form=['c'])
            >>> request_vary.key_form(request)
            'FN'

            Key is missing.

            >>> request_vary = RequestVary(form=['d'])
            >>> request_vary.key_form(request)
            'FX'
        """
        form = request.form
        return 'F' + ''.join([
            (name in form) and ('N' + ';'.join(form[name])) or 'X'
            for name in self.form])

    def key_cookies(self, request):
        """
            >>> from wheezy.core.collections import attrdict
            >>> request = attrdict(cookies={
            ...     'a': '1', 'b': '', 'c': None
            ... })
            >>> request_vary = RequestVary(cookies=['a', 'b'])
            >>> request_vary.key_cookies(request)
            'CN1N'
            >>> request_vary = RequestVary(cookies=['a'])
            >>> request_vary.key_cookies(request)
            'CN1'
            >>> request_vary = RequestVary(cookies=['c'])
            >>> request_vary.key_cookies(request)
            'CN'

            Key is missing.

            >>> request_vary = RequestVary(cookies=['d'])
            >>> request_vary.key_cookies(request)
            'CX'
        """
        cookies = request.cookies
        return 'C' + ''.join([
            (name in cookies) and ('N' + (cookies[name] or '')) or 'X'
            for name in self.cookies])

    def key_environ(self, request):
        """
            >>> from wheezy.core.collections import attrdict
            >>> request = attrdict(environ={
            ...     'a': '1', 'b': '', 'c': None
            ... })
            >>> request_vary = RequestVary(environ=['a', 'b'])
            >>> request_vary.key_environ(request)
            'EN1N'
            >>> request_vary = RequestVary(environ=['a'])
            >>> request_vary.key_environ(request)
            'EN1'
            >>> request_vary = RequestVary(environ=['c'])
            >>> request_vary.key_environ(request)
            'EN'

            Key is missing.

            >>> request_vary = RequestVary(environ=['d'])
            >>> request_vary.key_environ(request)
            'EX'
        """
        environ = request.environ
        return 'E' + ''.join([
            (name in environ) and ('N' + (environ[name] or '')) or 'X'
            for name in self.environ])

    def key(self, request):
        """
            >>> from wheezy.core.collections import attrdict
            >>> request = attrdict(method='GET',
            ...        environ={'PATH_INFO': '/abc'},
            ...        query={'a': ['1'], 'b': []},
            ...        form={'a': ['1', '2'], 'b': ['3']}
            ... )
            >>> request_vary = RequestVary()
            >>> request_vary.key(request)
            'G/abc'
            >>> request_vary = RequestVary(
            ...         query=['a', 'b'], form=['a', 'b'])
            >>> request_vary.key(request)
            'G/abcQN1NFN1;2N3'

            >>> request_vary = RequestVary(
            ...         query=['a', 'c'], form=['a', '_'])
            >>> request_vary.key(request)
            'G/abcQN1XFXN1;2'
        """
        return ''.join([vary(request) for vary in self.vary_parts])
