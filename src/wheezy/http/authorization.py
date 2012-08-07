
"""
"""

from wheezy.core.url import UrlParts
from wheezy.http.response import permanent_redirect


def secure(wrapped=None, enabled=True):
    """ Checks if user is accessing protected resource via SSL and if
        not, issue permanent redirect to HTTPS location.

        ``enabled`` - whenever to do any checks (defaults to ``True``).

        Example::

                @secure
                def my_view(request):
                    ...
                    return response

        Using ``enabled``::

                @secure(enabled=False)
                def my_view(request):
                    ...
                    return response
    """
    def decorate(method):
        if not enabled:
            return method

        def check(request, *args, **kwargs):
            if not request.secure:
                parts = request.urlparts
                parts = UrlParts(('https',  # scheme
                                  parts[1],  # netloc
                                  parts[2],  # path
                                  parts[3],  # query
                                  None,  # fragment
                                  ))
                return permanent_redirect(parts.geturl())
            return method(request, *args, **kwargs)
        return check
    if wrapped is None:
        return decorate
    else:
        return decorate(wrapped)
