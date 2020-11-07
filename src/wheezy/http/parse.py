""" ``parser`` module.
"""

from cgi import FieldStorage
from urllib.parse import unquote

MULTIPART_ENVIRON = {"REQUEST_METHOD": "POST"}


def parse_qs(qs):
    params = {}
    for field in qs.split("&"):
        r = field.partition("=")
        k = r[0]
        v = r[2]
        if "+" in k:
            k = k.replace("+", " ")
        if "%" in k:
            k = unquote(k)
        if "+" in v:
            v = v.replace("+", " ")
        if k in params:
            params[k].append("%" in v and unquote(v) or v)
        else:
            if "," in v:
                params[k] = [
                    ("%" in v and unquote(x) or x) for x in v.split(",")
                ]
            else:
                params[k] = ["%" in v and unquote(v) or v]
    return params


def parse_multipart(fp, ctype, clength, encoding):
    """Parse multipart/form-data request. Returns
    a tuple (form, files).
    """
    fs = FieldStorage(
        fp=fp,
        environ=MULTIPART_ENVIRON,
        headers={"content-type": ctype, "content-length": clength},
        keep_blank_values=True,
    )
    form = {}
    files = {}
    for f in fs.list:
        if f.filename:
            files.setdefault(f.name, []).append(f)
        else:
            form.setdefault(f.name, []).append(f.value)
    return form, files


def parse_cookie(cookie):
    """Parse cookie string and return a dictionary
    where key is a name of the cookie and value
    is cookie value.
    """
    return (
        cookie
        and dict([pair.split("=", 1) for pair in cookie.split("; ")])
        or {}
    )
