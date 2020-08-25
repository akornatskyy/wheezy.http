""" ``method`` module.
"""

from wheezy.http.response import method_not_allowed


def accept_method(constraint):
    """Decorator that accepts only particular HTTP
    request method if ``constraint`` is a string::

        @accept_method('GET')
        def my_view(request):
            response = ...
            return response

    or HTTP request methods if ``constraint`` is
    a list or tuple::

        @accept_method(('GET', 'POST'))
        def my_view(request):
            response = ...
            return response

    method constraint must be in uppercase.
    """

    def decorate(handler):
        if isinstance(constraint, (list, tuple)):

            def one_of(request, *args, **kwargs):
                if request.method not in constraint:
                    return method_not_allowed()
                return handler(request, *args, **kwargs)

            return one_of
        else:

            def exact(request, *args, **kwargs):
                if request.method != constraint:
                    return method_not_allowed()
                return handler(request, *args, **kwargs)

            return exact

    return decorate
