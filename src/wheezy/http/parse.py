
""" ``parser`` module.
"""

from cgi import FieldStorage

from wheezy.core.collections import defaultdict
from wheezy.http.comp import SimpleCookie


MULTIPART_ENVIRON = {'REQUEST_METHOD': 'POST'}


def parse_multipart(fp, ctype, clength, encoding):
    """ Parse multipart/form-data request. Returns
        a tuple (form, files).

        >>> from wheezy.http import sample
        >>> from wheezy.http.comp import ntob
        >>> fp, ctype, clength, encoding = sample.multipart()
        >>> form, files = parse_multipart(fp, ctype, clength,
        ...     encoding)
        >>> form['name']
        ['test']
        >>> f = files['file']
        >>> f
        [FieldStorage('file', 'f.txt', 'hello')]
        >>> f = f[0]
        >>> f.name
        'file'
        >>> f.filename
        'f.txt'
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
    form = defaultdict(list)
    files = defaultdict(list)
    for f in fs.list:
        if f.filename:
            files[f.name].append(f)
        else:
            form[f.name].append(f.value)
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
