# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)


from pyxform.xls2json import workbook_to_json
from pyxform.builder import create_survey_element_from_dict
from pyquery import PyQuery


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
