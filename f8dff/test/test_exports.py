# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

import unittest

from textwrap import dedent

from collections import OrderedDict

from nose.tools import raises

from path import tempdir

from ..models.formpack.pack import FormPack
from ..fixtures import build_fixture


customer_satisfaction = build_fixture('customer_satisfaction')
restaurant_profile = build_fixture('restaurant_profile')


class TestFormPackExport(unittest.TestCase):
    maxDiff = None

    def assertTextEqual(self, text1, text2):
        self.assertEquals(dedent(text1).strip(), dedent(text2).strip())

    def test_generator_export(self):
        forms = FormPack(**customer_satisfaction)
        export = forms.export()
        export = forms.export().to_dict()
        expected = OrderedDict({
                    "submissions": {
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
        fp = FormPack(**restaurant_profile)
        self.assertEqual(len(fp.versions), 4)
        self.assertEqual(len(fp[1].translations), 2)

        # by default, exports use the question 'name' attribute
        headers = fp.export(version=0).to_dict()['submissions']['fields']
        self.assertEquals(headers, ['restaurant_name', 'location'])

        # the first translation in the list is the translation that
        # appears first in the column list. in this case, 'label::english'
        translations = fp[1].translations
        export = fp.export(header_lang=translations[0], version=1).to_dict()
        headers = export['submissions']['fields']
        self.assertEquals(headers, ['restaurant name', 'location'])

        export = fp.export(header_lang=translations[1], version=1).to_dict()
        headers = export['submissions']['fields']
        self.assertEquals(headers, ['nom du restaurant', 'lieu'])

        # "_default" use the "Label" field
        # TODO: make a separate test to test to test __getitem__
        fp = FormPack(**restaurant_profile)
        export = fp.export(header_lang="_default", version='rpv1').to_dict()
        headers = export['submissions']['fields']
        self.assertEquals(headers, ['restaurant name', 'location'])

    def test_export_with_choice_lists(self):
        fp = FormPack(**restaurant_profile)
        self.assertEqual(len(fp[1].translations), 2)
        # by default, exports use the question 'name' attribute
        options = {'version': 'rpV3'}

        export = fp.export(**options).to_dict()['submissions']
        self.assertEquals(export['fields'], ['restaurant_name',
                                              'location',
                                              'eatery_type'])
        self.assertEquals(export['data'], [['Taco Truck',
                                             '13.42 -25.43',
                                             'takeaway'],
                                            ['Harvest',
                                             '12.43 -24.53',
                                             'sit_down']])

        # if a language is passed, fields with available translations
        # are translated into that language
        options['translation'] = fp[1].translations[0]
        export = fp.export(**options).to_dict()['submissions']
        self.assertEquals(export['data'], [['Taco Truck',
                                            '13.42 -25.43',
                                            'take-away'],
                                           ['Harvest',
                                            '12.43 -24.53',
                                            'sit down']])

        options['translation'] = fp[1].translations[1]
        export = fp.export(**options).to_dict()['submissions']
        self.assertEquals(export['data'], [['Taco Truck',
                                            '13.42 -25.43',
                                            'avec vente à emporter'],
                                           ['Harvest',
                                            '12.43 -24.53',
                                            'traditionnel']])

    def test_headers_of_group_exports(self):
        grouped_questions = build_fixture('grouped_questions')
        fp = FormPack(**grouped_questions)
        options = {'version': 'gqs'}

        # by default, groups are stripped.
        export = fp.export(**options).to_dict()
        headers = export['submissions']['fields']
        self.assertEquals(headers, ['q1', 'g1q1', 'g1sg1q1',
                                    'g1q2', 'g2q1', 'qz'])

    def test_submissions_of_group_exports(self):
        grouped_questions = build_fixture('grouped_questions')
        fp = FormPack(**grouped_questions)
        options = {'version': 'gqs'}

        export = fp.export(**options).to_dict()['submissions']
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

        options['group_sep'] = '/'
        export = fp.export(**options).to_dict()['submissions']
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
        grouped_repeatable = build_fixture('grouped_repeatable')
        fp = FormPack(**grouped_repeatable)
        options = {'version': 'rgv1'}
        export = fp.export(**options).to_dict()

        self.assertEqual(export, OrderedDict ([
                            ('submissions',
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
                                            'submissions',
                                            1
                                        ],
                                        [
                                            'kyle',
                                            'submissions',
                                            2
                                        ],
                                        [
                                            'linda',
                                            'submissions',
                                            2
                                        ],
                                        [
                                            'morty',
                                            'submissions',
                                            3
                                        ],
                                        [
                                            'tony',
                                            'submissions',
                                            4
                                        ],
                                        [
                                            'mary',
                                            'submissions',
                                            4
                                        ],
                                        [
                                            'emma',
                                            'submissions',
                                            5
                                        ],
                                        [
                                            'parker',
                                            'submissions',
                                            5
                                        ],
                                        [
                                            'amadou',
                                            'submissions',
                                            6
                                        ],
                                        [
                                            'esteban',
                                            'submissions',
                                            6
                                        ],
                                        [
                                            'suzie',
                                            'submissions',
                                            6
                                        ],
                                        [
                                            'fiona',
                                            'submissions',
                                            6
                                        ],
                                        [
                                            'phillip',
                                            'submissions',
                                            6
                                        ]
                                    ]
                                })
                            ])
        )

    def test_csv(self):
        grouped_questions = build_fixture('grouped_questions')
        fp = FormPack(**grouped_questions)
        options = {'version': 'gqs'}
        csv_data = "\n".join(fp.export(**options).to_csv())

        expected = """
        "q1";"g1q1";"g1sg1q1";"g1q2";"g2q1";"qz"
        "respondent1's r1";"respondent1's r2";"respondent1's r2.5";"respondent1's r2.75 :)";"respondent1's r3";"respondent1's r4"
        "respondent2's r1";"respondent2's r2";"respondent2's r2.5";"respondent2's r2.75 :)";"respondent2's r3";"respondent2's r4"
        """

        self.assertTextEqual(csv_data, expected)

        fp = FormPack(**grouped_questions)
        options = {'version': 'gqs', 'group_sep': '/'}
        csv_data = "\n".join(fp.export(**options).to_csv())

        expected = """
        "q1";"g1/g1q1";"g1/sg1/g1sg1q1";"g1/g1q2";"g2/g2q1";"qz"
        "respondent1's r1";"respondent1's r2";"respondent1's r2.5";"respondent1's r2.75 :)";"respondent1's r3";"respondent1's r4"
        "respondent2's r1";"respondent2's r2";"respondent2's r2.5";"respondent2's r2.75 :)";"respondent2's r3";"respondent2's r4"
        """

        self.assertTextEqual(csv_data, expected)

        fp = FormPack(**grouped_questions)
        options = {'version': 'gqs', 'group_sep': '/',
                   'header_lang': "_default"}
        csv_data = "\n".join(fp.export(**options).to_csv())

        expected = """
        "Q1";"Group 1/G1Q1";"Group 1/Sub Group 1/G1SG1Q1";"Group 1/G1Q2";"g2/G2Q1";"QZed"
        "respondent1's r1";"respondent1's r2";"respondent1's r2.5";"respondent1's r2.75 :)";"respondent1's r3";"respondent1's r4"
        "respondent2's r1";"respondent2's r2";"respondent2's r2.5";"respondent2's r2.75 :)";"respondent2's r3";"respondent2's r4"
        """
        self.assertTextEqual(csv_data, expected)

        fp = FormPack(**restaurant_profile)
        options = {'version': 'rpV3', 'translation': fp[1].translations[1]}
        csv_data = "\n".join(fp.export(**options).to_csv())

        expected = """
        "nom du restaurant";"lieu";"type de restaurant"
        "Taco Truck";"13.42 -25.43";"avec vente à emporter"
        "Harvest";"12.43 -24.53";"traditionnel"
        """
        self.assertTextEqual(csv_data, expected)

    @raises(RuntimeError)
    def test_csv_on_repeatable_groups(self):
        grouped_repeatable = build_fixture('grouped_repeatable')
        fp = FormPack(**grouped_repeatable)
        options = {'version': 'rgv1'}
        list(fp.export(**options).to_csv())

    def test_export_with_multiple_select(self):
        fp = FormPack(**restaurant_profile)
        options = {'version': 'rpV4'}
        export = fp.export(**options).to_dict()['submissions']
        expected = {
            'fields': [
                'restaurant_name',
                'location',
                'eatery_type',
                'eatery_type/sit_down',
                'eatery_type/takeaway'
            ],
            'data': [
                [
                    'Taco Truck',
                    '13.42 -25.43',
                    'takeaway sit_down',
                    '1',
                    '1'
                ],
                [
                    'Harvest',
                    '12.43 -24.53',
                    'sit_down',
                    '1',
                    '0'
                ],
                [
                    'Wololo',
                    '12.43 -24.54',
                    '',
                    '0',
                    '0'
                ]
            ]
        }

        self.assertEqual(export, expected)

        options = {'version': 'rpV4', "group_sep": "::",
                   "header_lang": fp[-1].translations[1]}
        export = fp.export(**options).to_dict()['submissions']

        expected = {
            'fields': [
                'nom du restaurant',
                'lieu',
                'type de restaurant',
                'type de restaurant::traditionnel',
                'type de restaurant::avec vente à emporter'
            ],
            'data': [
                [
                    'Taco Truck',
                    '13.42 -25.43',
                    'takeaway sit_down',
                    '1',
                    '1'
                ],
                [
                    'Harvest',
                    '12.43 -24.53',
                    'sit_down',
                    '1',
                    '0'
                ],
                [
                    'Wololo',
                    '12.43 -24.54',
                    '',
                    '0',
                    '0'
                ]
            ]
        }

        self.assertEqual(export, expected)

    def test_xlsx(self):
        grouped_questions = build_fixture('grouped_repeatable')
        fp = FormPack(**grouped_questions)
        options = {'version': 'rgv1'}

        with tempdir() as d:
            xls = d / 'foo.xlsx'
            fp.export(**options).to_xlsx('/tmp/foo.xlsx')
            assert xls.isfile()

    def test_big_xlsx(self):
        grouped_questions = build_fixture('uga_14_v6')
        fp = FormPack(**grouped_questions)
        options = {'version': 'v1'}
        export = fp.export(**options)

        with tempdir() as d:
            xls = d / 'foo.xlsx'
            export.to_xlsx(xls)
            assert xls.isfile()

