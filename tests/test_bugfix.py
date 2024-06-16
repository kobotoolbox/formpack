# coding: utf-8

from formpack.utils.bugfix import repair_file_column_content_in_place


def test_repair_file_column():
    content = {
        'schema': '1',
        'settings': {},
        'survey': [
            {
                '$kuid': 'qt1C9CFUj',
                '$qpath': 'interviewer_name_text',
                '$xpath': 'interviewer_name_text',
                'label': [
                    "Введіть ім'я співробітника:",
                    "Enter interviewer's name",
                ],
                'name': 'interviewer_name_text',
                'type': 'text',
            },
            {
                '$kuid': 'bHGP1YkRq',
                '$qpath': 'oblast',
                '$xpath': 'oblast',
                'label': ['Область', 'Oblast'],
                'media::file': [None, None, 'oblast.csv'],
                'name': 'oblast',
                'type': 'select_one_from_file',
            },
        ],
        'translated': ['label', 'media::file'],
        'translations': ['Ukrainian', 'English', None],
    }
    assert repair_file_column_content_in_place(content)
    assert content['survey'][1]['file'] == 'oblast.csv'
    assert content['translated'] == ['label']
    assert content['translations'] == ['Ukrainian', 'English']
