""" ``streaming`` module.
"""

from time import sleep

from wheezy.http import (
    HTTPResponse,
    WSGIApplication,
    bootstrap_http_defaults,
    not_found,
)


class HTTPTextStreamingResponse(object):
    status_code = 200
    cache_profile = None

    def __init__(
        self,
        iterable,
        content_type="text/html; charset=UTF-8",
        encoding="UTF-8",
    ):
        self.iterable = iterable
        self.encoding = encoding
        self.headers = [
            ("Content-Type", content_type),
            ("Cache-Control", "private"),
        ]

    def __call__(self, start_response):
        """WSGI call processing."""
        start_response("200 OK", self.headers)
        return (chunk.encode(self.encoding) for chunk in self.iterable)


def hello(request):
    def generate():
        yield "START"
        for _ in range(5):
            yield "Hello World!"
            sleep(2)

    return HTTPTextStreamingResponse(generate())


def welcome(request):
    response = HTTPResponse()
    response.write(
        """
<html>
<head>
<script src="//code.jquery.com/jquery-1.11.0.min.js" type="text/javascript">
</script>
</head>
<body>
<span id="c"></span>
<script type="text/javascript">
(function poll(){
    var l = 0;
    $.ajax({
        url: '/hello',
        xhrFields: {
            onprogress: function(e) {
                var response = e.currentTarget.response;
                if (l == 0 && response.indexOf('START') == 0) {
                    $('#c').text('');
                    l = 5;
                }
                $('#c').append(response.substring(l) + ' ');
                l = response.length;
            }
        }
    })
    .done(poll);
})();
</script>
</body>
</html>
    """
    )
    return response


def router_middleware(request, following):
    path = request.path
    if path == "/":
        response = welcome(request)
    elif path == "/hello":
        response = hello(request)
    else:
        response = not_found()
    return response


options = {}
main = WSGIApplication(
    [bootstrap_http_defaults, lambda ignore: router_middleware], options
)


if __name__ == "__main__":
    from wsgiref.simple_server import make_server

    try:
        print("Visit http://localhost:8080/")
        make_server("", 8080, main).serve_forever()
    except KeyboardInterrupt:
        pass
    print("\nThanks!")
