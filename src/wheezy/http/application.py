
""" ``app`` module.
"""

from wheezy.http.comp import reduce
from wheezy.http.request import HTTPRequest
from wheezy.http.response import not_found


def wraps_middleware(following, func):
    return lambda request: func(request, following)


class WSGIApplication(object):
    """
        ``middleware`` is any callable of the following contract:

        def middleware(request, following):
            if following:
                response = following(request)
            else:
                response
            return response

        ``middleware_factory`` is a factory that initialize middleware:

        def middleware_factory(options):
            return middleware
    """

    def __init__(self, middleware, options=None):
        """
            >>> def x(request, following):
            ...     return 'x'
            >>> def x_factory(options):
            ...     return x
            >>> app = WSGIApplication(middleware=[
            ...     x_factory
            ... ])
            >>> app.middleware(1)
            'x'

            ``middleware_factory`` can return None, this can be useful
            from some sort of initialization that needs to be run during
            application bootstrap.

            >>> def y_factory(options):
            ...     print('y_factory')
            ...     return None
            >>> app = WSGIApplication(middleware=[
            ...     x_factory,
            ...     y_factory
            ... ])
            y_factory
        """
        options = options or {}
        middleware = [m for m in
                (m(options) for m in middleware) if m is not None]
        middleware = reduce(
                wraps_middleware,
                reversed(middleware), None)
        assert middleware
        self.middleware = middleware
        self.options = options

    def __call__(self, environ, start_response):
        """
            >>> def x(request, following):
            ...     return None
            >>> def x_factory(options):
            ...     return x
            >>> app = WSGIApplication(middleware=[
            ...     x_factory
            ... ])
            >>> def start_response(s, h):
            ...     pass
            >>> environ = {'REQUEST_METHOD': 'GET'}
            >>> app(environ, start_response)
            []
        """
        request = HTTPRequest(environ, options=self.options)
        response = self.middleware(request)
        if response is None:
            response = not_found()
        return response(start_response)