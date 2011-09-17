
""" ``p2to3`` module.
"""

import sys


PY3 = sys.version_info[0] == 3

if PY3:  # pragma: nocover
    from io import BytesIO
    from http.cookies import SimpleCookie

    STRING_EMPTY = ''

    def ustr(s, encoding):
        if isinstance(s, bytes):
            return str(s, encoding=encoding)
        else:
            return s
else:  # pragma: nocover
    from cStringIO import StringIO as BytesIO
    from Cookie import SimpleCookie

    STRING_EMPTY = unicode('')

    def ustr(s, encoding):
        if isinstance(s, unicode):
            return s
        else:
            return unicode(s, encoding=encoding)
