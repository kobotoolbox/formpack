# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

import unittest

from textwrap import dedent

from collections import OrderedDict

from nose.tools import raises

from path import tempdir

from formpack import FormPack
from .fixtures import build_fixture


customer_satisfaction = build_fixture('customer_satisfaction')
restaurant_profile = build_fixture('restaurant_profile')


class TestFormPackExport(unittest.TestCase):
    maxDiff = None

    def assertTextEqual(self, text1, text2):
        self.assertEquals(dedent(text1).strip(), dedent(text2).strip())

    def test_generator_export(self):

        title, schemas, submissions = customer_satisfaction

        forms = FormPack(schemas, title)
        export = forms.export().to_dict(submissions)
        expected = OrderedDict({
                    "Customer Satisfaction": {
                        'fields': ["restaurant_name", "customer_enjoyment"],
                        'data': [
                            ["Felipes", "yes"],
                            ["Dunkin Donuts", "no"],
                            ["McDonalds", "no"]
                        ]
                    }
               })

        self.assertEqual(export, expected)

    def test_generator_export_translation_headers(self):

        title, schemas, submissions = restaurant_profile
        fp = FormPack(schemas, title)

        self.assertEqual(len(fp.versions), 4)
        self.assertEqual(len(fp[1].translations), 2)

        # by default, exports use the question 'name' attribute
        headers = fp.export(versions=0).to_dict(submissions)['Restaurant profile']['fields']
        self.assertEquals(headers, ['restaurant_name',
                                     'location',
                                     '_location_latitude',
                                     '_location_longitude',
                                     '_location_altitude',
                                     '_location_precision'])

        # the first translation in the list is the translation that
        # appears first in the column list. in this case, 'label::english'
        translations = fp[1].translations
        export = fp.export(lang=translations[0], versions=1)
        data = export.to_dict(submissions)
        headers = data['Restaurant profile']['fields']
        self.assertEquals(headers, ['restaurant name',
                                    'location',
                                    '_location_latitude',
                                    '_location_longitude',
                                    '_location_altitude',
                                    '_location_precision'])

        export = fp.export(lang=translations[1], versions=1)
        data = export.to_dict(submissions)
        headers = data['Restaurant profile']['fields']
        self.assertEquals(headers, ['nom du restaurant',
                                    'lieu',
                                    '_lieu_latitude',
                                    '_lieu_longitude',
                                    '_lieu_altitude',
                                    '_lieu_precision'])

        # "_default" use the "Label" field
        # TODO: make a separate test to test to test __getitem__
        export = fp.export(lang="_default", versions='rpv1')
        data = export.to_dict(submissions)
        headers = data['Restaurant profile']['fields']
        self.assertEquals(headers, ['restaurant name',
                                    'location',
                                    '_location_latitude',
                                    '_location_longitude',
                                    '_location_altitude',
                                    '_location_precision'])

    def test_export_with_choice_lists(self):

        title, schemas, submissions = restaurant_profile

        fp = FormPack(schemas, title)
        self.assertEqual(len(fp[1].translations), 2)
        # by default, exports use the question 'name' attribute
        options = {'versions': 'rpV3'}

        export = fp.export(**options).to_dict(submissions)['Restaurant profile']
        self.assertEquals(export['fields'], ['restaurant_name',
                                             'location',
                                             '_location_latitude',
                                             '_location_longitude',
                                             '_location_altitude',
                                             '_location_precision',
                                             'eatery_type'])
        self.assertEquals(export['data'], [['Taco Truck',
                                             '13.42 -25.43',
                                             '13.42',
                                             '-25.43',
                                             '',
                                             '',
                                             'takeaway'],
                                            ['Harvest',
                                             '12.43 -24.53',
                                             '12.43',
                                             '-24.53',
                                             '',
                                             '',
                                             'sit_down']])

        # if a language is passed, fields with available translations
        # are translated into that language
        options['lang'] = fp[1].translations[0]
        export = fp.export(**options).to_dict(submissions)['Restaurant profile']
        self.assertEquals(export['data'], [['Taco Truck',
                                             '13.42 -25.43',
                                             '13.42',
                                             '-25.43',
                                             '',
                                             '',
                                             'take-away'],
                                            ['Harvest',
                                             '12.43 -24.53',
                                             '12.43',
                                             '-24.53',
                                             '',
                                             '',
                                             'sit down']])

        options['lang'] = fp[1].translations[1]
        export = fp.export(**options).to_dict(submissions)['Restaurant profile']
        self.assertEquals(export['data'], [['Taco Truck',
                                             '13.42 -25.43',
                                             '13.42',
                                             '-25.43',
                                             '',
                                             '',
                                             'avec vente à emporter'],
                                            ['Harvest',
                                             '12.43 -24.53',
                                             '12.43',
                                             '-24.53',
                                             '',
                                             '',
                                             'traditionnel']])


    def test_headers_of_group_exports(self):
        title, schemas, submissions = build_fixture('grouped_questions')
        fp = FormPack(schemas, title)
        options = {'versions': 'gqs'}

        # by default, groups are stripped.
        export = fp.export(**options).to_dict(submissions)
        headers = export['Grouped questions']['fields']
        self.assertEquals(headers, ['q1', 'g1q1', 'g1sg1q1',
                                    'g1q2', 'g2q1', 'qz'])

    def test_submissions_of_group_exports(self):
        title, schemas, submissions = build_fixture('grouped_questions')
        fp = FormPack(schemas, title)
        options = {'versions': 'gqs'}

        export = fp.export(**options).to_dict(submissions)['Grouped questions']
        self.assertEquals(export['fields'], ['q1', 'g1q1', 'g1sg1q1',
                                             'g1q2', 'g2q1', 'qz'])
        self.assertEquals(export['data'], [['respondent1\'s r1',
                                            'respondent1\'s r2',
                                            'respondent1\'s r2.5',
                                            'respondent1\'s r2.75 :)',
                                            'respondent1\'s r3',
                                            'respondent1\'s r4'],
                                           ['respondent2\'s r1',
                                            'respondent2\'s r2',
                                            'respondent2\'s r2.5',
                                            'respondent2\'s r2.75 :)',
                                            'respondent2\'s r3',
                                            'respondent2\'s r4']])

        options['hierarchy_in_labels'] = '/'
        export = fp.export(**options).to_dict(submissions)['Grouped questions']
        self.assertEquals(export['fields'], ['q1',
                                             'g1/g1q1',
                                             'g1/sg1/g1sg1q1',
                                             'g1/g1q2',
                                             'g2/g2q1',
                                             'qz'])
        self.assertEquals(export['data'], [['respondent1\'s r1',
                                            'respondent1\'s r2',
                                            'respondent1\'s r2.5',
                                            'respondent1\'s r2.75 :)',
                                            'respondent1\'s r3',
                                            'respondent1\'s r4'],
                                           ['respondent2\'s r1',
                                            'respondent2\'s r2',
                                            'respondent2\'s r2.5',
                                            'respondent2\'s r2.75 :)',
                                            'respondent2\'s r3',
                                            'respondent2\'s r4']])

    def test_repeats(self):
        title, schemas, submissions = build_fixture('grouped_repeatable')
        fp = FormPack(schemas, title)
        options = {'versions': 'rgv1'}
        export = fp.export(**options).to_dict(submissions)

        self.assertEqual(export, OrderedDict ([
                            ('Household survey with repeat...',
                                {
                                    'fields': [
                                        'household_location',
                                        'start',
                                        'end',
                                        '_index'
                                    ],
                                    'data': [
                                        [
                                            'montreal',
                                            '2016-03-14T14:15:48.000-04:00',
                                            '2016-03-14T14:18:35.000-04:00',
                                            1
                                        ],
                                        [
                                            'marseille',
                                            '2016-03-14T14:14:10.000-04:00',
                                            '2016-03-14T14:15:48.000-04:00',
                                            2
                                        ],
                                        [
                                            'rocky mountains',
                                            '2016-03-14T14:13:53.000-04:00',
                                            '2016-03-14T14:14:10.000-04:00',
                                            3
                                        ],
                                        [
                                            'toronto',
                                            '2016-03-14T14:12:54.000-04:00',
                                            '2016-03-14T14:13:53.000-04:00',
                                            4
                                        ],
                                        [
                                            'new york',
                                            '2016-03-14T14:18:35.000-04:00',
                                            '2016-03-14T15:19:20.000-04:00',
                                            5
                                        ],
                                        [
                                            'boston',
                                            '2016-03-14T14:11:25.000-04:00',
                                            '2016-03-14T14:12:03.000-04:00',
                                            6
                                        ]
                                    ]
                                }),
                            ('houshold_member_repeat',
                                {
                                    'fields': [
                                        'household_member_name',
                                        '_parent_table_name',
                                        '_parent_index'
                                    ],
                                    'data': [
                                        [
                                            'peter',
                                            'Household survey with repeat...',
                                            1
                                        ],
                                        [
                                            'kyle',
                                            'Household survey with repeat...',
                                            2
                                        ],
                                        [
                                            'linda',
                                            'Household survey with repeat...',
                                            2
                                        ],
                                        [
                                            'morty',
                                            'Household survey with repeat...',
                                            3
                                        ],
                                        [
                                            'tony',
                                            'Household survey with repeat...',
                                            4
                                        ],
                                        [
                                            'mary',
                                            'Household survey with repeat...',
                                            4
                                        ],
                                        [
                                            'emma',
                                            'Household survey with repeat...',
                                            5
                                        ],
                                        [
                                            'parker',
                                            'Household survey with repeat...',
                                            5
                                        ],
                                        [
                                            'amadou',
                                            'Household survey with repeat...',
                                            6
                                        ],
                                        [
                                            'esteban',
                                            'Household survey with repeat...',
                                            6
                                        ],
                                        [
                                            'suzie',
                                            'Household survey with repeat...',
                                            6
                                        ],
                                        [
                                            'fiona',
                                            'Household survey with repeat...',
                                            6
                                        ],
                                        [
                                            'phillip',
                                            'Household survey with repeat...',
                                            6
                                        ]
                                    ]
                                })
                            ])
        )


    def test_repeats_alias(self):
        title, schemas, submissions = build_fixture('grouped_repeatable_alias')
        fp = FormPack(schemas, title)
        options = {'versions': 'rgv1'}
        export = fp.export(**options).to_dict(submissions)

        self.assertEqual(export, OrderedDict ([
                            ('Grouped Repeatable Alias',
                                {
                                    'fields': [
                                        'household_location',
                                        'start',
                                        'end',
                                        '_index'
                                    ],
                                    'data': [
                                        [
                                            'montreal',
                                            '2016-03-14T14:15:48.000-04:00',
                                            '2016-03-14T14:18:35.000-04:00',
                                            1
                                        ],
                                        [
                                            'marseille',
                                            '2016-03-14T14:14:10.000-04:00',
                                            '2016-03-14T14:15:48.000-04:00',
                                            2
                                        ],
                                        [
                                            'rocky mountains',
                                            '2016-03-14T14:13:53.000-04:00',
                                            '2016-03-14T14:14:10.000-04:00',
                                            3
                                        ],
                                        [
                                            'toronto',
                                            '2016-03-14T14:12:54.000-04:00',
                                            '2016-03-14T14:13:53.000-04:00',
                                            4
                                        ],
                                        [
                                            'new york',
                                            '2016-03-14T14:18:35.000-04:00',
                                            '2016-03-14T15:19:20.000-04:00',
                                            5
                                        ],
                                        [
                                            'boston',
                                            '2016-03-14T14:11:25.000-04:00',
                                            '2016-03-14T14:12:03.000-04:00',
                                            6
                                        ]
                                    ]
                                }),
                            ('houshold_member_repeat',
                                {
                                    'fields': [
                                        'household_member_name',
                                        '_parent_table_name',
                                        '_parent_index'
                                    ],
                                    'data': [
                                        [
                                            'peter',
                                            'Grouped Repeatable Alias',
                                            1
                                        ],
                                        [
                                            'kyle',
                                            'Grouped Repeatable Alias',
                                            2
                                        ],
                                        [
                                            'linda',
                                            'Grouped Repeatable Alias',
                                            2
                                        ],
                                        [
                                            'morty',
                                            'Grouped Repeatable Alias',
                                            3
                                        ],
                                        [
                                            'tony',
                                            'Grouped Repeatable Alias',
                                            4
                                        ],
                                        [
                                            'mary',
                                            'Grouped Repeatable Alias',
                                            4
                                        ],
                                        [
                                            'emma',
                                            'Grouped Repeatable Alias',
                                            5
                                        ],
                                        [
                                            'parker',
                                            'Grouped Repeatable Alias',
                                            5
                                        ],
                                        [
                                            'amadou',
                                            'Grouped Repeatable Alias',
                                            6
                                        ],
                                        [
                                            'esteban',
                                            'Grouped Repeatable Alias',
                                            6
                                        ],
                                        [
                                            'suzie',
                                            'Grouped Repeatable Alias',
                                            6
                                        ],
                                        [
                                            'fiona',
                                            'Grouped Repeatable Alias',
                                            6
                                        ],
                                        [
                                            'phillip',
                                            'Grouped Repeatable Alias',
                                            6
                                        ]
                                    ]
                                })
                            ])
        )

    def test_csv(self):
        title, schemas, submissions = build_fixture('grouped_questions')
        fp = FormPack(schemas, title)
        options = {'versions': 'gqs'}
        csv_data = "\n".join(fp.export(**options).to_csv(submissions))

        expected = """
        "q1";"g1q1";"g1sg1q1";"g1q2";"g2q1";"qz"
        "respondent1's r1";"respondent1's r2";"respondent1's r2.5";"respondent1's r2.75 :)";"respondent1's r3";"respondent1's r4"
        "respondent2's r1";"respondent2's r2";"respondent2's r2.5";"respondent2's r2.75 :)";"respondent2's r3";"respondent2's r4"
        """

        self.assertTextEqual(csv_data, expected)

        options = {'versions': 'gqs', 'hierarchy_in_labels': True}
        csv_data = "\n".join(fp.export(**options).to_csv(submissions))

        expected = """
        "q1";"g1/g1q1";"g1/sg1/g1sg1q1";"g1/g1q2";"g2/g2q1";"qz"
        "respondent1's r1";"respondent1's r2";"respondent1's r2.5";"respondent1's r2.75 :)";"respondent1's r3";"respondent1's r4"
        "respondent2's r1";"respondent2's r2";"respondent2's r2.5";"respondent2's r2.75 :)";"respondent2's r3";"respondent2's r4"
        """

        self.assertTextEqual(csv_data, expected)

        options = {'versions': 'gqs', 'hierarchy_in_labels': True,
                   'lang': "_default"}
        csv_data = "\n".join(fp.export(**options).to_csv(submissions))

        expected = """
        "Q1";"Group 1/G1Q1";"Group 1/Sub Group 1/G1SG1Q1";"Group 1/G1Q2";"g2/G2Q1";"QZed"
        "respondent1's r1";"respondent1's r2";"respondent1's r2.5";"respondent1's r2.75 :)";"respondent1's r3";"respondent1's r4"
        "respondent2's r1";"respondent2's r2";"respondent2's r2.5";"respondent2's r2.75 :)";"respondent2's r3";"respondent2's r4"
        """
        self.assertTextEqual(csv_data, expected)

        title, schemas, submissions = restaurant_profile
        fp = FormPack(schemas, title)
        options = {'versions': 'rpV3', 'lang': fp[1].translations[1]}
        csv_data = "\n".join(fp.export(**options).to_csv(submissions))

        expected = """
        "nom du restaurant";"lieu";"_lieu_latitude";"_lieu_longitude";"_lieu_altitude";"_lieu_precision";"type de restaurant"
        "Taco Truck";"13.42 -25.43";"13.42";"-25.43";"";"";"avec vente à emporter"
        "Harvest";"12.43 -24.53";"12.43";"-24.53";"";"";"traditionnel"
        """

        self.assertTextEqual(csv_data, expected)

    # disabled for now
    # @raises(RuntimeError)
    # def test_csv_on_repeatable_groups(self):
    #     title, schemas, submissions = build_fixture('grouped_repeatable')
    #     fp = FormPack(schemas, title)
    #     options = {'versions': 'rgv1'}
    #     list(fp.export(**options).to_csv(submissions))

    def test_export_with_split_fields(self):
        title, schemas, submissions = restaurant_profile
        fp = FormPack(schemas, title)
        options = {'versions': 'rpV4'}
        export = fp.export(**options).to_dict(submissions)['Restaurant profile']
        expected = {
            'fields': [
                'restaurant_name',
                'location',
                '_location_latitude',
                '_location_longitude',
                '_location_altitude',
                '_location_precision',
                'eatery_type',
                'eatery_type/sit_down',
                'eatery_type/takeaway',
            ],
            'data': [
                [
                    'Taco Truck',
                    '13.42 -25.43',
                    '13.42',
                    '-25.43',
                    '',
                    '',
                    'takeaway sit_down',
                    '1',
                    '1'
                ],
                [
                    'Harvest',
                    '12.43 -24.53',
                    '12.43',
                    '-24.53',
                    '',
                    '',
                    'sit_down',
                    '1',
                    '0'
                ],
                [
                    'Wololo',
                    '12.43 -24.54 1 0',
                    '12.43',
                    '-24.54',
                    '1',
                    '0',
                    '',
                    '0',
                    '0'
                ],
                [
                    'Los pollos hermanos',
                    '12.43 -24.54 1',
                    '12.43',
                    '-24.54',
                    '1',
                    '',
                    '',
                    '',
                    ''
                ]
            ]
        }

        self.assertEqual(export, expected)

        options = {'versions': 'rpV4', "group_sep": "::",
                    'hierarchy_in_labels': True,
                   "lang": fp[-1].translations[1]}
        export = fp.export(**options).to_dict(submissions)['Restaurant profile']

        expected = {
            'fields': [
                'nom du restaurant',
                'lieu',
                '_lieu_latitude',
                '_lieu_longitude',
                '_lieu_altitude',
                '_lieu_precision',
                'type de restaurant',
                'type de restaurant::traditionnel',
                'type de restaurant::avec vente à emporter',
            ],
            'data': [
                [
                    'Taco Truck',
                    '13.42 -25.43',
                    '13.42',
                    '-25.43',
                    '',
                    '',
                    'avec vente à emporter traditionnel',
                    '1',
                    '1'
                ],
                [
                    'Harvest',
                    '12.43 -24.53',
                    '12.43',
                    '-24.53',
                    '',
                    '',
                    'traditionnel',
                    '1',
                    '0'
                ],
                [
                    'Wololo',
                    '12.43 -24.54 1 0',
                    '12.43',
                    '-24.54',
                    '1',
                    '0',
                    '',
                    '0',
                    '0'
                ],
                [
                    'Los pollos hermanos',
                    '12.43 -24.54 1',
                    '12.43',
                    '-24.54',
                    '1',
                    '',
                    '',
                    '',
                    ''
                ]
            ]
        }

        self.assertEqual(export, expected)

    def test_xlsx(self):
        title, schemas, submissions = build_fixture('grouped_repeatable')
        fp = FormPack(schemas, title)
        options = {'versions': 'rgv1'}

        with tempdir() as d:
            xls = d / 'foo.xlsx'
            fp.export(**options).to_xlsx(xls, submissions)
            assert xls.isfile()

    def test_force_index(self):
        title, schemas, submissions = customer_satisfaction

        forms = FormPack(schemas, title)
        export = forms.export(force_index=True).to_dict(submissions)
        expected = OrderedDict({
                    "Customer Satisfaction": {
                        'fields': ["restaurant_name", "customer_enjoyment",
                                   "_index"],
                        'data': [
                            ["Felipes", "yes", 1],
                            ["Dunkin Donuts", "no", 2],
                            ["McDonalds", "no", 3]
                        ]
                    }
               })

        self.assertEqual(export, expected)

    def test_copy_fields(self):
        title, schemas, submissions = customer_satisfaction

        forms = FormPack(schemas, title)
        export = forms.export(copy_fields=('_uuid', '_submission_time'))
        exported = export.to_dict(submissions)
        expected = OrderedDict({
                    "Customer Satisfaction": {
                        'fields': ["restaurant_name", "customer_enjoyment",
                                   "_uuid", "_submission_time"],
                        'data': [
                            [
                                "Felipes",
                                "yes",
                                "90dd7750f83011e590707c7a9125d07d",
                                "2016-04-01 19:57:45.306805"
                            ],

                            [
                                "Dunkin Donuts",
                                "no",
                                "90dd7750f83011e590707c7a9125d08d",
                                "2016-04-02 19:57:45.306805"
                            ],

                            [
                                "McDonalds",
                                "no",
                                "90dd7750f83011e590707c7a9125d09d",
                                "2016-04-03 19:57:45.306805"
                            ]
                        ]
                    }
               })

        self.assertEqual(exported, expected)

    def test_copy_fields_and_force_index_and_unicode(self):
        title, schemas, submissions = customer_satisfaction

        fp = FormPack(schemas, 'رضا العملاء')
        export = fp.export(copy_fields=('_uuid', '_submission_time'),
                              force_index=True)
        exported = export.to_dict(submissions)
        expected = OrderedDict({
                    "رضا العملاء": {
                        'fields': ["restaurant_name", "customer_enjoyment",
                                   "_uuid", "_submission_time", "_index"],
                        'data': [
                            [
                                "Felipes",
                                "yes",
                                "90dd7750f83011e590707c7a9125d07d",
                                "2016-04-01 19:57:45.306805",
                                1
                            ],

                            [
                                "Dunkin Donuts",
                                "no",
                                "90dd7750f83011e590707c7a9125d08d",
                                "2016-04-02 19:57:45.306805",
                                2
                            ],

                            [
                                "McDonalds",
                                "no",
                                "90dd7750f83011e590707c7a9125d09d",
                                "2016-04-03 19:57:45.306805",
                                3
                            ]
                        ]
                    }
               })

        self.assertEqual(exported, expected)

        with tempdir() as d:
            xls = d / 'test.xlsx'
            fp.export().to_xlsx(xls, submissions)
            assert xls.isfile()

    def test_choices_external_as_text_field(self):
        title, schemas, submissions = build_fixture('sanitation_report_external')

        fp = FormPack(schemas, title)
        export = fp.export(lang="_default")
        exported = export.to_dict(submissions)
        expected = OrderedDict ([
                    (
                        'Sanitation report external', {
                            'fields': [
                                'Restaurant name',
                                'How did this restaurant do on its sanitation report?',
                                'Report date'
                            ],
                            'data': [
                                [
                                    'Felipes',
                                    'A',
                                    '012345'
                                ],
                                [
                                    'Chipotle',
                                    'C',
                                    '012346'
                                ],
                                [
                                    'Dunkin Donuts',
                                    'D',
                                    '012347'
                                ],
                                [
                                    'Boloco',
                                    'B',
                                    '012348'
                                ]
                            ]
                        }
                    )
                ])

        self.assertEqual(exported, expected)

    def test_multi_version_export(self):
        title, schemas, submissions = restaurant_profile
        fp = FormPack(schemas, title)
        self.assertEqual(len(fp.versions), 4)
        failure = fp.export(lang='_default', versions=fp.versions.keys())
