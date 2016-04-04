# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)


import re
import unicodedata
import string
import random

try:
    unicode = unicode
    basestring = basestring
except NameError:  # Python 3
    unicode = str

str_types = (unicode, bytes)


def randstr(n):
    return ''.join(random.choice(string.ascii_lowercase + string.digits)
                   for _ in range(n))


# TODO: use a lib for that such as minibelt or ww
def normalize(string):
    r"""
        Returns a new string withou non ASCII characters, trying to replace
        them with their ASCII closest counter parts when possible.
        :Example:
            >>> normalize(u"H\xe9ll\xf8 W\xc3\xb6rld")
            'Hell World'
        This version use unicodedata and provide limited yet
        useful results.
    """
    string = unicodedata.normalize('NFKD', string).encode('ascii', 'ignore')
    return string.decode('ascii')


def slugify(string, separator=r'-'):
    r"""
    Slugify a unicode string using unicodedata to normalize the string.
    :Example:
        >>> slugify(u"H\xe9ll\xf8 W\xc3\xb6rld")
        'hell-world'
        >>> slugify("Bonjour, tout l'monde !", separator="_")
        'bonjour_tout_lmonde'
        >>> slugify("\tStuff with -- dashes and...   spaces   \n")
        'stuff-with-dashes-and-spaces'
    """

    string = normalize(string)
    string = re.sub(r'[^\w\s' + separator + ']', '', string, flags=re.U)
    string = string.strip().lower()
    return re.sub(r'[' + separator + '\s]+', separator, string, flags=re.U)
