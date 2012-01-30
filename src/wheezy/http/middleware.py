
""" ``middleware`` module.
"""

from wheezy.http.cache import httpcache


class HTTPCacheMiddleware(object):
    """ HTTP cache middleware.
    """

    def __init__(self, cache, middleware_vary):
        """
            ``cache`` - cache to be used.
            ``middleware_vary`` - a way to determine cache key
            for the request.
        """
        assert cache
        assert middleware_vary
        self.cache = cache
        self.middleware_vary = middleware_vary

    def __call__(self, request, following):
        assert following is not None
        cache_profile = self.cache.get(
                'C' + self.middleware_vary.key(request))
        if cache_profile is None:
            return following(request)
        else:
            handler = httpcache(following, cache_profile, self.cache)
            return handler(request)


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
