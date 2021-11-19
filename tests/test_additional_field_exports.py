# coding: utf-8
from formpack import FormPack
from .fixtures import build_fixture

def tests_additional_field_exports():
    title, schemas, submissions, analysis_form = build_fixture('analysis_form')
    pack = FormPack(schemas, title=title)
    pack.extend_survey(analysis_form)

    options = {'include_analysis_fields': True, 'versions': 'v1'}
    export = pack.export(**options)
    values = export.to_dict(submissions)
    main_export_sheet = values['Simple Clerk Interaction']

    assert 3 == len(main_export_sheet['data'])
    assert main_export_sheet['fields'] == [
        'record_a_note',
        'record_a_note_transcription_acme_1_speech2text',
        'record_a_note_acme_timestamp',
        'name_of_clerk',
        'name_of_clerk_comment',
    ]
    response0 = main_export_sheet['data'][0]
    assert response0 == [
        'clerk_interaction_1.mp3',
        'Hello how may I help you?',
        '2021-11-01Z',
        'John',
        'Sounds like an interesting person',
    ]

def tests_additional_field_exports_repeat_groups():
    title, schemas, submissions, analysis_form = build_fixture(
        'analysis_form_repeat_groups'
    )
    pack = FormPack(schemas, title=title)
    pack.extend_survey(analysis_form)

    options = {
        'include_analysis_fields': True,
        'versions': 'v1',
    }
    export = pack.export(**options)
    values = export.to_dict(submissions)
    assert [
        'Clerk Interaction Repeat Groups',
        'stores',
        'record_interactions',
        'record_ambient_noises',
    ] == list(values.keys())

    main_export_sheet = values['Clerk Interaction Repeat Groups']
    assert ['enumerator_name', '_index'] == main_export_sheet['fields']
    main_response0 = main_export_sheet['data'][0]
    assert 'John Doe' == main_response0[0]

    repeat_sheet_0 = values['stores']
    assert 'Costco' == repeat_sheet_0['data'][0][0]

    repeat_sheet_1 = values['record_interactions']
    assert [
        'record_a_note',
        'record_a_note_transcription_acme_1_speech2text',
    ] == repeat_sheet_1['fields'][:2]
    assert 3 == len(repeat_sheet_1['data'])
    repeat_data_response_1 = [res[:2] for res in repeat_sheet_1['data']]
    repeat_data_expected_1 = [
        [
            'clerk_interaction_1.mp3',
            'Hello how may I help you?',
        ],
        [
            'clerk_interaction_2.mp3',
            '',
        ],
        [
            'clerk_interaction_3.mp3',
            'Thank you for your business',
        ],
    ]
    assert repeat_data_expected_1 == repeat_data_response_1

    repeat_sheet_2 = values['record_ambient_noises']
    assert [
        'record_a_noise',
        'record_a_noise_comment_on_noise_level',
    ] == repeat_sheet_2['fields'][:2]
    assert 2 == len(repeat_sheet_2['data'])
    repeat_data_response_2 = [res[:2] for res in repeat_sheet_2['data']]
    repeat_data_expected_2 = [
        [
            'noise_1.mp3',
            "Lot's of noise",
        ],
        [
            'noise_2.mp3',
            'Quiet',
        ],
    ]
    assert repeat_data_expected_2 == repeat_data_response_2

def tests_additional_field_exports_advanced():
    title, schemas, submissions, analysis_form = build_fixture(
        'analysis_form_advanced'
    )
    pack = FormPack(schemas, title=title)
    pack.extend_survey(analysis_form)

    options = {
        'include_analysis_fields': True,
        'versions': 'v1',
        'multiple_select': 'both',
    }
    export = pack.export(**options)
    values = export.to_dict(submissions)
    main_export_sheet = values['Advanced Clerk Interaction']

    assert 3 == len(main_export_sheet['data'])
    assert main_export_sheet['fields'] == [
        'record_a_note',
        'record_a_note_transcription_acme_1_speech2text',
        'record_a_note_tone_of_voice',
        'record_a_note_tone_of_voice/anxious',
        'record_a_note_tone_of_voice/excited',
        'record_a_note_tone_of_voice/confused',
        'goods_sold',
        'goods_sold/chocolate',
        'goods_sold/fruit',
        'goods_sold/pasta',
        'goods_sold_comment',
        'goods_sold_rating',
    ]
    assert main_export_sheet['data'] == [
        [
            'clerk_interaction_1.mp3',
            'Hello how may I help you?',
            'excited confused',
            '0',
            '1',
            '1',
            'chocolate',
            '1',
            '0',
            '0',
            'Not much diversity',
            '3',
        ],
        [
            'clerk_interaction_2.mp3',
            'Thank you for your business',
            'anxious excited',
            '1',
            '1',
            '0',
            'chocolate fruit pasta',
            '1',
            '1',
            '1',
            '',
            '2',
        ],
        [
            'clerk_interaction_3.mp3',
            '',
            '',
            '',
            '',
            '',
            'pasta',
            '0',
            '0',
            '1',
            '',
            '3',
        ],
    ]

    options['multiple_select'] = 'details'
    export = pack.export(**options)
    values = export.to_dict(submissions)
    main_export_sheet = values['Advanced Clerk Interaction']

    assert main_export_sheet['fields'] == [
        'record_a_note',
        'record_a_note_transcription_acme_1_speech2text',
        'record_a_note_tone_of_voice/anxious',
        'record_a_note_tone_of_voice/excited',
        'record_a_note_tone_of_voice/confused',
        'goods_sold/chocolate',
        'goods_sold/fruit',
        'goods_sold/pasta',
        'goods_sold_comment',
        'goods_sold_rating',
    ]
    assert main_export_sheet['data'] == [
        [
            'clerk_interaction_1.mp3',
            'Hello how may I help you?',
            '0',
            '1',
            '1',
            '1',
            '0',
            '0',
            'Not much diversity',
            '3',
        ],
        [
            'clerk_interaction_2.mp3',
            'Thank you for your business',
            '1',
            '1',
            '0',
            '1',
            '1',
            '1',
            '',
            '2',
        ],
        [
            'clerk_interaction_3.mp3',
            '',
            '',
            '',
            '',
            '0',
            '0',
            '1',
            '',
            '3',
        ],
    ]

    options['multiple_select'] = 'summary'
    export = pack.export(**options)
    values = export.to_dict(submissions)
    main_export_sheet = values['Advanced Clerk Interaction']

    assert main_export_sheet['fields'] == [
        'record_a_note',
        'record_a_note_transcription_acme_1_speech2text',
        'record_a_note_tone_of_voice',
        'goods_sold',
        'goods_sold_comment',
        'goods_sold_rating',
    ]
    assert main_export_sheet['data'] == [
        [
            'clerk_interaction_1.mp3',
            'Hello how may I help you?',
            'excited confused',
            'chocolate',
            'Not much diversity',
            '3',
        ],
        [
            'clerk_interaction_2.mp3',
            'Thank you for your business',
            'anxious excited',
            'chocolate fruit pasta',
            '',
            '2',
        ],
        [
            'clerk_interaction_3.mp3',
            '',
            '',
            'pasta',
            '',
            '3',
        ],
    ]

def tests_additional_field_exports_v2():
    title, schemas, submissions, analysis_form = build_fixture('analysis_form')
    pack = FormPack(schemas, title=title)
    pack.extend_survey(analysis_form)

    options = {'include_analysis_fields': True, 'versions': 'v2'}
    export = pack.export(**options)
    values = export.to_dict(submissions)
    main_export_sheet = values['Simple Clerk Interaction']

    assert 3 == len(main_export_sheet['data'])
    assert main_export_sheet['fields'] == [
        'record_a_note',
        'record_a_note_transcription_acme_1_speech2text',
        'record_a_note_acme_timestamp',
        'name_of_shop',
        'name_of_shop_comment',
    ]
    response0 = main_export_sheet['data'][0]
    assert response0 == [
        'clerk_interaction_4.mp3',
        'Hello how may I help you?',
        '2021-11-01Z',
        'Save On',
        'Pretty cliche',
    ]

def tests_additional_field_exports_all_versions():
    title, schemas, submissions, analysis_form = build_fixture('analysis_form')
    pack = FormPack(schemas, title=title)
    pack.extend_survey(analysis_form)

    options = {'include_analysis_fields': True, 'versions': pack.versions}
    export = pack.export(**options)
    values = export.to_dict(submissions)
    main_export_sheet = values['Simple Clerk Interaction']

    assert 6 == len(main_export_sheet['data'])
    assert main_export_sheet['fields'] == [
        'record_a_note',
        'record_a_note_transcription_acme_1_speech2text',
        'record_a_note_acme_timestamp',
        'name_of_shop',
        'name_of_shop_comment',
        'name_of_clerk',
        'name_of_clerk_comment',
    ]
    response0 = main_export_sheet['data'][0]
    assert response0 == [
        'clerk_interaction_1.mp3',
        'Hello how may I help you?',
        '2021-11-01Z',
        '',
        '',
        'John',
        'Sounds like an interesting person',
    ]
    response3 = main_export_sheet['data'][3]
    assert response3 == [
        'clerk_interaction_4.mp3',
        'Hello how may I help you?',
        '2021-11-01Z',
        'Save On',
        'Pretty cliche',
        '',
        '',
    ]

def tests_additional_field_exports_all_versions_exclude_fields():
    title, schemas, submissions, analysis_form = build_fixture('analysis_form')
    pack = FormPack(schemas, title=title)
    pack.extend_survey(analysis_form)

    options = {'versions': pack.versions}
    export = pack.export(**options)
    values = export.to_dict(submissions)
    main_export_sheet = values['Simple Clerk Interaction']

    assert 6 == len(main_export_sheet['data'])
    assert main_export_sheet['fields'] == [
        'record_a_note',
        'name_of_shop',
        'name_of_clerk',
    ]
    response0 = main_export_sheet['data'][0]
    assert response0 == [
        'clerk_interaction_1.mp3',
        '',
        'John',
    ]
    response3 = main_export_sheet['data'][3]
    assert response3 == [
        'clerk_interaction_4.mp3',
        'Save On',
        '',
    ]

def tests_additional_field_exports_all_versions_langs():
    title, schemas, submissions, analysis_form = build_fixture('analysis_form')
    pack = FormPack(schemas, title=title)
    pack.extend_survey(analysis_form)

    options = {
        'include_analysis_fields': True,
        'versions': pack.versions,
        'lang': 'English (en)',
    }
    export = pack.export(**options)
    values = export.to_dict(submissions)
    main_export_sheet = values['Simple Clerk Interaction']

    assert main_export_sheet['fields'] == [
        'Record a clerk saying something',
        ': ACME Transcription',
        'Transcription Timestamp',
        "What is the shop's name?",
        'Comment on the name of the shop',
        "What is the clerk's name?",
        'Comment on the name of the clerk',
    ]

    options['lang'] = 'Esperanto (es)'
    export = pack.export(**options)
    values = export.to_dict(submissions)
    main_export_sheet = values['Simple Clerk Interaction']

    assert main_export_sheet['fields'] == [
        'Registri oficiston dirantan ion',
        'record_a_note_transcription_acme_1_speech2text',
        'record_a_note_acme_timestamp',
        'Kio estas la nomo de la butiko?',
        'name_of_shop_comment',
        'name_of_clerk',
        'name_of_clerk_comment',
    ]

    options['lang'] = None
    export = pack.export(**options)
    values = export.to_dict(submissions)
    main_export_sheet = values['Simple Clerk Interaction']

    assert main_export_sheet['fields'] == [
        'record_a_note',
        'record_a_note_transcription_acme_1_speech2text',
        'record_a_note_acme_timestamp',
        'name_of_shop',
        'name_of_shop_comment',
        'name_of_clerk',
        'name_of_clerk_comment',
    ]

def test_simple_report_with_analysis_form():

    title, schemas, submissions, analysis_form = build_fixture('analysis_form')
    pack = FormPack(schemas, title)
    pack.extend_survey(analysis_form)

    report = pack.autoreport(versions=pack.versions.keys())
    stats = report.get_stats(submissions, lang='English (en)')

    assert stats.submissions_count == 6

    stats = [(str(repr(f)), n, d) for f, n, d in stats]

    expected = [
        (
            "<MediaField name='record_a_note' type='audio'>",
            'record_a_note',
            {
                'total_count': 6,
                'not_provided': 0,
                'provided': 6,
                'show_graph': False,
                'frequency': [
                    ('clerk_interaction_1.mp3', 1),
                    ('clerk_interaction_2.mp3', 1),
                    ('clerk_interaction_3.mp3', 1),
                    ('clerk_interaction_4.mp3', 1),
                    ('clerk_interaction_5.mp3', 1),
                    ('clerk_interaction_6.mp3', 1),
                ],
                'percentage': [
                    ('clerk_interaction_1.mp3', 16.67),
                    ('clerk_interaction_2.mp3', 16.67),
                    ('clerk_interaction_3.mp3', 16.67),
                    ('clerk_interaction_4.mp3', 16.67),
                    ('clerk_interaction_5.mp3', 16.67),
                    ('clerk_interaction_6.mp3', 16.67),
                ],
            },
        ),
        (
            "<TextField name='name_of_shop' type='text'>",
            "What is the shop's name?",
            {
                'total_count': 6,
                'not_provided': 3,
                'provided': 3,
                'show_graph': False,
                'frequency': [
                    ('Save On', 1),
                    ('Walmart', 1),
                    ('Costco', 1),
                ],
                'percentage': [
                    ('Save On', 16.67),
                    ('Walmart', 16.67),
                    ('Costco', 16.67),
                ],
            },
        ),
        (
            "<TextField name='name_of_clerk' type='text'>",
            "What is the clerk's name?",
            {
                'total_count': 6,
                'not_provided': 3,
                'provided': 3,
                'show_graph': False,
                'frequency': [
                    ('John', 1),
                    ('Alex', 1),
                    ('Olivier', 1),
                ],
                'percentage': [
                    ('John', 16.67),
                    ('Alex', 16.67),
                    ('Olivier', 16.67),
                ],
            },
        ),
    ]

    for i, stat in enumerate(stats):
        assert stat == expected[i]
