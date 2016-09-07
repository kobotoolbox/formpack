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


def test_to_xml():
    '''
    at the very least, version.to_xml() does not fail
    '''
    title, schemas, submissions = build_fixture('restaurant_profile')
    fp = FormPack(schemas, title)
    for version in fp.versions.keys():
        fp.versions[version].to_xml()
    # TODO: test output matches what is expected
