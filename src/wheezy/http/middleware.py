""" ``middleware`` module.
"""

from wheezy.core.datetime import parse_http_datetime

from wheezy.http.cache import (
    CacheableResponse,
    NotModifiedResponse,
    SurfaceResponse,
)
from wheezy.http.cacheprofile import RequestVary
from wheezy.http.response import HTTPResponse


class HTTPCacheMiddleware(object):
    """HTTP cache middleware."""

    def __init__(self, cache, middleware_vary):
        """
        ``cache`` - cache to be used.
        ``middleware_vary`` - a way to determine cache profile
        key for the request.
        """
        assert cache
        assert hasattr(cache, "get")
        assert hasattr(cache, "incr")
        assert hasattr(cache, "set")
        assert hasattr(cache, "set_multi")
        assert middleware_vary
        self.cache = cache
        self.key = middleware_vary.key
        self.profiles = {}

    def __call__(self, request, following):
        middleware_key = self.key(request)
        if middleware_key in self.profiles:
            cache_profile = self.profiles[middleware_key]
            request_key = cache_profile.request_vary.key(request)
            response = self.cache.get(request_key, cache_profile.namespace)
            if response:  # cache hit
                environ = request.environ
                if response.etag and "HTTP_IF_NONE_MATCH" in environ:
                    if response.etag in environ["HTTP_IF_NONE_MATCH"]:
                        return NotModifiedResponse(response)
                elif (
                    response.last_modified
                    and "HTTP_IF_MODIFIED_SINCE" in environ
                    and parse_http_datetime(environ["HTTP_IF_MODIFIED_SINCE"])
                    >= response.last_modified
                ):
                    return NotModifiedResponse(response)
                return response
        response = following(request)
        if response and response.status_code == 200:
            cache_profile = response.cache_profile
            if cache_profile:
                if (
                    middleware_key not in self.profiles
                    or cache_profile != self.profiles[middleware_key]
                ):
                    self.profiles[middleware_key] = cache_profile
                request_key = cache_profile.request_vary.key(request)
                cache_dependency = response.cache_dependency
                # cachable response filters out set-cookie headers
                cacheable = CacheableResponse(response)
                if cache_dependency:
                    # determine next key for dependency
                    mapping = dict.fromkeys(
                        [
                            key
                            + str(
                                self.cache.incr(
                                    key, 1, cache_profile.namespace, 0
                                )
                            )
                            for key in cache_dependency
                        ],
                        request_key,
                    )
                    mapping[request_key] = cacheable
                    self.cache.set_multi(
                        mapping,
                        cache_profile.duration,
                        cache_profile.namespace,
                    )
                else:
                    self.cache.set(
                        request_key,
                        cacheable,
                        cache_profile.duration,
                        cache_profile.namespace,
                    )
                environ = request.environ
                if cacheable.etag and "HTTP_IF_NONE_MATCH" in environ:
                    if cacheable.etag in environ["HTTP_IF_NONE_MATCH"]:
                        return NotModifiedResponse(response)
                elif (
                    cacheable.last_modified
                    and "HTTP_IF_MODIFIED_SINCE" in environ
                    and parse_http_datetime(environ["HTTP_IF_MODIFIED_SINCE"])
                    >= cacheable.last_modified
                ):
                    return NotModifiedResponse(response)
                # the response already has all necessary headers
                return SurfaceResponse(response)
        return response


def http_cache_middleware_factory(options):
    """HTTP cache middleware factory.

    Requires ``http_cache`` in options.

    Supports ``http_cache_middleware_vary`` - a way to determine
    cache key for the request.
    """
    cache = options["http_cache"]
    middleware_vary = options.get("http_cache_middleware_vary", None)
    if middleware_vary is None:
        middleware_vary = RequestVary()
        options["http_cache_middleware_vary"] = middleware_vary
    return HTTPCacheMiddleware(cache=cache, middleware_vary=middleware_vary)


class WSGIAdapterMiddleware(object):
    """WSGI adapter middleware."""

    def __init__(self, wsgi_app):
        """`` wsgi_app`` - a WSGI application used to adapt calls."""
        self.wsgi_app = wsgi_app

    def __call__(self, request, following):
        assert not following

        response = HTTPResponse()

        def start_response(status, headers):
            response.status_code = int(status.split(" ", 1)[0])
            response.headers = [
                (name, value)
                for name, value in headers
                if name != "Content-Length"
            ]
            return response.write_bytes

        result = self.wsgi_app(request.environ, start_response)
        try:
            response.buffer.extend(result)
        finally:
            if hasattr(result, "close"):  # pragma: nocover
                result.close()
        return response


def wsgi_adapter_middleware_factory(options):
    """WSGI adapter middleware factory.

    Requires ``wsgi_app`` in options.
    """
    wsgi_app = options["wsgi_app"]
    return WSGIAdapterMiddleware(wsgi_app)


class EnvironCacheAdapterMiddleware(object):
    """WSGI environ cache adapter middleware."""

    def __call__(self, request, following):
        assert following
        response = following(request)
        environ = request.environ
        policy = None
        if "wheezy.http.cache_policy" in environ:
            policy = environ["wheezy.http.cache_policy"]
            response.cache_policy = policy
        if "wheezy.http.cache_profile" in environ:
            profile = environ["wheezy.http.cache_profile"]
            response.cache_profile = profile
            if policy is None:
                response.cache_policy = profile.cache_policy()
                if profile.etag_func is not None:
                    response.cache_policy.etag(
                        profile.etag_func(response.buffer)
                    )
        if "wheezy.http.cache_dependency" in environ:
            response.cache_dependency = environ["wheezy.http.cache_dependency"]
        return response


def environ_cache_adapter_middleware_factory(options):
    """WSGI environ cache adapter middleware factory."""
    return EnvironCacheAdapterMiddleware()
