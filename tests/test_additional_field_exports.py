# coding: utf-8
import unittest
from formpack import FormPack
from .fixtures import build_fixture
from .fixtures.load_fixture_json import load_analysis_form_json


def test_additional_field_exports_without_labels():
    title, schemas, submissions = build_fixture('analysis_form')
    analysis_form = load_analysis_form_json('analysis_form')
    pack = FormPack(schemas, title=title)
    pack.extend_survey(analysis_form)

    options = {
        'versions': 'v1',
        'filter_fields': [
            'record_a_note',
            '_supplementalDetails/record_a_note/transcript_en',
            '_supplementalDetails/record_a_note/transcript_es',
            '_supplementalDetails/record_a_note/translation_en',
            '_supplementalDetails/record_a_note/translation_es',
        ],
    }
    export = pack.export(**options)
    values = export.to_dict(submissions)
    main_export_sheet = values['Simple Clerk Interaction']

    assert 3 == len(main_export_sheet['data'])
    assert main_export_sheet['fields'] == [
        'record_a_note',
        'record_a_note - transcript (en)',
        'record_a_note - transcript (es)',
        'record_a_note - translation (en)',
        'record_a_note - translation (es)',
    ]
    response0 = main_export_sheet['data'][0]
    assert response0 == [
        'clerk_interaction_1.mp3',
        '',
        'Saluton, kiel mi povas helpi vin?',
        'Hello how may I help you?',
        '',
    ]


def test_additional_field_exports_with_labels():
    title, schemas, submissions = build_fixture('analysis_form')
    analysis_form = load_analysis_form_json('analysis_form')
    pack = FormPack(schemas, title=title)
    pack.extend_survey(analysis_form)

    options = {
        'versions': 'v1',
        'filter_fields': [
            'record_a_note',
            '_supplementalDetails/record_a_note/transcript_en',
            '_supplementalDetails/record_a_note/transcript_es',
            '_supplementalDetails/record_a_note/translation_en',
            '_supplementalDetails/record_a_note/translation_es',
        ],
        'lang': 'English (en)',
    }
    export = pack.export(**options)
    values = export.to_dict(submissions)
    main_export_sheet = values['Simple Clerk Interaction']

    assert 3 == len(main_export_sheet['data'])
    assert main_export_sheet['fields'] == [
        'Record a clerk saying something',
        'Record a clerk saying something - transcript (en)',
        'Record a clerk saying something - transcript (es)',
        'Record a clerk saying something - translation (en)',
        'Record a clerk saying something - translation (es)',
    ]
    response0 = main_export_sheet['data'][0]
    assert response0 == [
        'clerk_interaction_1.mp3',
        '',
        'Saluton, kiel mi povas helpi vin?',
        'Hello how may I help you?',
        '',
    ]


@unittest.skip('Currently not supporting repeat groups')
def test_additional_field_exports_repeat_groups():
    title, schemas, submissions = build_fixture('analysis_form_repeat_groups')
    analysis_form = load_analysis_form_json('analysis_form_repeat_groups')
    pack = FormPack(schemas, title=title)
    pack.extend_survey(analysis_form)

    options = {
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
        'record_a_note/transcript_acme_1_speech2text',
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
        'record_a_noise/comment_on_noise_level',
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


def test_additional_field_exports_advanced():
    title, schemas, submissions = build_fixture('analysis_form_advanced')
    analysis_form = load_analysis_form_json('analysis_form_advanced')
    pack = FormPack(schemas, title=title)
    pack.extend_survey(analysis_form)

    options = {
        'versions': 'v1',
        'multiple_select': 'both',
    }
    export = pack.export(**options)
    values = export.to_dict(submissions)
    main_export_sheet = values['Advanced Clerk Interaction']

    assert 3 == len(main_export_sheet['data'])
    assert main_export_sheet['fields'] == [
        'record_a_note',
        'record_a_note - transcript (en)',
        "record_a_note - How was the tone of the clerk's voice?",
        'goods_sold',
        'goods_sold/chocolate',
        'goods_sold/fruit',
        'goods_sold/pasta',
        'goods_sold - Comment on the goods sold at the store',
        'goods_sold - Rate the quality of the goods sold at the store',
    ]
    assert main_export_sheet['data'] == [
        [
            'clerk_interaction_1.mp3',
            'Hello how may I help you?',
            'Excited,Confused',
            'chocolate',
            '1',
            '0',
            '0',
            'Not much diversity',
            'High quality',
        ],
        [
            'clerk_interaction_2.mp3',
            'Thank you for your business',
            'Anxious,Excited',
            'chocolate fruit pasta',
            '1',
            '1',
            '1',
            '',
            'Average quality',
        ],
        [
            'clerk_interaction_3.mp3',
            '',
            '',
            'pasta',
            '0',
            '0',
            '1',
            '',
            'High quality',
        ],
    ]

    options['multiple_select'] = 'details'
    export = pack.export(**options)
    values = export.to_dict(submissions)
    main_export_sheet = values['Advanced Clerk Interaction']

    assert main_export_sheet['fields'] == [
        'record_a_note',
        'record_a_note - transcript (en)',
        "record_a_note - How was the tone of the clerk's voice?",
        'goods_sold/chocolate',
        'goods_sold/fruit',
        'goods_sold/pasta',
        'goods_sold - Comment on the goods sold at the store',
        'goods_sold - Rate the quality of the goods sold at the store',
    ]
    assert main_export_sheet['data'] == [
        [
            'clerk_interaction_1.mp3',
            'Hello how may I help you?',
            'Excited,Confused',
            '1',
            '0',
            '0',
            'Not much diversity',
            'High quality',
        ],
        [
            'clerk_interaction_2.mp3',
            'Thank you for your business',
            'Anxious,Excited',
            '1',
            '1',
            '1',
            '',
            'Average quality',
        ],
        [
            'clerk_interaction_3.mp3',
            '',
            '',
            '0',
            '0',
            '1',
            '',
            'High quality',
        ],
    ]

    options['multiple_select'] = 'summary'
    export = pack.export(**options)
    values = export.to_dict(submissions)
    main_export_sheet = values['Advanced Clerk Interaction']

    assert main_export_sheet['fields'] == [
        'record_a_note',
        'record_a_note - transcript (en)',
        "record_a_note - How was the tone of the clerk's voice?",
        'goods_sold',
        'goods_sold - Comment on the goods sold at the store',
        'goods_sold - Rate the quality of the goods sold at the store',
    ]
    assert main_export_sheet['data'] == [
        [
            'clerk_interaction_1.mp3',
            'Hello how may I help you?',
            'Excited,Confused',
            'chocolate',
            'Not much diversity',
            'High quality',
        ],
        [
            'clerk_interaction_2.mp3',
            'Thank you for your business',
            'Anxious,Excited',
            'chocolate fruit pasta',
            '',
            'Average quality',
        ],
        [
            'clerk_interaction_3.mp3',
            '',
            '',
            'pasta',
            '',
            'High quality',
        ],
    ]


def test_additional_field_exports_v2():
    title, schemas, submissions = build_fixture('analysis_form')
    analysis_form = load_analysis_form_json('analysis_form')
    pack = FormPack(schemas, title=title)
    pack.extend_survey(analysis_form)

    options = {'versions': 'v2'}
    export = pack.export(**options)
    values = export.to_dict(submissions)
    main_export_sheet = values['Simple Clerk Interaction']

    assert 3 == len(main_export_sheet['data'])
    assert main_export_sheet['fields'] == [
        'record_a_note',
        'record_a_note - transcript (en)',
        'record_a_note - transcript (es)',
        'record_a_note - translation (en)',
        'record_a_note - translation (es)',
        # `name_of_clerk` is absent in v2
        'name_of_shop',
        'name_of_shop - Comment on the name of the shop',
    ]
    response0 = main_export_sheet['data'][0]
    assert response0 == [
        'clerk_interaction_4.mp3',
        'Hello how may I help you?',
        '',
        '',
        '',
        'Save On',
        'Pretty cliche',
    ]


def test_additional_field_exports_all_versions():
    title, schemas, submissions = build_fixture('analysis_form')
    analysis_form = load_analysis_form_json('analysis_form')
    pack = FormPack(schemas, title=title)
    pack.extend_survey(analysis_form)

    options = {'versions': pack.versions}
    export = pack.export(**options)
    values = export.to_dict(submissions)
    main_export_sheet = values['Simple Clerk Interaction']

    assert 6 == len(main_export_sheet['data'])
    assert main_export_sheet['fields'] == [
        'record_a_note',
        'record_a_note - transcript (en)',
        'record_a_note - transcript (es)',
        'record_a_note - translation (en)',
        'record_a_note - translation (es)',
        'name_of_shop',
        'name_of_shop - Comment on the name of the shop',
        'name_of_clerk',
        'name_of_clerk - Comment on the name of the clerk',
    ]
    response0 = main_export_sheet['data'][0]
    assert response0 == [
        'clerk_interaction_1.mp3',
        '',
        'Saluton, kiel mi povas helpi vin?',
        'Hello how may I help you?',
        '',
        '',
        '',
        'John',
        'Sounds like an interesting person',
    ]
    response3 = main_export_sheet['data'][3]
    assert response3 == [
        'clerk_interaction_4.mp3',
        'Hello how may I help you?',
        '',
        '',
        '',
        'Save On',
        'Pretty cliche',
        '',
        '',
    ]


def test_additional_field_exports_all_versions_exclude_fields():
    title, schemas, submissions = build_fixture('analysis_form')
    analysis_form = load_analysis_form_json('analysis_form')
    pack = FormPack(schemas, title=title)
    pack.extend_survey(analysis_form)

    options = {
        'versions': pack.versions,
        'filter_fields': [
            'record_a_note',
            # FIXME: These make no sense because `name_of_*` are regular survey questions, not "additional fields"
            # Or is the idea that by selecting the source fields the related additional fields come along automatically?
            # But if that's true, why do we explicitly request the additional fields in `test_additional_field_exports_with_labels()`?
            '_supplementalDetails/clerk_details/name_of_shop',
            '_supplementalDetails/clerk_details/name_of_clerk',
        ],
    }
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


def test_additional_field_exports_all_versions_langs():
    title, schemas, submissions = build_fixture('analysis_form')
    analysis_form = load_analysis_form_json('analysis_form')
    pack = FormPack(schemas, title=title)
    pack.extend_survey(analysis_form)

    options = {
        'versions': pack.versions,
        'lang': 'English (en)',
    }
    export = pack.export(**options)
    values = export.to_dict(submissions)
    main_export_sheet = values['Simple Clerk Interaction']

    assert main_export_sheet['fields'] == [
        'Record a clerk saying something',
        'Record a clerk saying something - transcript (en)',
        'Record a clerk saying something - transcript (es)',
        'Record a clerk saying something - translation (en)',
        'Record a clerk saying something - translation (es)',
        "What is the shop's name?",
        "What is the shop's name? - Comment on the name of the shop",
        "What is the clerk's name?",
        "What is the clerk's name? - Comment on the name of the clerk",
    ]

    options['lang'] = 'Esperanto (es)'
    export = pack.export(**options)
    values = export.to_dict(submissions)
    main_export_sheet = values['Simple Clerk Interaction']

    assert main_export_sheet['fields'] == [
        'Registri oficiston dirantan ion',
        'Registri oficiston dirantan ion - transcript (en)',
        'Registri oficiston dirantan ion - transcript (es)',
        'Registri oficiston dirantan ion - translation (en)',
        'Registri oficiston dirantan ion - translation (es)',
        'Kio estas la nomo de la butiko?',
        'Kio estas la nomo de la butiko? - Comment on the name of the shop',
        'name_of_clerk',
        'name_of_clerk - Comment on the name of the clerk',
    ]

    options['lang'] = None
    export = pack.export(**options)
    values = export.to_dict(submissions)
    main_export_sheet = values['Simple Clerk Interaction']

    assert main_export_sheet['fields'] == [
        'record_a_note',
        'record_a_note - transcript (en)',
        'record_a_note - transcript (es)',
        'record_a_note - translation (en)',
        'record_a_note - translation (es)',
        'name_of_shop',
        'name_of_shop - Comment on the name of the shop',
        'name_of_clerk',
        'name_of_clerk - Comment on the name of the clerk',
    ]


def test_simple_report_with_analysis_form():
    title, schemas, submissions = build_fixture('analysis_form')
    analysis_form = load_analysis_form_json('analysis_form')
    pack = FormPack(schemas, title)
    pack.extend_survey(analysis_form)

    lang = 'English (en)'
    report = pack.autoreport(versions=pack.versions.keys())
    stats = report.get_stats(submissions, lang=lang)

    assert stats.submissions_count == 6

    stats = [n for f, n, d in stats]
    # Ensure analysis fields aren't making it into the report
    assert stats == [
        'record_a_note',
        "What is the shop's name?",
        "What is the clerk's name?",
    ]
