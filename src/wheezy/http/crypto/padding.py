
""" ``padding`` module.

    see http://www.di-mgt.com.au/cryptopad.html
"""

from wheezy.http.comp import b
from wheezy.http.comp import chr
from wheezy.http.comp import ord


def pad(s, block_size):
    """ Pad with zeroes except make the last byte equal to the
        number of padding bytes.

        The convention with this method is usually always to
        add a padding string, even if the original plaintext was
        already an exact multiple of 8 bytes.

        ``s`` - byte string.

        >>> from binascii import hexlify
        >>> from wheezy.http.comp import n
        >>> n(hexlify(pad(b('workbook'), 8)))
        '776f726b626f6f6b0000000000000008'
        >>> n(hexlify(pad(b('for'), 8)))
        '666f720000000005'
        >>> n(hexlify(pad(b(''), 8)))
        '0000000000000008'
    """
    n = len(s) % block_size
    if n > 0:
        n = block_size - n
    else:
        n = block_size
    return (chr(0) * (n - 1)).join((s, chr(n)))


def unpad(s, block_size):
    """ Strip right by the last byte number.

        ``s`` - byte string.

        >>> from binascii import unhexlify
        >>> from wheezy.http.comp import n
        >>> s = unhexlify(b('666f720000000005'))
        >>> n(unpad(s, 8))
        'for'
        >>> s = unhexlify(b('776f726b626f6f6b'))
        >>> n(unpad(s, 8))
        'workbook'
        >>> unpad('', 8)
        >>> unpad('abcd', 8)
    """
    n = len(s)
    if n == 0:
        return None
    n = n % block_size
    if n > 0:
        return None
    n = ord(s[-1])
    if n >= block_size:
        return s
    return s[:-n]
