# coding: utf-8
import copy
from collections import OrderedDict

from formpack import FormPack
from formpack.constants import OR_OTHER_COLUMN as _OR_OTHER
from formpack.constants import UNTRANSLATED
from formpack.utils.expand_content import SCHEMA_VERSION
from formpack.utils.expand_content import _expand_tags
from formpack.utils.expand_content import _get_special_survey_cols
from formpack.utils.expand_content import expand_content, _expand_type_to_dict
from formpack.utils.flatten_content import flatten_content
from formpack.utils.string import orderable_with_none


def test_expand_selects_with_or_other():
    assert _expand_type_to_dict('select_one xx or other').get(_OR_OTHER
                                ) == True
    assert _expand_type_to_dict('select_one_or_other xx').get(_OR_OTHER
                                ) == True
    assert _expand_type_to_dict('select_multiple_or_other xx').get(_OR_OTHER
                                ) == True
    assert _expand_type_to_dict('select_multiple xx or other').get(_OR_OTHER
                                ) == True
    assert _expand_type_to_dict('select_one_or_other').get(_OR_OTHER
                                ) == True


def test_expand_select_one():
    s1 = {'survey': [{'type': 'select_one dogs'}]}
    expand_content(s1, in_place=True)
    assert s1['survey'][0]['type'] == 'select_one'
    assert s1['survey'][0]['select_from_list_name'] == 'dogs'


def test_expand_select_multiple_legacy():
    s1 = {'survey': [{'type': 'select all that apply from dogs'}]}
    expand_content(s1, in_place=True)
    assert s1['survey'][0]['type'] == 'select_multiple'
    assert s1['survey'][0]['select_from_list_name'] == 'dogs'

def test_expand_select_multiple_or_other():
    s1 = {'survey': [{'type': 'select_multiple dogs or_other'}]}
    expand_content(s1, in_place=True)
    assert s1['survey'][0]['type'] == 'select_multiple'
    assert s1['survey'][0]['select_from_list_name'] == 'dogs'
    assert s1['survey'][0][_OR_OTHER] == True


def test_expand_select_one_or_other():
    s1 = {'survey': [{'type': 'select_one dogs or_other'}]}
    expand_content(s1, in_place=True)
    assert s1['survey'][0]['type'] == 'select_one'
    assert s1['survey'][0]['select_from_list_name'] == 'dogs'


def test_expand_select_multiple():
    s1 = {'survey': [{'type': 'select_multiple dogs'}]}
    expand_content(s1, in_place=True)
    assert s1['survey'][0]['type'] == 'select_multiple'
    assert s1['survey'][0]['select_from_list_name'] == 'dogs'


def test_expand_media():
    s1 = {'survey': [{'type': 'note',
                      'media::image': 'ugh.jpg'}]}
    expand_content(s1, in_place=True)
    assert s1 == {'survey': [
            {
              'type': 'note',
              'media::image': ['ugh.jpg']
            }
        ],
        'translated': ['media::image'],
        'translations': [UNTRANSLATED],
        'schema': SCHEMA_VERSION,
        }
    flatten_content(s1, in_place=True)
    assert s1 == {'survey': [{
        'type': 'note',
        'media::image': 'ugh.jpg',
      }],
    }


def test_graceful_double_expand():
    s1 = {'survey': [{'type': 'note',
                      'label::English': 'english',
                      'hint::English': 'hint',
                      }]}
    content = expand_content(s1)
    assert content['translations'] == ['English']
    assert content['translated'] == ['hint', 'label']

    content = expand_content(content)
    assert content['translations'] == ['English']
    assert content['translated'] == ['hint', 'label']


def test_get_translated_cols():
    x1 = {'survey': [
          {'type': 'text', 'something::a': 'something-a', 'name': 'q1',
           'something_else': 'x'}
          ],
          'choices': [
          {'list_name': 'x', 'name': 'x1', 'something': 'something',
           'something_else::b': 'something_else::b'}
          ],
          'translations': [None]}
    expanded = expand_content(x1)
    assert expanded['translated'] == ['something', 'something_else']
    assert expanded['translations'] == [None, 'a', 'b']
    assert type(expanded['choices'][0]['something']) == list
    assert expanded['survey'][0]['something'] == [None, 'something-a', None]
    assert expanded['survey'][0]['something_else'] == ['x', None, None]
    assert expanded['choices'][0]['something'] == ['something', None, None]


def test_translated_label_hierarchy():
    survey = {'survey': [
            {
                'type': 'begin_group',
                'name': 'group',
                'label::English': 'Group',
                'label::Español': 'Grupo',
            },
            {
                'type': 'text',
                'name': 'question',
                'label::English': 'Question',
                'label::Español': 'Pregunta',
            },
            {
                'type': 'begin_repeat',
                'name': 'repeat',
                'label::English': 'Repeat',
                'label::Español': 'Repetición',
            },
            {
                'type': 'text',
                'name': 'repeated_question',
                'label::English': 'Repeated Question',
                'label::Español': 'Pregunta con repetición',
            },
            {'type': 'end_repeat'},
            {'type': 'end_group'},
        ]
    }
    schema = {'content': expand_content(survey), 'version': 1}
    version = FormPack([schema], 'title').versions[1]

    assert version.sections['title'].fields['question'].get_labels(
        hierarchy_in_labels=True, lang='English') == ['Group/Question']
    assert version.sections['title'].fields['question'].get_labels(
        hierarchy_in_labels=True, lang='Español') == ['Grupo/Pregunta']
    assert(
        version.sections['repeat'].fields['repeated_question'].get_labels(
            hierarchy_in_labels=True, lang='English') ==
                ['Group/Repeat/Repeated Question']
    )
    assert(
        version.sections['repeat'].fields['repeated_question'].get_labels(
            hierarchy_in_labels=True, lang='Español') ==
                ['Grupo/Repetición/Pregunta con repetición']
    )


def test_expand_translated_media():
    s1 = {'survey': [{'type': 'note',
                      'media::image::English': 'eng.jpg'
                      }]}
    expand_content(s1, in_place=True)
    assert s1 == {'survey': [
            {'type': 'note',
                'media::image': ['eng.jpg']
             }
        ],
        'translated': ['media::image'],
        'schema': SCHEMA_VERSION,
        'translations': ['English']}
    flatten_content(s1, in_place=True)
    assert s1 == {'survey': [{
        'type': 'note',
        'media::image::English': 'eng.jpg',
      }],
      }


def test_expand_translated_media_with_no_translated():
    s1 = {'survey': [{'type': 'note',
                      'media::image': 'nolang.jpg',
                      'media::image::English': 'eng.jpg',
                      }],
          'translations': ['English', UNTRANSLATED]}
    expand_content(s1, in_place=True)
    assert s1 == {'survey': [
            {'type': 'note',
                'media::image': ['eng.jpg', 'nolang.jpg']
             }
        ],
        'schema': SCHEMA_VERSION,
        'translated': ['media::image'],
        'translations': ['English', UNTRANSLATED]}
    flatten_content(s1, in_place=True)
    assert s1 == {'survey': [{
        'type': 'note',
        'media::image': 'nolang.jpg',
        'media::image::English': 'eng.jpg',
      }],
      }


def test_convert_select_objects():
    s1 = {'survey': [{'type': {'select_one': 'xyz'}},
                     {'type': {'select_one_or_other': 'xyz'}},
                     {'type': {'select_multiple': 'xyz'}}
                     ]}
    expand_content(s1, in_place=True)
    # print('_row', _row)
    _row = s1['survey'][0]
    assert _row['type'] == 'select_one'
    assert _row['select_from_list_name'] == 'xyz'

    _row = s1['survey'][1]
    assert _row['type'] == 'select_one'
    assert _row['select_from_list_name'] == 'xyz'

    _row = s1['survey'][2]
    assert _row['type'] == 'select_multiple'
    assert _row['select_from_list_name'] == 'xyz'


def test_expand_translated_choice_sheets():
    s1 = {'survey': [{'type': 'select_one yn',
                      'label::En': 'English Select1',
                      'label::Fr': 'French Select1',
                      }],
          'choices': [{'list_name': 'yn',
                       'name': 'y',
                       'label::En': 'En Y',
                       'label::Fr': 'Fr Y',
                       },
                      {
                       'list_name': 'yn',
                       'name': 'n',
                       'label::En': 'En N',
                       'label::Fr': 'Fr N',
                      }],
          'translations': ['En', 'Fr']}
    expand_content(s1, in_place=True)
    assert s1 == {'survey': [{
                  'type': 'select_one',
                  'select_from_list_name': 'yn',
                  'label': ['English Select1', 'French Select1'],
                  }],
                  'choices': [{'list_name': 'yn',
                               'name': 'y',
                               'label': ['En Y', 'Fr Y'],
                               },
                              {
                               'list_name': 'yn',
                               'name': 'n',
                               'label': ['En N', 'Fr N'],
                               }],
                  'schema': SCHEMA_VERSION,
                  'translated': ['label'],
                  'translations': ['En', 'Fr']}


def test_expand_hints_and_labels():
    """
    this was an edge case that triggered some weird behavior
    """
    s1 = {'survey': [{'type': 'select_one yn',
                      'label': 'null lang select1',
                      }],
          'choices': [{'list_name': 'yn',
                       'name': 'y',
                       'label': 'y',
                       'hint::En': 'En Y',
                      },
                      {
                       'list_name': 'yn',
                       'name': 'n',
                       'label': 'n',
                       'hint::En': 'En N',
                      }],
          }
    expand_content(s1, in_place=True)
    # Python3 raises a TypeError:
    # `'<' not supported between instances of 'NoneType' and 'str'`
    # when sorting a list with `None` values.
    # We need
    assert sorted(s1['translations'], key=orderable_with_none) == [None, 'En']


def test_ordered_dict_preserves_order():
    (special, t, tc) = _get_special_survey_cols({
            'survey': [
                OrderedDict([
                        ('label::A', 'A'),
                        ('label::B', 'B'),
                        ('label::C', 'C'),
                    ])
            ]
        })
    assert t == ['A', 'B', 'C']
    (special, t, tc) = _get_special_survey_cols({
            'survey': [
                OrderedDict([
                        ('label::C', 'C'),
                        ('label::B', 'B'),
                        ('label::A', 'A'),
                    ])
            ]
        })
    assert t == ['C', 'B', 'A']


def test_get_special_survey_cols():
    (special, t, tc) = _get_special_survey_cols(_s([
            'type',
            'media::image',
            'media::image::English',
            'label::Français',
            'label',
            'label::English',
            'media::audio::chinese',
            'label: Arabic',
            'label :: German',
            'label:English',
            'hint:English',
        ]))
    assert sorted(special.keys()) == sorted([
            'label',
            'media::image',
            'media::image::English',
            'label::Français',
            'label::English',
            'media::audio::chinese',
            'label: Arabic',
            'label :: German',
            'label:English',
            'hint:English',
        ])
    values = [special[key] for key in sorted(special.keys())]
    translations = sorted([x.get('translation') for x in values],
                          key=orderable_with_none)
    expected = sorted(['English', 'English', 'English', 'English',
                       'chinese', 'Arabic', 'German', 'Français',
                       UNTRANSLATED, UNTRANSLATED],
                      key=orderable_with_none)
    assert translations == expected


def test_not_special_cols():
    not_special = [
        'bind::orx:for',
        'bind:jr:constraintMsg',
        'bind:relevant',
        'body::accuracyThreshold',
        'body::accuracyTreshold',
        'body::acuracyThreshold',
        'body:accuracyThreshold',
    ]
    (not_special, _t, tc) = _get_special_survey_cols(_s(not_special))
    assert list(not_special) == []


def test_expand_constraint_message():
    s1 = {'survey': [{'type': 'integer',
                      'constraint': '. > 3',
                      'label::XX': 'X number',
                      'label::YY': 'Y number',
                      'constraint_message::XX': 'X: . > 3',
                      'constraint_message::YY': 'Y: . > 3',
                      }],
          'translated': ['constraint_message', 'label'],
          'translations': ['XX', 'YY']}
    s1_copy = copy.deepcopy(s1)
    x1 = {'survey': [{'type': 'integer',
                      'constraint': '. > 3',
                      'label': ['X number', 'Y number'],
                      'constraint_message': ['X: . > 3', 'Y: . > 3'],
                      }],
          'schema': SCHEMA_VERSION,
          'translated': ['constraint_message', 'label'],
          'translations': ['XX', 'YY'],
          }
    expand_content(s1, in_place=True)
    assert s1 == x1
    flatten_content(x1, in_place=True)
    s1_copy.pop('translated')
    s1_copy.pop('translations')
    assert x1 == s1_copy


def test_expand_translations():
    s1 = {'survey': [{'type': 'text',
                      'label::English': 'OK?',
                      'label::Français': 'OK!'}]}
    x1 = {'survey': [{'type': 'text',
                      'label': ['OK?', 'OK!']}],
          'schema': SCHEMA_VERSION,
          'translated': ['label'],
          'translations': ['English', 'Français']}
    expand_content(s1, in_place=True)
    assert s1 == x1
    flatten_content(s1, in_place=True)
    assert s1 == {'survey': [{'type': 'text',
                              'label::English': 'OK?',
                              'label::Français': 'OK!'}],
                  }


def test_expand_hxl_tags():
    s1 = {'survey': [{'type': 'text',
                      'hxl': '#tag+attr'}]}
    expand_content(s1, in_place=True)
    assert 'hxl' not in s1['survey'][0]
    assert s1['survey'][0]['tags'] == ['hxl:#tag', 'hxl:+attr']


def test_expand_tags_method():
    def _expand(tag_str, existing_tags=None):
        row = {'hxl': tag_str}
        if existing_tags:
            row['tags'] = existing_tags
        return sorted(_expand_tags(row, tag_cols_and_seps={'hxl': ''})['tags'])
    expected = sorted(['hxl:#tag1', 'hxl:+attr1', 'hxl:+attr2'])
    assert expected == _expand('#tag1+attr1+attr2')
    assert expected == _expand(' #tag1 +attr1 +attr2 ')
    assert expected == _expand(' #tag1 +attr1 ', ['hxl:+attr2'])
    test_underscores = ['#tag_underscore', '+attr_underscore']
    expected = ['hxl:' + x for x in test_underscores]
    assert expected == _expand(''.join(test_underscores))


def test_expand_translations_null_lang():
    s1 = {'survey': [{'type': 'text',
                      'label': 'NoLang',
                      'label::English': 'EnglishLang'}],
          'translated': ['label'],
          'translations': [UNTRANSLATED, 'English']}
    x1 = {'survey': [{'type': 'text',
                      'label': ['NoLang', 'EnglishLang']}],
          'schema': SCHEMA_VERSION,
          'translated': ['label'],
          'translations': [UNTRANSLATED, 'English']}
    s1_copy = copy.deepcopy(s1)
    expand_content(s1, in_place=True)
    assert s1.get('translations') == x1.get('translations')
    assert s1.get('translated') == ['label']
    assert s1.get('survey')[0] == x1.get('survey')[0]
    assert s1 == x1
    flatten_content(s1, in_place=True)
    s1_copy.pop('translated')
    s1_copy.pop('translations')
    assert s1 == s1_copy

def _s(rows):
    return {'survey': [dict([[key, 'x']]) for key in rows]}
