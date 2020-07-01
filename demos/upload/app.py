"""
"""

from wheezy.http import (
    HTTPResponse,
    WSGIApplication,
    bad_request,
    bootstrap_http_defaults,
    not_found,
)


def welcome(request):
    response = HTTPResponse()
    response.write(
        """
<html>
<head>
<script src="//code.jquery.com/jquery-1.11.2.min.js" type="text/javascript">
</script>
</head>
<body>
<form enctype="multipart/form-data">
    <input name="myfile" type="file" />
    <input type="button" value="Upload" />
</form>
<p><progress></progress></p>
<script type="text/javascript">
$(':button').click(function() {
    var d = new FormData($('form')[0]);
    $.ajax({
        url: '/upload',
        type: 'POST',
        data: d,
        xhr: function() {
            var x = $.ajaxSettings.xhr();
            if (x.upload) {
                x.upload.addEventListener('progress', function(e) {
                    if(e.lengthComputable) {
                        $('progress').attr({value: e.loaded, max: e.total});
                    }
                },
                false);
            }
            return x;
        },
        cache: false,
        contentType: false,
        processData: false
    }).done(function(data) {
        $('body').append('<img src="/i/' + data + '"/>');
    });
});
</script>
</body>
</html>
    """
    )
    return response


def upload(request):
    f = request.files.get("myfile")
    if not f:
        return bad_request()
    f = f[0]
    images[f.filename] = (f.type, f.value)
    response = HTTPResponse("plain/text")
    response.write(f.filename)
    return response


def img(request):
    name = request.path[3:]
    i = images.get(name)
    if not i:
        return not_found()
    content_type, b = i
    response = HTTPResponse(content_type)
    response.write_bytes(b)
    return response


# region: samples

images = {}


# region: urls


def router_middleware(request, following):
    path = request.path
    if path == "/":
        return welcome(request)
    elif path == "/upload":
        return upload(request)
    elif path.startswith("/i/"):
        return img(request)
    return not_found()


# region: config

options = {}

# region: app

main = WSGIApplication(
    [bootstrap_http_defaults, lambda ignore: router_middleware], options
)


if __name__ == "__main__":
    from wsgiref.handlers import BaseHandler
    from wsgiref.simple_server import make_server

    try:
        print("Visit http://localhost:8080/")
        BaseHandler.http_version = "1.1"
        make_server("", 8080, main).serve_forever()
    except KeyboardInterrupt:
        pass
    print("\nThanks!")
