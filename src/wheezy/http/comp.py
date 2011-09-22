
""" ``p2to3`` module.
"""

import sys


PY3 = sys.version_info[0] >= 3

if PY3:  # pragma: nocover
    from io import BytesIO

    def ntob(native, encoding):
        """ Converts native string to bytes
        """
        return native.encode(encoding)

    def ntou(native, encoding):
        """ Converts native string to unicode
        """
        return native

else:  # pragma: nocover
    from cStringIO import StringIO as BytesIO

    def ntob(native, encoding):
        """ Converts native string to bytes
        """
        return native

    def ntou(native, encoding):
        """ Converts native string to unicode
        """
        return native.decode(encoding)

if PY3:  # pragma: nocover
    from http.cookies import SimpleCookie
else:  # pragma: nocover
    from Cookie import SimpleCookie


if PY3:  # pragma: nocover
    from urllib.parse import parse_qs as _parse_qs

    def parse_qs(qs, encoding):
        return _parse_qs(qs, keep_blank_values=True, encoding=encoding)
else:  # pragma: nocover
    try:
        # Python 2.6+
        from urlparse import parse_qs as _parse_qs
    except ImportError:  # pragma: nocover
        # Python 2.5, 2.4
        from cgi import parse_qs as _parse_qs

    def parse_qs(qs, encoding):
        return _parse_qs(qs, keep_blank_values=True)
