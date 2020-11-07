""" ``request`` module.
"""
from json import loads as json_loads

from wheezy.core.descriptors import attribute
from wheezy.core.url import UrlParts

from wheezy.http.parse import parse_cookie, parse_multipart, parse_qs


class HTTPRequest(object):
    """Represent HTTP request. ``environ`` variables
    are accessable via attributes.
    """

    def __init__(self, environ, encoding, options):
        self.environ = environ
        self.encoding = encoding
        self.options = options
        self.method = environ["REQUEST_METHOD"]

    @attribute
    def host(self):
        host = self.environ["HTTP_HOST"]
        if "," in host:
            host = host.rsplit(",", 1)[-1].strip()
        return host

    @attribute
    def remote_addr(self):
        addr = self.environ["REMOTE_ADDR"]
        if "," in addr:
            addr = addr.split(",", 1)[0].strip()
        return addr

    @attribute
    def root_path(self):
        return self.environ["SCRIPT_NAME"] + "/"

    @attribute
    def path(self):
        return self.environ["SCRIPT_NAME"] + self.environ["PATH_INFO"]

    @attribute
    def query(self):
        return parse_qs(self.environ["QUERY_STRING"])

    def get_param(self, name):
        p = self.query.get(name)
        return p and p[-1]

    @attribute
    def form(self):
        form, self.files = self.load_body()
        return form

    @attribute
    def files(self):
        self.form, files = self.load_body()
        return files

    @attribute
    def cookies(self):
        if "HTTP_COOKIE" in self.environ:
            return parse_cookie(self.environ["HTTP_COOKIE"])
        else:
            return {}

    @attribute
    def ajax(self):
        if "HTTP_X_REQUESTED_WITH" in self.environ:
            return self.environ["HTTP_X_REQUESTED_WITH"] == "XMLHttpRequest"
        else:
            return False

    @attribute
    def secure(self):
        return self.environ["wsgi.url_scheme"] == "https"

    @attribute
    def scheme(self):
        return self.environ["wsgi.url_scheme"]

    @attribute
    def urlparts(self):
        return UrlParts(
            (
                self.scheme,
                self.host,
                self.path,
                self.environ["QUERY_STRING"],
                None,
            )
        )

    @attribute
    def content_type(self):
        return self.environ["CONTENT_TYPE"]

    @attribute
    def content_length(self):
        return int(self.environ["CONTENT_LENGTH"])

    @attribute
    def stream(self):
        return self.environ["wsgi.input"]

    def load_body(self):
        """Load http request body and returns
        form data and files.
        """
        environ = self.environ
        cl = environ["CONTENT_LENGTH"]
        icl = int(cl)
        if icl > self.options["MAX_CONTENT_LENGTH"]:
            raise ValueError("Maximum content length exceeded")
        fp = environ["wsgi.input"]
        ct = environ["CONTENT_TYPE"]
        # application/x-www-form-urlencoded
        if "/x" in ct:
            return parse_qs(fp.read(icl).decode(self.encoding)), None
        # application/json
        elif "/j" in ct:
            return json_loads(fp.read(icl).decode(self.encoding)), None
        # multipart/form-data
        elif ct.startswith("m"):
            return parse_multipart(fp, ct, cl, self.encoding)
        else:
            return None, None
