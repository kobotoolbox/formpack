# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

import re
import string
import random
import unicodedata

try:
    unicode = unicode
    basestring = basestring
except NameError:  # Python 3
    unicode = str

str_types = (unicode, bytes)

from pyxform.xls2json import workbook_to_json
from pyxform.builder import create_survey_element_from_dict
from pyquery import PyQuery


def randstr(n):
    return ''.join(random.choice(string.ascii_lowercase + string.digits)
                   for _ in range(n))


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


# TODO: use a lib for that such as minibelt or ww
def normalize(string):
    r"""
        Returns a new string withou non ASCII characters, trying to replace
        them with their ASCII closest counter parts when possible.
        :Example:
            >>> normalize(u"H\xe9ll\xf8 W\xc3\xb6rld")
            'Hell World'
        This version use unicodedata and provide limited yet
        useful results.
    """
    string = unicodedata.normalize('NFKD', string).encode('ascii', 'ignore')
    return string.decode('ascii')


def slugify(string, separator=r'-'):
    r"""
    Slugify a unicode string using unicodedata to normalize the string.
    :Example:
        >>> slugify(u"H\xe9ll\xf8 W\xc3\xb6rld")
        'hell-world'
        >>> slugify("Bonjour, tout l'monde !", separator="_")
        'bonjour_tout_lmonde'
        >>> slugify("\tStuff with -- dashes and...   spaces   \n")
        'stuff-with-dashes-and-spaces'
    """

    string = normalize(string)
    string = re.sub(r'[^\w\s' + separator + ']', '', string, flags=re.U)
    string = string.strip().lower()
    return re.sub(r'[' + separator + '\s]+', separator, string, flags=re.U)
