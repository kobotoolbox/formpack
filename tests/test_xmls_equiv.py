import os
from os.path import join as _join
import sys

import json

from a1d05eba1 import Content
from a1d05eba1.utils.form_to_yaml_string import form_to_yaml_string

CURDIR = os.path.dirname(os.path.abspath(__file__))
XMLS_DIR = os.path.abspath(_join(CURDIR, 'fixtures', 'xml'))
V2_FIXDIR = os.path.abspath(_join(CURDIR, 'v2_fixtures'))

def mkdir_p(dirpath):
    if not os.path.exists(dirpath):
        os.mkdir(dirpath)
    return dirpath

from .fixtures.build_fixture import build_fixture
from formpack import FormPack


import shutil

MODULES = [
    'literacy_test',
    'nested_grouped_repeatable',
    'grouped_translated',
    'long_unicode_labels',
    'restaurant_profile',
    'all_geo_types',
    'auto_report',
    'auto_report_extended_fields',
    'customer_satisfaction',
    'dietary_needs',
    'favorite_coffee', # missing fixture file
    'field_position_with_multiple_versions',
    'fields_for_versions_list_index_out_of_range',
    'grouped_questions',
    'grouped_repeatable',
    'grouped_repeatable_alias',
    'hxl_grouped_repeatable',
    'long_names',
    'quotes_newlines_and_long_urls',
    'sanitation_report',
    'site_inspection',
    ]

import os

def test_xml_equivs():
    # print()
    # print('xml equivs:')

    for (zinx, mn) in enumerate(MODULES):
        (title, versions, submissions) = build_fixture(mn)
        fp = FormPack(versions)
        # print('\t-', mn)
        for (index, vkey) in enumerate(fp.versions.keys()):
            fversion = fp.versions[vkey]
            expected_xml_f = _join(XMLS_DIR, '{}_v{}.xml'.format(mn, index))

            with open(expected_xml_f, 'r') as ff:
                expected_xml = ff.read()
            xml_output = fversion.to_xml()
            assert xml_output == expected_xml
            # print('\t\t', index, ' ', mn,)
