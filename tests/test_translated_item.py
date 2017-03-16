# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)
import json
import pytest
from collections import OrderedDict

from formpack.translated_item import TranslatedItem
from formpack.errors import TranslationError


def test_simple_translated():
    t1 = TranslatedItem(['x', 'y'],
                        translations=['langx', 'langy'])
    expected = '{"langx": "x", "langy": "y"}'
    assert json.dumps(t1._translations) == expected

    # an OrderedDict can also be used to initialize a TranslatedItem
    t2 = TranslatedItem(OrderedDict([
            ('langx', 'x'),
            ('langy', 'y'),
        ]))
    assert json.dumps(t1._translations) == json.dumps(t2._translations)


def test_invalid_translateds():
    with pytest.raises(TranslationError):
        TranslatedItem(['two', 'translations'],
                       translations=['onelang'])

    ti = TranslatedItem(['one translation'],
                        # strict=False, by default
                        translations=['lang1', 'lang2'])
    assert ti._translations['lang2'] is None

    # this happens when a null translation is created on an
    # incomplete form. If we were to make this invalid, we should
    # enforce it at a different step
    ti = TranslatedItem([], translations=[None])
    assert json.dumps(ti._translations) == '{"null": null}'


def test_strict_translateds():
    with pytest.raises(TranslationError):
        TranslatedItem(['one translation'],
                       strict=True,
                       translations=['two', 'langs'])

    with pytest.raises(TranslationError):
        TranslatedItem(['two', 'translations'],
                       translations=['onelang'],
                       strict=True)
