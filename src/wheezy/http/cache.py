
""" ``cache`` module
"""
from functools import partial


def httpcache(factory, cache_profile, cache):
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
    response = factory(request)
    if response.status_code == 200:
        if response.cache is None:
            response.cache = cache_profile.cache_policy()
    return response


def get_or_set(request, cache, cache_profile, factory):
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
        start_response('200 OK', self.headers)
        return self.buffer
