""" ``transforms`` module
"""

from wheezy.core.collections import gzip_iterator


def gzip_transform(compress_level=6, min_length=1024, vary=False):
    """Allows gzip compression.

    ``compress_level`` - the compression level, between 1 and 9, where 1
    is the least compression (fastest) and 9 is the most (slowest)

    ``min_length`` - sets the minimum length, in bytes, of the
    first chunk in response that will be compressed. Responses
    shorter than this byte-length will not be compressed.

    ``vary`` - enables response header "Vary: Accept-Encoding".
    """

    def gzip(request, response):
        chunks = response.buffer
        if not chunks or len(chunks[0]) < min_length:
            return response
        environ = request.environ
        if (
            "HTTP_ACCEPT_ENCODING" in environ
            and "gzip" in environ["HTTP_ACCEPT_ENCODING"]
        ):
            content_type = response.content_type
            if (
                "text" in content_type
                or "json" in content_type
                or "script" in content_type
            ):
                response.headers.append(("Content-Encoding", "gzip"))
                response.buffer = tuple(gzip_iterator(chunks, compress_level))
                if vary:
                    cache_policy = response.cache_policy
                    if cache_policy:
                        if cache_policy.is_public:
                            cache_policy.vary("Accept-Encoding")
        return response

    return gzip


def response_transforms(*transforms):
    """Applies several `transforms` at once."""
    assert transforms

    def decorate(factory):
        if len(transforms) == 1:
            transform = transforms[0]

            def single(request, *args, **kwargs):
                return transform(request, factory(request, *args, **kwargs))

            return single
        else:

            def multi(request, *args, **kwargs):
                response = factory(request, *args, **kwargs)
                for transform in transforms:
                    response = transform(request, response)
                return response

            return multi

    return decorate
