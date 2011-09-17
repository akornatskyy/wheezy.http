
""" ``parser`` module.
"""

from cgi import FieldStorage

try:
    from mod_python.util import parse_qs as pqs
except ImportError:  # pragma: nocover
    try:
        # Python 2.6+
        from urlparse import parse_qs as pqs
    except ImportError:  # pragma: nocover
        # Python 2.5, 2.4
        from cgi import parse_qs as pqs

from wheezy.http.p2to3 import SimpleCookie
from wheezy.http.p2to3 import ustr
from wheezy.http.utils import HttpDict


MULTIPART_ENVIRON = {'REQUEST_METHOD': 'POST'}


def parse_qs(qs):
    """ Parse query string and returns ``HttpDict``.
    """
    return HttpDict(pqs(qs, keep_blank_values=True))


def parse_multipart(fp, ctype, clength, encoding):
    """ Parse multipart/form-data request. Returns
        a tuple (form, files).

        >>> from wheezy.http import sample
        >>> mp = sample.multipart()
        >>> form, files = parse_multipart(*mp)
        >>> str(form['name'])
        'test'
        >>> f = files['file']
        >>> str(f.name)
        'file'
        >>> str(f.filename)
        'f.txt'
        >>> str(f.value.decode('utf-8'))
        'hello'
    """
    fs = FieldStorage(
        fp=fp,
        environ=MULTIPART_ENVIRON,
        headers={
            'content-type': ctype,
            'content-length': clength
        },
        keep_blank_values=True
    )
    form = HttpDict()
    files = HttpDict()
    for f in fs.list:
        name = f.name = ustr(f.name, encoding)
        if f.filename:
            f.filename = ustr(f.filename, encoding)
            files.getlist(name).append(f)
        else:
            form.getlist(name).append(ustr(f.value, encoding))
    return form, files


def parse_cookie(cookie):
    """ Parse cookie string and return a dictionary
        where key is a name of the cookie and value
        is cookie value.

        >>> parse_cookie('ID=1234;PREF=abc')
        {'PREF': 'abc', 'ID': '1234'}
    """
    c = SimpleCookie(cookie)
    cookies = {}
    for key in c.keys():
        cookies[key] = c[key].value
    return cookies
