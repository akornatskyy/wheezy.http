
""" ``crypto`` module.
"""

from base64 import b64decode
from base64 import b64encode
from hmac import new as hmac_new
from os import urandom
from struct import pack
from struct import unpack
from time import time

from wheezy.http import config
from wheezy.http.comp import aes128
from wheezy.http.comp import b
from wheezy.http.comp import block_size
from wheezy.http.comp import bton
from wheezy.http.comp import decrypt
from wheezy.http.comp import digest_size
from wheezy.http.comp import encrypt
from wheezy.http.comp import ntob
from wheezy.http.comp import sha1
from wheezy.http.crypto.padding import pad
from wheezy.http.crypto.padding import unpad


EPOCH = 1317212745
BASE64_ALTCHARS = b('-~')


def ensure_strong_key(key):
    """ Translates a given key to a computed strong key of length
        320 bit suitable for encryption.

        >>> from wheezy.http.comp import n
        >>> k = ensure_strong_key(b(''))
        >>> len(k)
        40
        >>> n(b64encode(k))
        '+9sdGxiqbAgyS31ktx+3Y3BpDh1fA7dyIanFu+fzE/Lc5EaX+NQGsA=='
        >>> n(b64encode(ensure_strong_key(b('abc'))))
        'zEfjwKoMKYRFRHbQYRCMCxEBd66sLMHe/H6umZFFQMixhLcp8jfwGQ=='
    """
    hmac = hmac_new(key, digestmod=sha1)
    key = hmac.digest()
    hmac.update(key)
    return key + hmac.digest()


class Ticket:
    """ Protects sensitive information (e.g. user id). Default policy
        applies verification and encryption. Verification is provided
        by ``hmac`` initialized with ``sha1`` digestmod. Encryption
        is provided is available, by default it attempts to use AES
        cypher.

        >>> t = Ticket()
        >>> x = t.encode('hello')
        >>> t.decode(x)
        'hello'

        If cypher is not available verification is still applied.

        >>> t = Ticket(cypher=None)
        >>> x = t.encode('hello')
        >>> t.decode(x)
        'hello'
    """

    cypher = None

    def __init__(self, max_age=900, salt='', digestmod=None,
            cypher=aes128):
        self.max_age = max_age
        digestmod = digestmod or sha1
        key = b(salt + config.CRYPTO_VALIDATION_KEY)
        key = ensure_strong_key(key)
        self.hmac = hmac_new(key, digestmod=digestmod)
        self.digest_size = digest_size(digestmod)
        if cypher:
            key = b(salt + config.CRYPTO_ENCRYPTION_KEY)
            key = ensure_strong_key(key)
            self.cypher = cypher(key)
            self.block_size = block_size(self.cypher())

    def encode(self, value, encoding='utf-8'):
        """ Encode ``value`` accoring to ticket policy.
        """
        value = ntob(value, encoding)
        expires = pack('<i', self.timestamp())
        noise = urandom(12)
        value = b('').join((
            noise[:4],
            expires,
            noise[4:8],
            value,
            noise[8:]
        ))
        cypher = self.cypher
        if cypher:
            cypher = cypher()
            value = encrypt(cypher, pad(value, self.block_size))
        return b64encode(self.sign(value) + value, BASE64_ALTCHARS)

    def decode(self, value, encoding='utf-8'):
        """ Decode ``value`` according to ticket policy.
        """
        if len(value) < 56:
            return None
        value = b64decode(value, BASE64_ALTCHARS)
        signature = value[:self.digest_size]
        value = value[self.digest_size:]
        if signature != self.sign(value):
            return None
        cypher = self.cypher
        if cypher:
            cypher = cypher()
            value = unpad(decrypt(cypher, value), self.block_size)
        expires, value = value[4:8], value[12:-4]
        if unpack('<i', expires)[0] < self.timestamp():
            return None
        return bton(value, encoding)

    def timestamp(self):
        return int(time()) - EPOCH + self.max_age

    def sign(self, value):
        h = self.hmac.copy()
        h.update(value)
        return h.digest()
