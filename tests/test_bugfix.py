# coding: utf-8
from copy import deepcopy

from formpack.constants import UNTRANSLATED
from formpack.utils.bugfix import repair_media_column_content_in_place


def test_repair_file_column():
    content = {
        'schema': '1',
        'settings': {},
        'survey': [
            {
                'label': [
                    "Введіть ім'я співробітника:",
                    "Enter interviewer's name",
                ],
                'name': 'interviewer_name_text',
                'type': 'text',
            },
            {
                'label': ['Область', 'Oblast'],
                'media::file': [None, None, 'oblast.csv'],
                'name': 'oblast',
                'type': 'select_one_from_file',
            },
        ],
        'translated': ['label', 'media::file'],
        'translations': ['Ukrainian', 'English', None],
    }
    assert repair_media_column_content_in_place(content)
    assert content['survey'][1]['file'] == 'oblast.csv'
    assert content['translated'] == ['label']
    assert content['translations'] == ['Ukrainian', 'English']


def test_repair_media_image_none_plus_value_and_translations():
    content = {
        'schema': '1',
        'settings': {},
        'survey': [
            {
                'label': ['Código de participante'],
                'name': 'repro_media',
                'type': 'text',
                'media::image': [None, 'repro_test.png'],
                '$xpath': 'repro_media',
            }
        ],
        'translated': ['label', 'media::image'],
        'translations': [UNTRANSLATED, 'big-image'],
    }
    content_copy = deepcopy(content)

    assert repair_media_column_content_in_place(content_copy) is True
    assert 'image' in content_copy['survey'][0]
    assert content_copy['survey'][0]['image'] == 'repro_test.png'

    # 'media::image' token must be removed from translated
    assert 'media::image' not in content_copy['translated']
    assert 'label' in content_copy['translated']
    resulting_translations = content_copy['translations']
    assert resulting_translations in (['big-image'], [UNTRANSLATED], [None])
