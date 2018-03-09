# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)
from copy import deepcopy

from formpack import FormPack
from .fixtures import build_fixture


def test_fixture_has_translations():
    '''
    restauraunt_profile@v2 has two translations
    '''

    title, schemas, submissions = build_fixture('restaurant_profile')
    fp = FormPack(schemas, title)
    assert len(fp[1].translations) == 2


def test_to_dict():
    schema = build_fixture('restaurant_profile')[1][2]
    _copy = deepcopy(schema)
    fp = FormPack([schema], 'title')
    original_content = _copy['content']
    new_content = fp[0].to_dict()
    assert original_content == new_content


def test_to_xml():
    '''
    at the very least, version.to_xml() does not fail
    '''
    title, schemas, submissions = build_fixture('restaurant_profile')
    fp = FormPack(schemas, title)
    for version in fp.versions.keys():
        fp.versions[version].to_xml()
    # TODO: test output matches what is expected


def test_to_xml_fails_when_null_labels():
    # currently, this form will trigger a confusing error from pyxform:
    #  - Exception: (<type 'NoneType'>, None)

    # it occurs when a named translation has a <NoneType> value
    # (empty strings are OK)
    fp = FormPack({'content': {
                   'survey': [
                              {'type': 'note',
                               'name': 'n1',
                               'label': [None],
                               },
                              ],
                   'translations': ['NamedTranslation'],
                   'translated': ['label'],
                   }}, id_string='sdf')
    fp[0].to_xml()


def test_get_fields_for_versions_returns_unique_fields():
    '''
    As described in #127, `get_field_for_versions()` would return identical
    fields multiple times. This is was a failing test to reproduce that issue
    '''
    fp = FormPack(
        [{'content': {u'survey': [{u'name': u'hey', u'type': u'image'},
                                  {u'name': u'two', u'type': u'image'}]},
          'version': u'vRR7hH6SxTupvtvCqu7n5d'},
         {'content': {u'survey': [{u'name': u'one', u'type': u'image'},
                                  {u'name': u'two', u'type': u'image'}]},
          'version': u'vA8xs9JVi8aiSfypLgyYW2'},
         {'content': {u'survey': [{u'name': u'one', u'type': u'image'},
                                  {u'name': u'two', u'type': u'image'}]},
          'version': u'vNqgh8fJqyjFk6jgiCk4rn'}]
    )
    fields = fp.get_fields_for_versions(fp.versions)
    field_names = [field.name for field in fields]
    assert sorted(field_names) == [u'hey', u'one', u'two']


def test_get_fields_for_versions_returns_newest_of_fields_with_same_name():
    schemas = [
        {
            'version': 'v1',
            'content': {
                'survey': [
                    {
                        'name': 'constant_question_name',
                        'type': 'select_one choice',
                        'label': 'first version question label',
                        'hxl': '#first_version_hxl'
                    },
                ],
                'choices': [
                    {
                        'list_name': 'choice',
                        'name': 'constant_choice_name',
                        'label': 'first version choice label',
                    },
                ],
            }
        },
        {
            'version': 'v2',
            'content': {
                'survey': [
                    {
                        'name': 'constant_question_name',
                        'type': 'select_one choice',
                        'label': 'second version question label',
                        'hxl': '#second_version_hxl'
                    },
                ],
                'choices': [
                    {
                        'list_name': 'choice',
                        'name': 'constant_choice_name',
                        'label': 'second version choice label',
                    }
                ],
            }
        }
    ]
    fp = FormPack(schemas)
    fields = fp.get_fields_for_versions(fp.versions)
    # The first and only field returned should be the first field of the first
    # section of the last version
    assert fields[0] == fp[-1].sections.values()[0].fields.values()[0]


def test_get_fields_for_versions_returns_all_choices():
    schemas = [
        {
            'version': 'v1',
            'content': {
                'survey': [
                    {
                        'name': 'constant_question_name',
                        'type': 'select_one choice',
                        'label': 'first version question label',
                    },
                ],
                'choices': [
                    {
                        'list_name': 'choice',
                        'name': 'first_version_choice_name',
                        'label': 'first version choice label',
                    },
                ],
            }
        },
        {
            'version': 'v2',
            'content': {
                'survey': [
                    {
                        'name': 'constant_question_name',
                        'type': 'select_one choice',
                        'label': 'second version question label',
                    },
                ],
                'choices': [
                    {
                        'list_name': 'choice',
                        'name': 'second_version_choice_name',
                        'label': 'second version choice label',
                    }
                ],
            }
        }
    ]
    fp = FormPack(schemas)
    fields = fp.get_fields_for_versions(fp.versions)
    choice_names = fields[0].choice.options.keys()
    assert 'first_version_choice_name' in choice_names
    assert 'second_version_choice_name' in choice_names


def test_field_position_with_multiple_versions():
    title, schemas, submissions = build_fixture(
        'field_position_with_multiple_versions')
    fp = FormPack(schemas, title)

    all_fields = fp.get_fields_for_versions(fp.versions.keys())
    expected = [
        u'City',
        u'Firstname',
        u'Fullname',
        u'Lastname',
        u'Gender',
        u'Age',
    ]
    field_names = [field.name for field in all_fields]
    assert len(all_fields) == 6
    assert field_names == expected


def test_fields_for_versions_list_index_out_of_range():
    title, schemas, submissions = build_fixture(
        'fields_for_versions_list_index_out_of_range')
    fp = FormPack(schemas, title)
    all_fields = fp.get_fields_for_versions(fp.versions.keys())
    expected = [
        u'one',
        u'first_but_not_one',
        u'third',
    ]
    field_names = [field.name for field in all_fields]
    assert len(all_fields) == 3
    assert field_names == expected
