
""" ``application`` module.
"""

from wheezy.http.comp import reduce
from wheezy.http.request import HTTPRequest
from wheezy.http.response import not_found


def wrap_middleware(following, func):
    """ Helper function to wrap middleware, adapts middleware
        contract to::

            def handler(request):
                return response

        ``following`` - next middleware in the chain.
        ``func`` - middleware callable.
    """
    return lambda request: func(request, following)


class WSGIApplication(object):
    """ The application object is simply a WSGI callable object.

        ``middleware`` is any callable of the following
        contract::

            def middleware(request, following):
                if following:
                    response = following(request)
                else:
                    response
                return response

        ``middleware_factory`` is a factory that initialize
        middleware::

            def middleware_factory(options):
                return middleware

        Here are few examples of using middleware:

            >>> def x(request, following):
            ...     return 'response'
            >>> def x_factory(options):
            ...     return x
            >>> options = {'ENCODING': 'utf-8'}
            >>> app = WSGIApplication(middleware=[
            ...     x_factory
            ... ], options=options)
            >>> app.middleware(1)
            'response'

            ``middleware_factory`` can return None, this can be useful
            for some sort of initialization that needs to be run during
            application bootstrap.

            >>> def y_factory(options):
            ...     print('y_factory')
            ...     return None
            >>> app = WSGIApplication(middleware=[
            ...     x_factory,
            ...     y_factory
            ... ], options=options)
            y_factory
    """

    def __init__(self, middleware, options):
        """
        """
        middleware = [m for m in
                      (m(options) for m in middleware) if m is not None]
        middleware = reduce(
            wrap_middleware,
            reversed(middleware), None)
        assert middleware
        self.middleware = middleware
        self.options = options
        self.encoding = options['ENCODING']

    def __call__(self, environ, start_response):
        """
            >>> def x(request, following):
            ...     return None
            >>> def x_factory(options):
            ...     return x
            >>> options = {'ENCODING': 'utf-8'}
            >>> app = WSGIApplication(middleware=[
            ...     x_factory
            ... ], options=options)
            >>> def start_response(s, h):
            ...     pass
            >>> environ = {'REQUEST_METHOD': 'GET'}
            >>> app(environ, start_response)
            []
        """
        request = HTTPRequest(environ, self.encoding, self.options)
        response = self.middleware(request)
        if response is None:
            response = not_found()
        return response(start_response)
