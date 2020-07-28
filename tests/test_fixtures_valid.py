# coding: utf-8
from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

import os
import json
import unittest

from glob import glob
from jsonschema import ValidationError

from a1d05eba1 import Content
from formpack import FormPack
from .fixtures import build_fixture

CURDIR = os.path.dirname(os.path.abspath(__file__))
JSONS_DIR = os.path.abspath(os.path.join(CURDIR, 'fixtures', 'json'))
GLOB_PATH = os.path.join(JSONS_DIR, '*.json')


class TestFormPackFixtures(unittest.TestCase):
    maxDiff = None

    def _reimport(self, fd):
        fd2 = FormPack(**fd.to_dict())
        return fd2

    def test_sanitation_report(self):
        """
        sanitation_report
        """
        title, schemas, submissions = build_fixture('sanitation_report')
        fp = FormPack(schemas)
        self.assertEqual(len(fp.versions), 1)
        v0 = fp[0]
        self.assertEqual(list(v0.sections['Sanitation report'].fields.keys()),
                         ['restaurant_name',
                          'restaurant_rating',
                          'report_date'])

    def test_grouped_questions(self):
        """
        questions groups
        """
        title, schemas, submissions = build_fixture('grouped_questions')
        fp = FormPack(schemas)
        self.assertEqual(len(fp.versions), 1)
        self.assertEqual(list(fp[0].sections['Grouped questions'].fields.keys()),
                         ['q1', 'g1q1', 'g1sg1q1', 'g1q2', 'g2q1', 'qz'])

    def test_customer_satisfaction(self):
        """
        customer_satisfaction
        """
        title, schemas, submissions = build_fixture('customer_satisfaction')
        fp = FormPack(schemas)
        v0 = fp[0]
        self.assertEqual(len(fp.versions), 1)
        self.assertEqual(list(v0.sections['Customer Satisfaction'].fields.keys()),
                         ['restaurant_name', 'customer_enjoyment'])
        self.assertEqual(sorted(fp.to_dict().keys()),
                         ['id_string', 'title', 'versions'])
        # TODO: find a way to restore this test (or change fixtures)
        # self.assertEqual(fp.to_dict(), {'title': 'Customer Satisfaction',
        #                                 'id_string': 'customer_satisfaction',
        #                                 'versions': schemas})

    def test_restaurant_profile(self):
        title, schemas, submissions = build_fixture('restaurant_profile')
        fp = FormPack(schemas)
        self.assertEqual(len(fp.versions), 4)
        v0 = fp[0]
        self.assertEqual(list(v0.sections['Restaurant profile'].fields.keys()),
                         ['restaurant_name', 'location'])

        self.assertEqual(sorted(fp.to_dict().keys()),
                         sorted(['id_string', 'title', 'versions']))
        # TODO: find a way to restore this test (or change fixtures)
        # self.assertEqual(fp.to_dict(), {'title': 'Restaurant profile',
        #                                 'id_string': 'restaurant_profile',
        #                                 'versions': schemas})

    def test_site_inspection(self):
        title, schemas, submissions = build_fixture('site_inspection')
        fp = FormPack(schemas)
        self.assertEqual(len(fp.versions), 5)
        v0 = fp[0]
        self.assertEqual(
            list(v0.sections['Site inspection'].fields.keys()), [
                'inspector',
                'did_you_find_the_site',
                'was_there_damage_to_the_site',
                'was_there_damage_to_the_site_dupe',
                'ping',
                'rssi',
                'is_the_gate_secure',
                'is_plant_life_encroaching',
                'please_rate_the_impact_of_any_defects_observed',
            ]
        )

        v_out = fp.to_version_list()
        assert v_out == [Content(s).export(flat=False)
                         for s in schemas]


def _each_fixture():
    outs = []
    for jfpath in glob(GLOB_PATH):
        if jfpath.endswith('_old.json'):
            continue
        filename = os.path.split(jfpath)[-1]
        with open(jfpath, 'r') as ff:
            versions = json.loads(ff.read()).get('versions')
            outs.append(
                (jfpath, filename, versions,)
            )
    for out in outs:
        yield out


def test_new_jsons():
    assert os.path.exists(JSONS_DIR)
    for (filepath, filename, versions) in _each_fixture():
        needs_update = False
        for version_content in versions:
            try:
                Content(version_content, validate=True)
            except ValidationError as err:
                vmessage = 'fixtures/json/{} : {}'.format(filename, err.message)
                raise ValidationError(vmessage)
