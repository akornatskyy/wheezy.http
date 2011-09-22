
""" ``parser`` module.
"""

from cgi import FieldStorage

from wheezy.http.p2to3 import SimpleCookie
from wheezy.http.p2to3 import ntou
from wheezy.http.utils import HttpDict


MULTIPART_ENVIRON = {'REQUEST_METHOD': 'POST'}


def parse_multipart(fp, ctype, clength, encoding):
    """ Parse multipart/form-data request. Returns
        a tuple (form, files).

        >>> from wheezy.http import sample
        >>> from wheezy.http.p2to3 import ntob
        >>> fp, ctype, clength, encoding = sample.multipart()
        >>> form, files = parse_multipart(fp, ctype, clength,
        ...     encoding)
        >>> assert form['name'] == ntou('test', encoding)
        >>> f = files['file']
        >>> assert f.name == ntou('file', encoding)
        >>> assert f.filename == ntou('f.txt', encoding)
        >>> assert f.value == ntob('hello', encoding)
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
        name = f.name = ntou(f.name, encoding)
        if f.filename:
            f.filename = ntou(f.filename, encoding)
            files.getlist(name).append(f)
        else:
            form.getlist(name).append(ntou(f.value, encoding))
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
