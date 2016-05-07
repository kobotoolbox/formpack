# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

import unittest
import pytest

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

        stats = [(repr(f), n, d) for f, n, d in stats]

        assert list(stats) == [
            (
             "<TextField name='restaurant_name' type='text'>",
             'nom du restaurant',
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
            (
             "<FormGPSField name='location' type='geopoint'>",
             'lieu',
                  {'not_provided': 0,
                  'provided': 4,
                  'show_graph': False,
                  'total_count': 4}),
            (
             "<FormChoiceFieldWithMultipleSelect name='eatery_type' type='select_multiple'>",
             'type de restaurant',
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

        stats = [(repr(f), n, d) for f, n, d in stats]

        assert list(stats) == [
            (
             "<TextField name='restaurant_name' type='text'>",
             'restaurant_name',
                  {'frequency': [('Felipes', 2),
                                 ('The other one', 2),
                                   ('That one', 1)],
                   'not_provided': 1,
                   'percentage': [('Felipes', '33.33'),
                                   ('The other one', '33.33'),
                                   ('That one', '16.67')],
                   'provided': 5,
                   'show_graph': False,
                   'total_count': 6}
            ),
            (
             "<FormGPSField name='location' type='geopoint'>",
             'location',
                  {'not_provided': 1,
                   'provided': 5,
                   'show_graph': False,
                   'total_count': 6}
            ),
            (
             "<DateField name='when' type='date'>",
             'when',
                  {'frequency': [('2001-01-01', 2),
                                  ('2002-01-01', 2),
                                  ('2003-01-01', 1)],
                   'not_provided': 1,
                   'percentage': [('2001-01-01', '33.33'),
                                    ('2002-01-01', '33.33'),
                                    ('2003-01-01', '16.67')],

                   'provided': 5,
                   'show_graph': True,
                   'total_count': 6}
            ),
            (
             "<NumField name='howmany' type='integer'>",
             'howmany',
                  {'mean': 1.6,
                   'median': 2,
                   'mode': 2,
                   'not_provided': 1,
                   'provided': 5,
                   'show_graph': False,
                   'stdev': 0.5477225575051661,
                   'total_count': 6}
            )
        ]


    def test_disaggregate(self):
            title, schemas, submissions = build_fixture('auto_report')
            fp = FormPack(schemas, title)

            report = fp.autoreport()
            stats = report.get_stats(submissions, split_by="when")

            stats = [(repr(f), n, d) for f, n, d in stats]

            assert list(stats) == [
                          (
                            "<TextField name='restaurant_name' type='text'>",
                            'restaurant_name',
                            {
                              'not_provided': 1,
                              'provided': 5,
                              'show_graph': False,
                              'total_count': 6,
                              'values': [
                              (None,
                                {
                                  'frequency': [], 'percentage': []
                                }),
                                ('That one',
                                {
                                  'frequency': [('2003-01-01', 1 ) ],
                                  'percentage': [('2003-01-01', '16.67') ]
                                }),
                                ('Felipes',
                                {
                                  'frequency': [('2001-01-01', 2 ) ],
                                  'percentage': [('2001-01-01', '33.33') ]
                                }),
                                ('The other one',
                                {
                                  'frequency': [('2002-01-01', 2 ) ],
                                  'percentage': [('2002-01-01', '33.33') ]
                                })
                              ]
                            }
                          ),
                          (
                            "<FormGPSField name='location' type='geopoint'>",
                            'location',
                            {
                              'not_provided': 1,
                              'provided': 5,
                              'show_graph': False,
                              'total_count': 6
                            }
                          ),
                          (
                            "<NumField name='howmany' type='integer'>",
                            'howmany',
                            {
                              'not_provided': 1,
                              'provided': 5,
                              'show_graph': False,
                              'total_count': 6,
                              'values': (
                                (
                                  '2001-01-01',
                                  {
                                    'mean': 1.5,
                                    'median': 1.5,
                                    'mode': '<N/A>',
                                    'stdev': 0.7071067811865476
                                  }
                                ),
                                (
                                  '2002-01-01',
                                  {
                                    'mean': 2.0,
                                    'median': 2.0,
                                    'mode': 2,
                                    'stdev': 0.0
                                  }
                                ),
                                (
                                  '2003-01-01',
                                  {
                                    'mean': 1.0,
                                    'median': 1,
                                    'mode': '<N/A>',
                                    'stdev': '<N/A>'
                                  }
                                )
                              )
                            }
                          )
                        ]
