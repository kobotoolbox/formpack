# coding: utf-8

from __future__ import (unicode_literals, print_function, absolute_import,
                        division)

from collections import OrderedDict
from .errors import TranslationError


class TranslatedItem(object):
    def __init__(self, values=[], translations=[], strict=False, context=''):
        if isinstance(values, OrderedDict):
            translations = values.keys()
            values = values.values()

        if len(translations) == 1 and translations[0] is None and \
                len(values) == 0:
            values = [None]
        if len(values) > len(translations):
            raise TranslationError('String count exceeds translation count. {}'
                                   .format(context))
        if strict and len(values) < len(translations):
            raise TranslationError('Translation count does not match'
                                   ' string count. {}'.format(context))
        else:
            while len(values) < len(translations):
                values = values + [None]

        self._translations = OrderedDict(zip(translations, values))

    def __getitem__(self, index):
        return self._translations.values()[index]

    def get(self, key, default=None):
        return self._translations.get(key, default)
