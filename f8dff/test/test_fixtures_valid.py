# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

import unittest

from ..models.formpack.pack import FormPack
from ..fixtures import build_fixture


sanitation_report = build_fixture('sanitation_report')
customer_satisfaction = build_fixture('customer_satisfaction')
restaurant_profile = build_fixture('restaurant_profile')
favcolor = build_fixture('favcolor')


class TestFormPackFixtures(unittest.TestCase):
    maxDiff = None

    def _reimport(self, fd):
        fd2 = FormPack(**fd.to_dict())
        return fd2

    def test_sanitation_report(self):
        '''
        sanitation_report
        '''
        title, schemas, submissions = sanitation_report
        fp = FormPack(schemas, title)
        self.assertEqual(len(fp.versions), 1)
        v0 = fp[0]
        self.assertEqual(list(v0.sections['submissions'].fields.keys()),
                         ['restaurant_name',
                          'restaurant_rating',
                          'report_date'])

    def test_grouped_questions(self):
        '''
        questions groups
        '''
        title, schemas, submissions = build_fixture('grouped_questions')
        fp = FormPack(schemas, title)
        self.assertEqual(len(fp.versions), 1)
        self.assertEqual(list(fp[0].sections['submissions'].fields.keys()),
                         ['q1', 'g1q1', 'g1sg1q1', 'g1q2', 'g2q1', 'qz'])

    def test_customer_satisfaction(self):
        '''
        customer_satisfaction
        '''
        title, schemas, submissions = customer_satisfaction
        fp = FormPack(schemas, title)
        v0 = fp[0]
        self.assertEqual(len(fp.versions), 1)
        self.assertEqual(list(v0.sections['submissions'].fields.keys()),
                         [u'restaurant_name', u'customer_enjoyment'])
        self.assertEqual(sorted(fp.to_dict().keys()),
                         [u'id_string', u'title', u'versions'])
        self.assertEqual(fp.to_dict(), {u'title': u'Customer Satisfaction',
                                        u'id_string': u'customer_satisfaction',
                                        u'versions': schemas})

    def test_restaurant_profile(self):
        title, schemas, submissions = restaurant_profile
        fp = FormPack(schemas, title)
        self.assertEqual(len(fp.versions), 4)
        v0 = fp[0]
        self.assertEqual(list(v0.sections['submissions'].fields.keys()),
                         [u'restaurant_name', u'location'])

        self.assertEqual(sorted(fp.to_dict().keys()),
                         sorted([u'id_string', u'title', u'versions']))

        self.assertEqual(fp.to_dict(), {u'title': u'Restaurant profile',
                                        u'id_string': u'restaurant_profile',
                                        u'versions': schemas})

    # TODO: update this test, it doesn't test anything anymore.
    def test_xml_instances_loaded(self):
        '''
        favcolor has submissions_xml specified
        '''
        fp = FormPack(**favcolor)
        self.assertEqual(len(fp.versions), 2)

