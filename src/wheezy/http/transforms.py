
""" ``transforms`` module
"""

from wheezy.core.collections import gzip_iterator


def gzip_transform(compress_level=6, min_length=1024, vary=False):
    """ Allows gzip compression.

        ``compress_level`` - the compression level, between 1 and 9, where 1
        is the least compression (fastest) and 9 is the most (slowest)

        ``min_length`` - sets the minimum length, in bytes, of the
        first chunk in response that will be compressed. Responses
        shorter than this byte-length will not be compressed.

        ``vary`` - enables response header "Vary: Accept-Encoding".
    """
    def gzip(request, response):
        if response.skip_body:
            return response
        chunks = response.buffer
        if len(chunks) == 0 or len(chunks[0]) < min_length:
            return response
        # HTTP/1.1
        if request.environ['SERVER_PROTOCOL'][-1] == '1' and \
                (
                    # text/html, script, etc.
                    response.content_type[0] == 't'
                    or response.content_type[-2:] == 'pt'
                ) and 'gzip' in request.environ.get(
                    'HTTP_ACCEPT_ENCODING', ''):
            # text or script
            response.headers.append(('Content-Encoding', 'gzip'))
            response.buffer = tuple(gzip_iterator(chunks, compress_level))
            if vary:
                cache_policy = response.cache_policy
                if cache_policy:
                    if cache_policy.is_public:
                        cache_policy.vary('Accept-Encoding')
        return response
    return gzip


def response_transforms(*transforms):
    assert transforms

    def decorate(factory):
        if len(transforms) == 1:
            transform = transforms[0]

            def strategy(request, *args, **kwargs):
                return transform(
                    request,
                    factory(request, *args, **kwargs))
        else:
            def strategy(request, *args, **kwargs):
                response = factory(request, *args, **kwargs)
                for transform in transforms:
                    response = transform(request, response)
                return response
        return strategy
    return decorate
