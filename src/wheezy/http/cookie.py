
""" ``cookie`` module.
"""

from datetime import datetime
from time import time

from wheezy.core.datetime import format_http_datetime
from wheezy.core.descriptors import attribute
from wheezy.core.config import Config

from wheezy.http import config


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

        >>> from wheezy.core.datetime import UTC
        >>> when = datetime(2011, 9, 26, 19, 34, tzinfo=UTC)
        >>> c = HttpCookie('a', expires=when)
        >>> c.HTTP_SET_COOKIE
        'a=; expires=Mon, 26 Sep 2011 19:34:00 GMT; path=/'

        Max Age:

        >>> from datetime import timedelta
        >>> c = HttpCookie('a', max_age=1200)
        >>> now = datetime.utcnow()
        >>> assert c.expires > now
        >>> assert c.expires <= now + timedelta(seconds=1200)

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

    def __init__(self, name, value=None, expires=None, max_age=None,
            path='/', domain=None, secure=None, httponly=None,
            options=None):
        self.name = name
        self.value = value
        if max_age:
            self.expires = datetime.utcfromtimestamp(time() + max_age)
        else:
            self.expires = expires
        self.path = path
        self.config = Config(options, master=config)
        if domain is None:
            self.domain = self.config.HTTP_COOKIE_DOMAIN
        else:
            self.domain = domain
        if secure is None:
            self.secure = self.config.HTTP_COOKIE_SECURE
        else:
            self.secure = secure
        if httponly is None:
            self.httponly = self.config.HTTP_COOKIE_HTTPONLY
        else:
            self.httponly = httponly

    @classmethod
    def delete(cls, name, path='/', domain=None, options=None):
        """ Returns a cookie that is deleted by browser.

            >>> c = HttpCookie.delete('abc')
            >>> c.HTTP_SET_COOKIE
            'abc=; expires=Sat, 01 Jan 2000 00:00:01 GMT; path=/'
        """
        return cls(name,
                expires='Sat, 01 Jan 2000 00:00:01 GMT',
                path=path, domain=domain, options=options)

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
