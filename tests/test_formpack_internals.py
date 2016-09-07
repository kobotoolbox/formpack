# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

from formpack import FormPack
from .fixtures import build_fixture


def test_fixture_has_translations():
    '''
    restauraunt_profile@v2 has two translations
    '''

    title, schemas, submissions = build_fixture('restaurant_profile')
    fp = FormPack(schemas, title)
    assert len(fp[1].translations) == 2
