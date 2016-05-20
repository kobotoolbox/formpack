# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

import re

from pyxform.xls2json import workbook_to_json
from pyxform.builder import create_survey_element_from_dict
from pyquery import PyQuery


DATA_TYPE_ALIASES = (
    ("add select one prompt using", 'select_one'),
    ("select one from", 'select_one'),
    ("select1", 'select_one'),
    ("select one", 'select_one'),
    ("add select multiple prompt using", 'select_multiple'),
    ("select all that apply from", 'select_multiple'),
    ("select multiple", 'select_multiple'),
    ("select all that apply", 'select_multiple'),
    ("select_one_external", "select one external"),
    ('cascading select', 'cascading_select'),
    ('location', 'geopoint'),
    ("begin lgroup", 'begin_repeat'),
    ("end lgroup", 'end_repeat'),
    ("begin group", 'begin_group'),
    ("end group", 'end_group'),
    ("begin repeat", 'begin_repeat'),
    ("end repeat", 'end_repeat'),
    ("begin looped group", 'begin_repeat'),
    ("end looped group", 'end_repeat'),
)


def formversion_pyxform(data):
    content = data.get('content')
    imported_survey_json = workbook_to_json(content)
    return create_survey_element_from_dict(imported_survey_json)


def get_version_identifiers(node):
    pqi = PyQuery(node)
    return (pqi.attr('id_string'), pqi.attr('version'))


def parse_xml_to_xmljson(node):
    pqi = PyQuery(node)
    items = pqi[0].attrib
    out = {'tag': pqi[0].tag}
    if len(items) > 0:
        out['attributes'] = dict(items)
    if len(pqi.children()) > 0:
        out['children'] = []
        for child in pqi.children():
            out['children'].append(parse_xml_to_xmljson(child))
    else:
        out['text'] = pqi.text()
    return out


def parse_xmljson_to_data(data, parent_tags=[], output=[]):
    tag = data.get('tag')
    new_parents = parent_tags + [tag]
    if len(data.get('children', [])) > 0:
        for child in data.get('children'):
            parse_xmljson_to_data(child, new_parents, output)
    else:
        key = '/' + '/'.join(parent_tags) + '/' + tag
        val = data.get('text')
        output.append((key, val,))
    return output


def parse_xml_to_data(xml_str):
    xmljson = parse_xml_to_xmljson(xml_str)
    return parse_xmljson_to_data(xmljson)


def normalize_data_type(data_type):
    """ Normalize spaces and aliases for field data types """

    # normalize spaces
    data_type = ' '.join(data_type.split())

    # replace some common data_type aliases
    for alias, standard in DATA_TYPE_ALIASES:
        if data_type.startswith(alias):
            data_type = re.sub('^%s' % alias, standard, data_type)
            break

    return data_type
