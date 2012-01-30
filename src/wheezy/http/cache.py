
""" ``cache`` module
"""

from wheezy.core.datetime import parse_http_datetime
from wheezy.http.response import HTTP_HEADER_CONTENT_LENGTH_ZERO


def response_cache(profile, cache=None):
    """ Decorator that applies cache profile strategy to the
        wrapping handler.
    """
    def decorate(func):
        handler = httpcache(
                factory=func,
                cache_profile=profile,
                cache=cache)

        def call(request, *args, **kwargs):
            if args or kwargs:
                response = func(request, *args, **kwargs)
            else:
                response = handler(request)
            return response
        return call
    return decorate


def httpcache(factory, cache_profile, cache=None):
    """ cache factory that selects appropriate cache strategy
        according to cache profile settings.

        Disabled

        >>> from wheezy.http.cacheprofile import CacheProfile
        >>> cacheprofile = CacheProfile('none', enabled=False)
        >>> httpcache('factory', cacheprofile, 'cache')
        'factory'

        No cache strategy

        >>> from wheezy.http.response import HTTPResponse
        >>> def factory(request):
        ...     return HTTPResponse()
        >>> cacheprofile = CacheProfile('none')
        >>> result = httpcache(factory, cacheprofile, 'cache')
        >>> result.__name__
        'nocache_strategy'

        Get or set strategy

        >>> from wheezy.core.collections import attrdict
        >>> class Cache(object):
        ...     def __init__(self, response=None):
        ...         self.response = response
        ...     def get(self, key):
        ...         return self.response
        ...     def set_multi(self, mapping, time):
        ...         pass
        >>> request = attrdict(method='GET', path='/abc')
        >>> cache = Cache(response='x')
        >>> cacheprofile = CacheProfile('server', duration=100)
        >>> result = httpcache(factory, cacheprofile, cache)
        >>> result.__name__
        'get_or_set_strategy'
    """
    if cache_profile.enabled:
        if cache_profile.request_vary:
            def get_or_set_strategy(*args, **kwargs):
                kwargs['cache'] = cache
                kwargs['cache_profile'] = cache_profile
                kwargs['factory'] = factory
                return get_or_set2(*args, **kwargs)
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
    """ No cache strategy.

        CachePolicy is set if response status code is 200.

        >>> from wheezy.http.cacheprofile import CacheProfile
        >>> from wheezy.http.response import HTTPResponse
        >>> def factory(request):
        ...     return HTTPResponse()
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
    """ Get or set cache strategy.

        Cache hit.

        >>> from wheezy.core.collections import attrdict
        >>> from wheezy.http.cacheprofile import CacheProfile
        >>> from wheezy.http.response import HTTPResponse
        >>> class Cache(object):
        ...     def __init__(self, response=None):
        ...         self.response = response
        ...     def get(self, key):
        ...         return self.response
        ...     def set_multi(self, mapping, time):
        ...         pass
        >>> request = attrdict(method='GET', path='/abc')
        >>> cache_profile = CacheProfile('server', duration=100)
        >>> cache = Cache(response='x')
        >>> factory = None
        >>> get_or_set(request, cache, cache_profile, factory)
        'x'

        Cache miss.

        >>> cache = Cache(response=None)
        >>> factory = lambda r: HTTPResponse()
        >>> response = get_or_set(request, cache, cache_profile, factory)
        >>> assert isinstance(response, CacheableResponse)

        Cache dependency.

        >>> class CacheDependency(object):
        ...     def next_key(self): return 'k'
        >>> response = HTTPResponse()
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


def get_or_set2(request, cache, cache_profile, factory):
    """ cache strategy that supports IF_MODIFIED_SINCE and
        IF_NONE_MATCH HTTP request headers.
    """
    request_vary = cache_profile.request_vary
    request_key = request_vary.key(request)
    response = cache.get(request_key)
    if response:  # cache hit
        if response.last_modified:
            environ = request.environ
            modified_since = environ.get('HTTP_IF_MODIFIED_SINCE', None)
            if modified_since:
                modified_since = parse_http_datetime(modified_since)
                if modified_since >= response.last_modified:
                    return NotModifiedResponse(response)
        if response.etag:
            none_match = environ.get('HTTP_IF_NONE_MATCH', None)
            if none_match and response.etag in none_match:
                return NotModifiedResponse(response)
        return response
    response = factory(request)
    if response.status_code == 200:
        if response.cache is None:
            response.cache = cache_profile.cache_policy()
        mapping = {}
        dependency = response.dependency
        if dependency:
            mapping[dependency.next_key()] = request_key
        middleware_vary = cache_profile.middleware_vary
        if middleware_vary:
            mapping['C' + middleware_vary.key(request)] = cache_profile
        response = CacheableResponse(response)
        mapping[request_key] = response
        cache.set_multi(mapping, cache_profile.duration)
    return response


class NotModifiedResponse(object):
    """ Not modified cachable response.
    """

    status_code = 304

    def __init__(self, response):
        """
            >>> from wheezy.http.comp import ntob
            >>> from wheezy.http.response import HTTPResponse
            >>> response = HTTPResponse()
            >>> response.write('Hello')
            >>> response = CacheableResponse(response)
            >>> response = NotModifiedResponse(response)
            >>> response.headers # doctest: +NORMALIZE_WHITESPACE
            [('Content-Type', 'text/html; charset=utf-8'),
            ('Cache-Control', 'private'), ('Content-Length', '0')]
        """
        headers = [header for header in response.headers
                if header[0] != 'Content-Length']
        headers.append(HTTP_HEADER_CONTENT_LENGTH_ZERO)
        self.headers = headers

    def __call__(self, start_response):
        """
            >>> from wheezy.http.comp import ntob
            >>> from wheezy.http.response import HTTPResponse
            >>> response = HTTPResponse()
            >>> response.write('Hello')
            >>> response = CacheableResponse(response)
            >>> response = NotModifiedResponse(response)
            >>> response.status_code
            304
            >>> status = None
            >>> headers = None
            >>> def start_response(s, h):
            ...     global status
            ...     global headers
            ...     status = s
            ...     headers = h
            >>> result = response(start_response)
            >>> assert result == []
            >>> status
            '304 Not Modified'
            >>> headers # doctest: +NORMALIZE_WHITESPACE
            [('Content-Type', 'text/html; charset=utf-8'),
            ('Cache-Control', 'private'), ('Content-Length', '0')]
        """
        start_response('304 Not Modified', self.headers)
        return []


class CacheableResponse(object):
    """ Cachable response.
    """

    status_code = 200
    last_modified = None
    etag = None

    def __init__(self, response):
        """
            >>> from wheezy.http.comp import ntob
            >>> from wheezy.http.response import HTTPResponse
            >>> response = HTTPResponse()
            >>> response.write('Hello')
            >>> response = CacheableResponse(response)
            >>> response.headers # doctest: +NORMALIZE_WHITESPACE
            [('Content-Type', 'text/html; charset=utf-8'),
            ('Cache-Control', 'private'), ('Content-Length', '5')]
            >>> assert ntob('Hello', 'utf-8') in response.buffer
        """
        def capture_headers(status, headers):
            self.headers = headers
        self.buffer = tuple(response(capture_headers))
        cache_policy = response.cache
        if cache_policy:
            self.last_modified = cache_policy.modified
            self.etag = cache_policy.http_etag

    def __call__(self, start_response):
        """
            >>> from wheezy.http.comp import ntob
            >>> from wheezy.http.response import HTTPResponse
            >>> response = HTTPResponse()
            >>> response.write('Hello')
            >>> response = CacheableResponse(response)
            >>> response.status_code
            200
            >>> status = None
            >>> headers = None
            >>> def start_response(s, h):
            ...     global status
            ...     global headers
            ...     status = s
            ...     headers = h
            >>> result = response(start_response)
            >>> assert ntob('Hello', 'utf-8') in result
            >>> status
            '200 OK'
            >>> headers # doctest: +NORMALIZE_WHITESPACE
            [('Content-Type', 'text/html; charset=utf-8'),
            ('Cache-Control', 'private'), ('Content-Length', '5')]
        """
        start_response('200 OK', self.headers)
        return self.buffer
