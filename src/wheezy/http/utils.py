
""" ``utils`` module.
"""

from wheezy.http.p2to3 import STRING_EMPTY


class attribute(object):
    """ ``attribute`` decorator is intended to promote a
        function call to object attribute. This means the
        function is called once and replaced with
        returned value.

        >>> class A:
        ...     def __init__(self):
        ...         self.counter = 0
        ...     @attribute
        ...     def count(self):
        ...         self.counter += 1
        ...         return self.counter
        >>> a = A()
        >>> a.count
        1
        >>> a.count
        1
    """
    def __init__(self, f):
        self.f = f
        self.__module__ = f.__module__
        self.__name__ = f.__name__
        self.__doc__ = f.__doc__

    def __get__(self, obj, t=None):
        val = self.f(obj)
        setattr(obj, self.f.__name__, val)
        return val


class HttpDict(dict):
    """ ``HttpDict`` is a multi-value dictionary.

        >>> d = HttpDict({
        ...     'color': ['red', 'yellow']
        ... })

        Lookup by key return the last item from the list.

        >>> d['color']
        'yellow'

        A way to get whole list of items.

        >>> d.getlist('color')
        ['red', 'yellow']

        If ``key`` not found return empty string/list.

        >>> str(d['x1'])
        ''
        >>> d.getlist('x2')
        []
        >>> str(d['x2'])
        ''
    """

    def __init__(self, mapping=None):
        if mapping:
            super(HttpDict, self).__init__(mapping)

    def __getitem__(self, key):
        """ Returns the last value stored under given key. If key
            is not present it returns an empty string.
        """
        if key not in self:
            return STRING_EMPTY
        l = super(HttpDict, self).__getitem__(key)
        if l:
            return l[-1]
        else:
            return STRING_EMPTY

    def getlist(self, key):
        """ Returns a list of values for the given key.

            >>> d = HttpDict()
            >>> d.getlist('x').append('a')
            >>> d['x']
            'a'
        """
        if key not in self:
            l = []
            super(HttpDict, self).__setitem__(key, l)
            return l
        return super(HttpDict, self).__getitem__(key)
