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
        fp = FormPack(**sanitation_report)
        self.assertEqual(len(fp.versions), 1)
        self.assertEqual(fp.submissions_count(), 4)
        v0 = fp[0]
        self.assertEqual(list(v0.sections['submissions']['fields'].keys()),
                         ['restaurant_name',
                          'restaurant_rating',
                          'report_date'])

    def test_grouped_questions(self):
        '''
        questions groups
        '''
        fp = FormPack(**build_fixture('grouped_questions'))
        self.assertEqual(len(fp.versions), 1)
        self.assertEqual(fp.submissions_count(), 2)
        self.assertEqual(list(fp[0].sections['submissions']['fields'].keys()),
                         ['q1', 'g1q1', 'g1sg1q1', 'g1q2', 'g2q1', 'qz'])

    def test_customer_satisfaction(self):
        '''
        customer_satisfaction
        '''
        fxt = customer_satisfaction
        fp = FormPack(**customer_satisfaction)
        v0 = fp[0]
        self.assertEqual(len(fp.versions), 1)
        self.assertEqual(fp.submissions_count(), 3)
        self.assertEqual(list(v0.sections['submissions']['fields'].keys()),
                         [u'restaurant_name', u'customer_enjoyment'])
        self.assertEqual(sorted(fp.to_dict().keys()),
                         sorted(fxt.keys()))
        self.assertEqual(fp.to_dict(), fxt)
        self.assertEqual(fp.to_dict(), customer_satisfaction)

    def test_restaurant_profile(self):
        fxt = restaurant_profile
        fp = FormPack(**fxt)
        self.assertEqual(len(fp.versions), 3)
        v0 = fp[0]
        self.assertEqual(list(v0.sections['submissions']['fields'].keys()),
                         [u'restaurant_name', u'location'])

        self.assertEqual(sorted(fp.to_dict().keys()),
                         sorted(fxt.keys()))

        self.assertEqual(fp.to_dict(), fxt)

        v0.submit([u'Dominos', u'-12.22 12.22'])
        v0.submit(restaurant_name=u'Boston Market', location=u'-13.22 13.22')
        v0.submit({u'restaurant_name': u'Starbx', u'location': u'-11.2 11.2'})
        self.assertEqual(fp.to_dict(), self._reimport(fp).to_dict())

    def test_xml_instances_loaded(self):
        '''
        favcolor has submissions_xml specified
        '''
        fp = FormPack(**favcolor)
        self.assertEqual(len(fp.versions), 2)
        self.assertGreater(fp.submissions_count(), 0,
                           'submission count should be > 0')
