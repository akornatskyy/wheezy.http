
""" ``cookie`` module.
"""

from wheezy.http import config
from wheezy.http.date import format_http_datetime
from wheezy.http.utils import attribute


class HttpCookie(object):
    """ HTTP Cookie
        http://www.ietf.org/rfc/rfc2109.txt

        ``domain``, ``secure`` and ``httponly`` are
        taken from ``config`` if not set.

        >>> c = HttpCookie('a')
        >>> c.HTTP_SET_COOKIE
        'a=; path=/'

        Value:

        >>> c = HttpCookie('a', value='123')
        >>> c.HTTP_SET_COOKIE
        'a=123; path=/'

        Domain:

        >>> c = HttpCookie('a', value='123', domain='.abc.com')
        >>> c.HTTP_SET_COOKIE
        'a=123; domain=.abc.com; path=/'

        Expires:

        >>> from datetime import datetime
        >>> from wheezy.http.date import UTC
        >>> when = datetime(2011, 9, 26, 19, 34, tzinfo=UTC)
        >>> c = HttpCookie('a', expires=when)
        >>> c.HTTP_SET_COOKIE
        'a=; expires=Mon, 26 Sep 2011 19:34:00 GMT; path=/'

        Path:

        >>> c = HttpCookie('a', path=None)
        >>> c.HTTP_SET_COOKIE
        'a='

        Secure:

        >>> c = HttpCookie('a', value='123', secure=True)
        >>> c.HTTP_SET_COOKIE
        'a=123; path=/; secure'

        Http Only:

        >>> c = HttpCookie('a', value='123', httponly=True)
        >>> c.HTTP_SET_COOKIE
        'a=123; path=/; httponly'

        All:

        >>> c = HttpCookie('a', value='123', expires=when,
        ...     path='abc', domain='.abc.com',
        ...     secure=True, httponly=True)
        >>> c.HTTP_SET_COOKIE # doctest: +NORMALIZE_WHITESPACE
        'a=123; domain=.abc.com;
        expires=Mon, 26 Sep 2011 19:34:00 GMT;
        path=abc; secure; httponly'
    """

    def __init__(self, name, value=None, expires=None,
            path='/', domain=None, secure=None, httponly=None):
        self.name = name
        self.value = value
        self.expires = expires
        self.path = path
        if domain is None:
            self.domain = config.HTTP_COOKIE_DOMAIN
        else:
            self.domain = domain
        if secure is None:
            self.secure = config.HTTP_COOKIE_SECURE
        else:
            self.secure = secure
        if httponly is None:
            self.httponly = config.HTTP_COOKIE_HTTPONLY
        else:
            self.httponly = httponly

    @classmethod
    def delete(cls, name, path='/', domain=None):
        """ Returns a cookie that is deleted by browser.

            >>> c = HttpCookie.delete('abc')
            >>> c.HTTP_SET_COOKIE
            'abc=; expires=Sat, 01 Jan 2000 00:00:01 GMT; path=/'
        """
        return cls(name,
                expires='Sat, 01 Jan 2000 00:00:01 GMT',
                path=path, domain=domain)

    def update(self, headers):
        """
            >>> from wheezy.http.utils import HttpDict
            >>> headers = HttpDict()
            >>> c = HttpCookie('a')
            >>> c.update(headers)
            >>> headers['Set-Cookie']
            'a=; path=/'
        """
        headers.getlist('Set-Cookie').append(self.HTTP_SET_COOKIE)

    @attribute
    def HTTP_SET_COOKIE(self):
        directives = []
        append = directives.append
        append(self.name + '=')
        if self.value:
            append(self.value)
        if self.domain:
            append('; domain=' + self.domain)
        if self.expires:
            append('; expires=' +
                    format_http_datetime(self.expires))
        if self.path:
            append('; path=' + self.path)
        if self.secure:
            append('; secure')
        if self.httponly:
            append('; httponly')
        return ''.join(directives)
