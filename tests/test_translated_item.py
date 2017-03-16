# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)
import json
import pytest

from formpack.translated_item import TranslatedItem
from formpack.errors import TranslationError


def test_simple_translated():
    labels = TranslatedItem(['x', 'y'],
                            translations=['langx', 'langy'])
    expected = '{"langx": "x", "langy": "y"}'
    assert json.dumps(labels._translations) == expected


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
