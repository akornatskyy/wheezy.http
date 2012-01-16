
""" ``transforms`` module
"""

from wheezy.core.collections import gzip_iterator


def gzip_transform(request, response):
    if response.skip_body:
        return response
    chunks = response.buffer
    if len(chunks) == 0 or len(chunks[0]) < 1024:
        return response
    if 'gzip' in request.environ.get('HTTP_ACCEPT_ENCODING', ''):
        # text or script
        if response.content_type[0] == 't' \
                or response.content_type[-2:] == 'pt':
            response.headers.append(('Content-Encoding', 'gzip'))
            cache_policy = response.cache
            if cache_policy:
                if cache_policy.is_public:
                    cache_policy.vary('Accept-Encoding')
            response.buffer = tuple(gzip_iterator(chunks))
    return response


def response_transforms(transform=None, transforms=None):
    def decorate(factory):
        if transform:
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
