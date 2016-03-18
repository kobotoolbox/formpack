# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

import unittest

from collections import OrderedDict

from ..models.formpack.pack import FormPack
from ..fixtures import build_fixture


customer_satisfaction = build_fixture('customer_satisfaction')
restaurant_profile = build_fixture('restaurant_profile')


class TestFormPackExport(unittest.TestCase):
    maxDiff = None

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
        self.assertEqual(len(fp.versions), 3)
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
                            (u'submissions',
                                {
                                    u'fields': [
                                        u'household_location',
                                        u'start',
                                        u'end',
                                        u'_index'
                                    ],
                                    u'data': [
                                        [
                                            u'montreal',
                                            u'2016-03-14T14:15:48.000-04:00',
                                            u'2016-03-14T14:18:35.000-04:00',
                                            1
                                        ],
                                        [
                                            u'marseille',
                                            u'2016-03-14T14:14:10.000-04:00',
                                            u'2016-03-14T14:15:48.000-04:00',
                                            2
                                        ],
                                        [
                                            u'rocky mountains',
                                            u'2016-03-14T14:13:53.000-04:00',
                                            u'2016-03-14T14:14:10.000-04:00',
                                            3
                                        ],
                                        [
                                            u'toronto',
                                            u'2016-03-14T14:12:54.000-04:00',
                                            u'2016-03-14T14:13:53.000-04:00',
                                            4
                                        ],
                                        [
                                            u'new york',
                                            u'2016-03-14T14:18:35.000-04:00',
                                            u'2016-03-14T15:19:20.000-04:00',
                                            5
                                        ],
                                        [
                                            u'boston',
                                            u'2016-03-14T14:11:25.000-04:00',
                                            u'2016-03-14T14:12:03.000-04:00',
                                            6
                                        ]
                                    ]
                                }),
                            (u'houshold_member_repeat',
                                {
                                    u'fields': [
                                        u'household_member_name',
                                        u'_parent_table_name',
                                        u'_parent_index'
                                    ],
                                    u'data': [
                                        [
                                            u'peter',
                                            u'submissions',
                                            1
                                        ],
                                        [
                                            u'kyle',
                                            u'submissions',
                                            2
                                        ],
                                        [
                                            u'linda',
                                            u'submissions',
                                            2
                                        ],
                                        [
                                            u'morty',
                                            u'submissions',
                                            3
                                        ],
                                        [
                                            u'tony',
                                            u'submissions',
                                            4
                                        ],
                                        [
                                            u'mary',
                                            u'submissions',
                                            4
                                        ],
                                        [
                                            u'emma',
                                            u'submissions',
                                            5
                                        ],
                                        [
                                            u'parker',
                                            u'submissions',
                                            5
                                        ],
                                        [
                                            u'amadou',
                                            u'submissions',
                                            6
                                        ],
                                        [
                                            u'esteban',
                                            u'submissions',
                                            6
                                        ],
                                        [
                                            u'suzie',
                                            u'submissions',
                                            6
                                        ],
                                        [
                                            u'fiona',
                                            u'submissions',
                                            6
                                        ],
                                        [
                                            u'phillip',
                                            u'submissions',
                                            6
                                        ]
                                    ]
                                })
                            ])
        )
