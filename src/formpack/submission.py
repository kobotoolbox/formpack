# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

import re
import json

from collections import OrderedDict
from lxml import etree

try:
    from cStringIO import StringIO
except ImportError:  # we are on Python 3
    from io import StringIO

from pyquery import PyQuery

from .b64_attachment import B64Attachment
from .utils import parse_xmljson_to_data


class FormSubmission:
    def __init__(self, submission_data=None, version=None):
        self.data = submission_data or {}
        self._version = version

        for key in submission_data:
            val = submission_data[key]
            if B64Attachment._is_attachment(val):
                submission_data[key] = B64Attachment(val)

    def to_dict(self):
        return self.data

    def to_xml_struct(self, files=False):
        def _item_to_struct(item):
            (key, val,) = item
            if isinstance(val, list):
                val = map(_item_to_struct, val)
            elif isinstance(val, B64Attachment) and files is not False:
                (fname, fpath) = B64Attachment.write_to_tempfile(
                                                        val)
                files.append([fname, fpath])
                val = fname
            return {'tag': key, 'attributes': {}, 'children': val}
        return {
            'tag': self._version._root_node_name or 'data',
            'attributes': {
                'id_string': self._version.id_string,
                'version': self._version._version_id,
            },
            'children': [_item_to_struct(item)
                         for item in self.data.iteritems()],
        }

    def to_xml(self, files=False):
        return xmljson_to_xml(self.to_xml_struct(files))

    def to_xml_export(self):
        files = []
        return (self.to_xml(), files)

    @classmethod
    def from_xml(kls, xml, version=None):
        xmljson = OrderedDict(parse_xmljson_to_data(xml, [], []))
        return kls(xmljson, version)


class NestedStruct(OrderedDict):
    def get(self, key):
        if key not in self:
            self[key] = NestedStruct()
        return self[key]

    def to_json(self):
        return json.dumps(self, indent=4)

    def to_xml(self):
        (_tag, contents) = list(self.iteritems())[0]
        pqi = PyQuery('<wrap />')

        def _append_contents(struct, par):
            tag = struct['tag']
            _node = PyQuery('<%s />' % tag)
            if 'attributes' in struct:
                for key in struct['attributes'].keys():
                    _node.attr(key, struct['attributes'][key])
            if 'text' in struct:
                _node.text(struct['text'])
            elif 'children' in struct:
                for (ugh, child) in struct['children'].iteritems():
                    _append_contents(child, _node)
            par.append(_node)

        _append_contents(contents, pqi)
        _xio = StringIO(pqi.html())
        _parsed = etree.parse(_xio)
        return etree.tostring(_parsed, pretty_print=True)

    @classmethod
    def from_abspaths(kls, par_item):
        items_ns = NestedStruct()
        for child in par_item.get('children'):
            tag = child.get('tag')
            layers = re.sub(r'^\/', '', tag).split('/')
            outer_layer = layers[-1]
            layers = layers[0:-1]
            cur_ptr = items_ns
            for _layer in layers:
                cur_ptr = cur_ptr.get(_layer)
                cur_ptr['tag'] = _layer
                cur_ptr = cur_ptr.get('children')
            cur_ptr[outer_layer] = {'tag': outer_layer,
                                    'text': child.get('children')}
        return items_ns


def xmljson_to_xml(xmljson):
    return NestedStruct.from_abspaths(xmljson).to_xml()
