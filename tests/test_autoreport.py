# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

import unittest

from formpack import FormPack
from .fixtures import build_fixture


class TestAutoReport(unittest.TestCase):

    maxDiff = None

    def test_list_fields_on_packs(self):

        title, schemas, submissions = build_fixture('restaurant_profile')
        fp = FormPack(schemas, title)

        fields = fp.get_fields_for_versions()

        field_names = [field.name for field in fields]
        assert field_names == ['restaurant_name', 'location', 'eatery_type']

        field_types = [field.__class__.__name__ for field in fields]
        assert field_types == ['TextField', 'FormGPSField',
                               'FormChoiceFieldWithMultipleSelect']

    def test_simple_report(self):

        title, schemas, submissions = build_fixture('restaurant_profile')
        fp = FormPack(schemas, title)

        report = fp.autoreport()
        stats = report.get_stats(submissions, lang='french')

        assert list(stats) == [
            ('nom du restaurant',
                  {'frequency': [('Taco Truck', 1),
                                    ('Harvest', 1),
                                    ('Los pollos hermanos', 1),
                                    ('Wololo', 1)],
                  'not_provided': 0,
                  'percentage': [('Taco Truck', '25.00'),
                                    ('Harvest', '25.00'),
                                    ('Los pollos hermanos', '25.00'),
                                    ('Wololo', '25.00')],
                  'provided': 4,
                  'show_graph': False,
                  'total_count': 4}),
            ('lieu',
                  {'not_provided': 0,
                  'provided': 4,
                  'show_graph': False,
                  'total_count': 4}),
            ('type de restaurant',
                  {'frequency': [('traditionnel', 2), ('avec vente \xe0 emporter', 1)],
                  'not_provided': 1,
                  'percentage': [('traditionnel', '50.00'),
                                    ('avec vente \xe0 emporter', '25.00')],
                  'provided': 3,
                  'show_graph': True,
                  'total_count': 4})
         ]

    def test_rich_report(self):

        title, schemas, submissions = build_fixture('auto_report')
        fp = FormPack(schemas, title)

        report = fp.autoreport()
        stats = report.get_stats(submissions)

        assert list(stats) == [
            ('restaurant_name',
                  {'frequency': [('Felipes', 2),
                                 ('The other one', 2),
                                   ('That one', 1)],
                   'not_provided': 1,
                   'percentage': [('Felipes', '33.33'),
                                   ('The other one', '33.33'),
                                   ('That one', '16.67')],
                   'provided': 5,
                   'show_graph': False,
                   'total_count': 6}),
            ('location',
                  {'not_provided': 1,
                   'provided': 5,
                   'show_graph': False,
                   'total_count': 6}),
            ('when',
                  {'frequency': [('2001-01-01', 2),
                                  ('2002-01-01', 2),
                                  ('2003-01-01', 1)],
                   'not_provided': 1,
                   'percentage': [('2001-01-01', '33.33'),
                                    ('2002-01-01', '33.33'),
                                    ('2003-01-01', '16.67')],

                   'provided': 5,
                   'show_graph': True,
                   'total_count': 6}),
            ('howmany',
                  {'mean': 1.6,
                   'median': 2,
                   'mode': 2,
                   'not_provided': 1,
                   'provided': 5,
                   'show_graph': False,
                   'stdev': 0.5477225575051661,
                   'total_count': 6})
        ]

    def test_aggregate(self):

            title, schemas, submissions = build_fixture('auto_report')
            fp = FormPack(schemas, title)

            report = fp.autoreport()
            stats = report.get_stats(submissions, group_by="when")

            assert list(stats) == [
                (
                    'restaurant_name',
                    [
                        (
                             '2003-01-01',
                             {
                                'frequency': [('That one', 1)],
                                'not_provided': 0,
                                'percentage': [('That one', '100.00')],
                                'provided': 1,
                                'show_graph': False,
                                'total_count': 1
                             }
                        ),
                        (
                            '2001-01-01',
                            {
                                'frequency': [('Felipes', 2)],
                                'not_provided': 0,
                                'percentage': [('Felipes', '100.00')],
                                'provided': 2,
                                'show_graph': False,
                                'total_count': 2
                            }
                        ),
                        (
                            '2002-01-01',
                            {
                                'frequency': [('The other one', 2)],
                                'not_provided': 0,
                                'percentage': [('The other one', '100.00')],
                                'provided': 2,
                                'show_graph': False,
                                'total_count': 2
                            }
                        ),
                        (
                            None,
                            {
                                'frequency': [],
                                'not_provided': 1,
                                'percentage': [],
                                'provided': 0,
                                'show_graph': False,
                                'total_count': 1
                            }
                        )
                    ]
                ),
                (
                    'location',
                    [
                        (
                            '2003-01-01',
                            {
                                'not_provided': 0,
                                'provided': 1,
                                'show_graph': False,
                                'total_count': 1
                            }
                        ),
                        (
                            '2001-01-01',
                            {
                                'not_provided': 0,
                                'provided': 2,
                                'show_graph': False,
                                'total_count': 2
                            }
                        ),
                        (
                            '2002-01-01',
                            {
                                'not_provided': 0,
                                'provided': 2,
                                'show_graph': False,
                                'total_count': 2
                            }
                        ),
                        (
                            None,
                            {
                                'not_provided': 1,
                                'provided': 0,
                                'show_graph': False,
                                'total_count': 1
                            }
                        )
                    ]
                ),

                (
                    'howmany',
                    [
                        (
                            '2003-01-01',
                            {
                                'mean': 1.0,
                                'median': 1,
                                'mode': '<N/A>',
                                'not_provided': 0,
                                'provided': 1,
                                'show_graph': False,
                                'stdev': '<N/A>',
                                'total_count': 1
                            }
                        ),
                        (
                            '2001-01-01',
                            {
                                'mean': 1.5,
                                'median': 1.5,
                                'mode': '<N/A>',
                                'not_provided': 0,
                                'provided': 2,
                                'show_graph': False,
                                'stdev': 0.7071067811865476,
                                'total_count': 2
                            }
                        ),
                        (
                            '2002-01-01',
                            {
                                'mean': 2.0,
                                'median': 2.0,
                                'mode': 2,
                                'not_provided': 0,
                                'provided': 2,
                                'show_graph': False,
                                'stdev': 0.0,
                                'total_count': 2
                            }
                        ),
                        (
                            None,
                            {
                                'mean': '<N/A>',
                                'median': '<N/A>',
                                'mode': '<N/A>',
                                'not_provided': 1,
                                'provided': 0,
                                'show_graph': False,
                                'stdev': '<N/A>',
                                'total_count': 1
                            }
                        )
                    ]
                )
            ]
