
""" ``middleware`` module.
"""

from wheezy.core.collections import defaultdict
from wheezy.core.datetime import parse_http_datetime
from wheezy.http.cache import CacheableResponse
from wheezy.http.cache import NotModifiedResponse
from wheezy.http.cacheprofile import RequestVary


class HTTPCacheMiddleware(object):
    """ HTTP cache middleware.
    """

    def __init__(self, cache, middleware_vary):
        """
            ``cache`` - cache to be used.
            ``middleware_vary`` - a way to determine cache profile
            key for the request.
        """
        assert cache
        assert middleware_vary
        self.cache = cache
        self.middleware_vary = middleware_vary
        self.profiles = defaultdict()

    def __call__(self, request, following):
        middleware_key = 'C' + self.middleware_vary.key(request)
        cache_profile = self.profiles.get(middleware_key, None)
        if cache_profile:
            request_key = cache_profile.request_vary.key(request)
            response = self.cache.get(request_key)
            if response:  # cache hit
                if response.last_modified:
                    environ = request.environ
                    modified_since = environ.get(
                            'HTTP_IF_MODIFIED_SINCE', None)
                    if modified_since:
                        modified_since = parse_http_datetime(modified_since)
                        if modified_since >= response.last_modified:
                            return NotModifiedResponse(response)
                if response.etag:
                    none_match = environ.get('HTTP_IF_NONE_MATCH', None)
                    if none_match and response.etag in none_match:
                        return NotModifiedResponse(response)
                return response
        response = following(request)
        if response.status_code == 200:
            response_cache_profile = response.cache_profile
            if response_cache_profile:
                if cache_profile != response_cache_profile:
                    self.profiles[middleware_key] = response_cache_profile
                    request_key = response_cache_profile.request_vary.key(
                            request)
                dependency = response.dependency
                response = CacheableResponse(response)
                if dependency:
                    self.cache.set_multi({
                        request_key: response,
                        dependency.next_key(): request_key
                        }, response_cache_profile.duration)
                else:
                    self.cache.set(
                        request_key,
                        response,
                        response_cache_profile.duration)
        return response


def http_cache_middleware_factory(options):
    """ HTTP cache middleware factory.

        Requires ``http_cache`` in options.

        Supports ``http_cache_middleware_vary`` - a way to determine
        cache key for the request.
    """
    cache = options['http_cache']
    middleware_vary = options.get('http_cache_middleware_vary', None)
    if middleware_vary is None:
        middleware_vary = RequestVary()
        options['http_cache_middleware_vary'] = middleware_vary
    return HTTPCacheMiddleware(
            cache=cache,
            middleware_vary=middleware_vary)
