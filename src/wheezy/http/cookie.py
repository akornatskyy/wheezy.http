
""" ``cookie`` module.
"""

from datetime import datetime
from time import time

from wheezy.core.datetime import format_http_datetime

from wheezy.http.comp import n


class HTTPCookie(object):
    """ HTTP Cookie
        http://www.ietf.org/rfc/rfc2109.txt

        ``domain``, ``secure`` and ``httponly`` are
        taken from ``config`` if not set.

        >>> from wheezy.http.config import bootstrap_http_defaults
        >>> options = {}
        >>> bootstrap_http_defaults(options)
        >>> c = HTTPCookie('a', options=options)
        >>> c.http_set_cookie('utf-8')
        ('Set-Cookie', 'a=; path=/')

        Value:

        >>> c = HTTPCookie('a', value='123', options=options)
        >>> c.http_set_cookie('utf-8')
        ('Set-Cookie', 'a=123; path=/')

        Domain:

        >>> c = HTTPCookie('a', value='123',
        ...         domain='.abc.com', options=options)
        >>> c.http_set_cookie('utf-8')
        ('Set-Cookie', 'a=123; domain=.abc.com; path=/')

        Expires:

        >>> from wheezy.core.datetime import UTC
        >>> when = datetime(2011, 9, 26, 19, 34, tzinfo=UTC)
        >>> c = HTTPCookie('a', expires=when, options=options)
        >>> c.http_set_cookie('utf-8')
        ('Set-Cookie', 'a=; expires=Mon, 26 Sep 2011 19:34:00 GMT; path=/')

        Max Age:

        >>> from datetime import timedelta
        >>> c = HTTPCookie('a', max_age=1200, options=options)
        >>> now = datetime.utcnow()
        >>> assert c.expires > now
        >>> assert c.expires <= now + timedelta(seconds=1200)

        Path:

        >>> c = HTTPCookie('a', path=None, options=options)
        >>> c.http_set_cookie('utf-8')
        ('Set-Cookie', 'a=')

        Secure:

        >>> c = HTTPCookie('a', value='123', secure=True, options=options)
        >>> c.http_set_cookie('utf-8')
        ('Set-Cookie', 'a=123; path=/; secure')

        HTTP Only:

        >>> c = HTTPCookie('a', value='123', httponly=True, options=options)
        >>> c.http_set_cookie('utf-8')
        ('Set-Cookie', 'a=123; path=/; httponly')

        All:

        >>> c = HTTPCookie('a', value='123', expires=when,
        ...     path='abc', domain='.abc.com',
        ...     secure=True, httponly=True)
        >>> c.http_set_cookie('utf-8') # doctest: +NORMALIZE_WHITESPACE
        ('Set-Cookie', 'a=123; domain=.abc.com;
        expires=Mon, 26 Sep 2011 19:34:00 GMT;
        path=abc; secure; httponly')
    """
    __slots__ = ('name', 'value', 'path', 'expires',
                 'domain', 'secure', 'httponly')

    def __init__(self, name, value=None, path='/',
                 expires=None, max_age=None,
                 domain=None, secure=None, httponly=None,
                 options=None):
        self.name = name
        self.value = value
        self.path = path
        if max_age is None:
            self.expires = expires
        else:
            self.expires = datetime.utcfromtimestamp(time() + max_age)
        if domain is None:
            self.domain = options['HTTP_COOKIE_DOMAIN']
        else:
            self.domain = domain
        if secure is None:
            self.secure = options['HTTP_COOKIE_SECURE']
        else:
            self.secure = secure
        if httponly is None:
            self.httponly = options['HTTP_COOKIE_HTTPONLY']
        else:
            self.httponly = httponly

    @classmethod
    def delete(cls, name, path='/', domain=None, options=None):
        """ Returns a cookie that is deleted by browser.

            >>> from wheezy.http.config import bootstrap_http_defaults
            >>> options = {}
            >>> bootstrap_http_defaults(options)
            >>> c = HTTPCookie.delete('abc', options=options)
            >>> c.http_set_cookie('utf-8') # doctest: +NORMALIZE_WHITESPACE
            ('Set-Cookie', 'abc=;
                    expires=Sat, 01 Jan 2000 00:00:01 GMT; path=/')
        """
        return cls(name,
                   expires='Sat, 01 Jan 2000 00:00:01 GMT',
                   path=path, domain=domain, options=options)

    def http_set_cookie(self, encoding):
        directives = []
        append = directives.append
        append(self.name + '=')
        if self.value:
            append(n(self.value, encoding))
        if self.domain:
            append('; domain=' + self.domain)
        if self.expires:
            append('; expires=' + format_http_datetime(self.expires))
        if self.path:
            append('; path=' + self.path)
        if self.secure:
            append('; secure')
        if self.httponly:
            append('; httponly')
        return ('Set-Cookie', ''.join(directives))
