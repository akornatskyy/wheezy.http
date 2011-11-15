
""" ``cache`` module
"""
from functools import partial


def httpcache(factory, cache_profile, cache):
    """
        >>> from wheezy.http.cacheprofile import CacheProfile
        >>> cp = CacheProfile('none', enabled=False)
        >>> httpcache('factory', cp, 'cache')
        'factory'
        >>> cp = CacheProfile('none')
        >>> result = httpcache('factory', cp, 'cache')
        >>> result.func.__name__
        'nocache'
        >>> cp = CacheProfile('server', duration=100)
        >>> result = httpcache('factory', cp, 'cache')
        >>> result.func.__name__
        'get_or_set'
    """
    if cache_profile.enabled:
        if cache_profile.request_vary:
            return partial(get_or_set, cache=cache,
                    cache_profile=cache_profile,
                    factory=factory)
        else:
            return partial(nocache,
                    cache_profile=cache_profile,
                    factory=factory)
    else:
        return factory


def nocache(request, cache_profile, factory):
    """ CachePolicy is set if response status code is 200.

        >>> from wheezy.http.cacheprofile import CacheProfile
        >>> from wheezy.http.response import HttpResponse
        >>> def factory(request):
        ...     return HttpResponse()
        >>> cp = CacheProfile('none')
        >>> response = nocache(None, cp, factory)
        >>> assert response.cache
    """
    response = factory(request)
    if response.status_code == 200:
        if response.cache is None:
            response.cache = cache_profile.cache_policy()
    return response


def get_or_set(request, cache, cache_profile, factory):
    """
        Cache hit.

        >>> from wheezy.core.collections import attrdict
        >>> from wheezy.http.cacheprofile import CacheProfile
        >>> from wheezy.http.response import HttpResponse
        >>> class Cache(object):
        ...     def __init__(self, response=None):
        ...         self.response = response
        ...     def get(self, key):
        ...         return self.response
        ...     def set_multi(self, mapping, time):
        ...         pass
        >>> request = attrdict(METHOD='GET', PATH='/abc')
        >>> cache_profile = CacheProfile('server', duration=100)
        >>> cache = Cache(response='x')
        >>> factory = None
        >>> get_or_set(request, cache, cache_profile, factory)
        'x'

        Cache miss.

        >>> cache = Cache(response=None)
        >>> factory = lambda r: HttpResponse()
        >>> response = get_or_set(request, cache, cache_profile, factory)
        >>> assert isinstance(response, CacheableResponse)

        Cache dependency.

        >>> class CacheDependency(object):
        ...     def next_key(self): return 'k'
        >>> response = HttpResponse()
        >>> response.dependency = CacheDependency()
        >>> factory = lambda r: response
        >>> response = get_or_set(request, cache, cache_profile, factory)
        >>> assert isinstance(response, CacheableResponse)
    """
    request_vary = cache_profile.request_vary
    request_key = request_vary.key(request)
    response = cache.get(request_key)
    if response:  # cache hit
        return response
    response = factory(request)
    if response.status_code == 200:
        if response.cache is None:
            response.cache = cache_profile.cache_policy()
        mapping = {}
        dependency = response.dependency
        if dependency:
            mapping[dependency.next_key()] = request_key
        response = CacheableResponse(response)
        mapping[request_key] = response
        cache.set_multi(mapping, cache_profile.duration)
    return response


class CacheableResponse(object):

    def __init__(self, response):
        """
            >>> from wheezy.http.response import HttpResponse
            >>> response = HttpResponse()
            >>> response.write('Hello')
            >>> response = CacheableResponse(response)
            >>> response.headers # doctest: +NORMALIZE_WHITESPACE
            [('Content-Type', 'text/html; charset=utf-8'),
            ('Cache-Control', 'private'), ('Content-Length', '5')]
            >>> response.buffer
            ('Hello',)
        """
        def capture_headers(status_code, headers):
            self.headers = headers
        self.buffer = tuple(response(capture_headers))

    def __call__(self, start_response):
        """
            >>> from wheezy.http.response import HttpResponse
            >>> response = HttpResponse()
            >>> response.write('Hello')
            >>> response = CacheableResponse(response)
            >>> status_code = None
            >>> headers = None
            >>> def start_response(s, h):
            ...     global status_code
            ...     global headers
            ...     status_code = s
            ...     headers = h
            >>> response(start_response)
            ('Hello',)
            >>> status_code
            '200 OK'
            >>> headers # doctest: +NORMALIZE_WHITESPACE
            [('Content-Type', 'text/html; charset=utf-8'),
            ('Cache-Control', 'private'), ('Content-Length', '5')]
        """
        start_response('200 OK', self.headers)
        return self.buffer