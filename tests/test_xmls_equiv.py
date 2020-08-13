import os
import sys
import json

from .fixtures.build_fixture import build_fixture

from formpack import FormPack
from formpack.content import Content

CURDIR = os.path.dirname(os.path.abspath(__file__))
XMLS_DIR = os.path.abspath(os.path.join(CURDIR, 'fixtures', 'xml'))
V2_FIXDIR = os.path.abspath(os.path.join(CURDIR, 'v2_fixtures'))

def mkdir_p(dirpath):
    if not os.path.exists(dirpath):
        os.mkdir(dirpath)
    return dirpath


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
    'favorite_coffee',
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

def test_xml_equivs():
    for module in MODULES:
        (title, versions, submissions) = build_fixture(module)
        fp = FormPack(versions)
        for (index, vkey) in enumerate(fp.versions.keys()):
            fversion = fp.versions[vkey]
            expected_xml_f = os.path.join(XMLS_DIR,
                                          '{}_v{}.xml'.format(module, index))
            with open(expected_xml_f, 'r') as ff:
                expected_xml = ff.read()
            xml_output = fversion.to_xml()
            assert xml_output == expected_xml
