
""" ``cache`` module
"""


def httpcache(factory, cache_profile, cache):
    """
        Disabled

        >>> from wheezy.http.cacheprofile import CacheProfile
        >>> cacheprofile = CacheProfile('none', enabled=False)
        >>> httpcache('factory', cacheprofile, 'cache')
        'factory'

        No cache strategy

        >>> from wheezy.http.response import HttpResponse
        >>> def factory(request):
        ...     return HttpResponse()
        >>> cacheprofile = CacheProfile('none')
        >>> result = httpcache(factory, cacheprofile, 'cache')
        >>> result.__name__
        'nocache_strategy'
        >>> assert isinstance(result(None), HttpResponse)

        Get or set strategy

        >>> from wheezy.core.collections import attrdict
        >>> class Cache(object):
        ...     def __init__(self, response=None):
        ...         self.response = response
        ...     def get(self, key):
        ...         return self.response
        ...     def set_multi(self, mapping, time):
        ...         pass
        >>> request = attrdict(METHOD='GET', PATH='/abc')
        >>> cache = Cache(response='x')
        >>> cacheprofile = CacheProfile('server', duration=100)
        >>> result = httpcache(factory, cacheprofile, cache)
        >>> result.__name__
        'get_or_set_strategy'
        >>> result(request)
        'x'
    """
    if cache_profile.enabled:
        if cache_profile.request_vary:
            def get_or_set_strategy(*args, **kwargs):
                kwargs['cache'] = cache
                kwargs['cache_profile'] = cache_profile
                kwargs['factory'] = factory
                return get_or_set(*args, **kwargs)
            return get_or_set_strategy
        else:
            def nocache_strategy(*args, **kwargs):
                kwargs['cache_profile'] = cache_profile
                kwargs['factory'] = factory
                return nocache(*args, **kwargs)
            return nocache_strategy
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
    if response.status_code in (200, 304):
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
            >>> from wheezy.http.comp import ntob
            >>> from wheezy.http.response import HttpResponse
            >>> response = HttpResponse()
            >>> response.write('Hello')
            >>> response = CacheableResponse(response)
            >>> response.headers # doctest: +NORMALIZE_WHITESPACE
            [('Content-Type', 'text/html; charset=utf-8'),
            ('Cache-Control', 'private'), ('Content-Length', '5')]
            >>> assert ntob('Hello', 'utf-8') in response.buffer
        """
        def capture_headers(status, headers):
            self.status = status
            self.headers = headers
        self.buffer = tuple(response(capture_headers))
        self.status_code = response.status_code

    def __call__(self, start_response):
        """
            >>> from wheezy.http.comp import ntob
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
            >>> result = response(start_response)
            >>> assert ntob('Hello', 'utf-8') in result
            >>> status_code
            '200 OK'
            >>> headers # doctest: +NORMALIZE_WHITESPACE
            [('Content-Type', 'text/html; charset=utf-8'),
            ('Cache-Control', 'private'), ('Content-Length', '5')]
        """
        start_response(self.status, self.headers)
        return self.buffer
