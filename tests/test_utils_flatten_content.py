# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

import unittest
from collections import OrderedDict
from formpack.constants import OR_OTHER_COLUMN
from formpack.utils.xls_to_ss_structure import _parsed_sheet
from formpack.utils.flatten_content import flatten_content
from formpack.utils.json_hash import json_hash


class TestXlsToSpreadsheetStructure(unittest.TestCase):
    def _to_dicts(self, list_of_ordered_dicts):
        # convert OrderedDicts to dicts
        return [dict(d) for d in list_of_ordered_dicts]

    def test_internal_method_parsed_sheet_normal(self):
        '''
        in xls_to_ss_structure, the internal method
        _parsed_sheet(...) accepts a list of lists and
        returns a list of dicts
        '''
        sheet_dicts = _parsed_sheet([['h1', 'h2'],
                                     ['r1v1', 'r1v2'],
                                     ['r2v1', 'r2v2']])
        sheet_dicts = self._to_dicts(sheet_dicts)

        self.assertEqual(sheet_dicts, [
                {'h1': 'r1v1', 'h2': 'r1v2'},
                {'h1': 'r2v1', 'h2': 'r2v2'},
            ])

    def test_internal_method_parsed_sheet_normal(self):
        '''
        edge cases:
         * sheet has only column headers (no values)
         * sheet has no rows
        should return an empty list
        '''
        sheet_dicts = self._to_dicts(_parsed_sheet([['h1', 'h2']]))
        self.assertEqual(sheet_dicts, [])

        sheet_dicts = self._to_dicts(_parsed_sheet([]))
        self.assertEqual(sheet_dicts, [])


class TestNestedStructureToFlattenedStructure(unittest.TestCase):
    def _wrap_field(self, field_name, value):
        return {'survey': [
            {'type': 'text', 'name': 'x'},
            {'type': 'text', 'name': 'y', field_name: value},
        ]}

    def _wrap_type(self, type_val):
        return {'survey': [{
            'type': type_val,
            'name': 'q_yn',
            'label': 'Yes or No',
        }], 'choices': [
            {'list_name': 'yn', 'name': 'y', 'label': 'Yes'},
            {'list_name': 'yn', 'name': 'n', 'label': 'No'},
        ]}

    def test_flatten_select_type(self):
        s1 = {'survey': [{'type': 'select_multiple',
                          'select_from_list_name': 'xyz'}]}
        flatten_content(s1, in_place=True)
        row0 = s1['survey'][0]
        assert row0['type'] == 'select_multiple xyz'
        assert 'select_from_list_name' not in row0

    def test_flatten_select_or_other(self):
        s1 = {'survey': [{'type': 'select_one_or_other',
                          'select_from_list_name': 'xyz'}]}
        flatten_content(s1, in_place=True)
        row0 = s1['survey'][0]
        assert row0['type'] == 'select_one xyz or_other'
        assert 'select_from_list_name' not in row0

    def test_flatten_select(self):
        s1 = {'survey': [{'type': 'select_one',
                          'select_from_list_name': 'aaa'}]}
        flatten_content(s1, in_place=True)
        row0 = s1['survey'][0]
        assert row0['type'] == 'select_one aaa'
        assert 'select_from_list_name' not in row0

    def test_flatten_empty_relevant(self):
        a1 = self._wrap_field('relevant', [])
        flatten_content(a1, in_place=True)
        ss_struct = a1['survey']
        self.assertEqual(ss_struct[1]['relevant'], '')

    def test_flatten_relevant(self):
        a1 = self._wrap_field('relevant', [{'@lookup': 'x'}])
        flatten_content(a1, in_place=True)
        ss_struct = a1['survey']
        self.assertEqual(ss_struct[1]['relevant'], '${x}')

    def test_flatten_constraints(self):
        a1 = self._wrap_field('constraint', ['.', '>', {'@lookup': 'x'}])
        flatten_content(a1, in_place=True)
        ss_struct = a1['survey']
        self.assertEqual(ss_struct[1]['constraint'], '. > ${x}')

    def test_flatten_select_one_type_deprecated_format(self):
        a1 = self._wrap_type({'select_one': 'yn'})
        flatten_content(a1, in_place=True)
        ss_struct = a1['survey']
        self.assertEqual(ss_struct[0]['type'], 'select_one yn')

    def test_flatten_select_multiple_type(self):
        a1 = self._wrap_type({'select_multiple': 'yn'})
        flatten_content(a1, in_place=True)
        ss_struct = a1['survey']
        self.assertEqual(ss_struct[0]['type'], 'select_multiple yn')


def test_json_hash():
    # consistent output
    assert json_hash({'a': 'z', 'b': 'y', 'c': 'x'}) == 'f6117d60'

    # second parameter is size of string
    val = json_hash(['abc'], 35)
    assert len(val) == 35

    # even OrderedDicts have the keys reordered
    assert json_hash(OrderedDict([
            ('c', 'x'),
            ('b', 'y'),
            ('a', 'z'),
        ])) == json_hash(OrderedDict([
            ('a', 'z'),
            ('b', 'y'),
            ('c', 'x'),
        ]))

    # identical objects match (==)
    assert json_hash({'d': 1, 'e': 2, 'f': 3}) == json_hash({'d': 1,
                                                             'e': 2,
                                                             'f': 3})
    # types don't match (1 != '1')
    assert json_hash({'d': 1, 'e': 2, 'f': 3}) != json_hash({'d': '1',
                                                             'e': '2',
                                                             'f': '3'})


# should be test_flatten
from formpack.utils.spreadsheet_content import (flatten_to_spreadsheet_content,
                                                _order_cols,
                                                _order_sheet_names)

import pytest
from collections import OrderedDict


def test_flatten_fails_with_too_many_translations_listed():
    with pytest.raises(ValueError) as err:
        flatten_content({'survey': [
                {'type': 'text', 'name': 'q1',
                    'label': ['lang1', 'lang2']
                 },
            ],
            'translated': ['label'],
            'translations': ['lang1', 'lang2', 'lang3'],
        })
    assert 'Incorrect translation count: "label"' in str(err.value)

def test_flatten_fails_with_not_enough_translations_listed():
    with pytest.raises(ValueError) as err:
        flatten_content({'survey': [
                {'type': 'text', 'name': 'q1',
                    'label': ['lang1', 'lang2', 'lang3'],
                 },
            ],
            'translated': ['label'],
            'translations': ['lang1', 'lang2'],
        })
    assert 'Incorrect translation count: "label"' in str(err.value)


def test_order_sheet_names():
    assert _order_sheet_names([]) == []
    assert _order_sheet_names(['a', 'survey', 'z']) == ['survey', 'a', 'z']
    assert _order_sheet_names(['settings', 'choices', 'survey']) == ['survey', 'choices', 'settings']


def test_flatten_select_types():
    def _flatten_type(_r):
        return flatten_content({'survey': [_r]})['survey'][0]['type']
    assert _flatten_type({'type': 'select_one',
                          'select_from_list_name': 'xyz'}
                         ) == 'select_one xyz'
    assert _flatten_type({'type': 'select_multiple',
                          'select_from_list_name': 'xyz'}
                         ) == 'select_multiple xyz'
    assert _flatten_type({'type': 'select_one',
                          OR_OTHER_COLUMN: False,
                          'select_from_list_name': 'xyz'}
                         ) == 'select_one xyz'
    assert _flatten_type({'type': 'select_multiple',
                          OR_OTHER_COLUMN: False,
                          'select_from_list_name': 'xyz'}
                         ) == 'select_multiple xyz'
    assert _flatten_type({'type': 'select_one',
                          OR_OTHER_COLUMN: True,
                          'select_from_list_name': 'xyz'}
                         ) == 'select_one xyz or_other'
    assert _flatten_type({'type': 'select_multiple',
                          OR_OTHER_COLUMN: True,
                          'select_from_list_name': 'xyz'}
                         ) == 'select_multiple xyz or_other'


def test_flatten_label_with_xpath():
    _c = flatten_content({'survey': [
                {'type': 'acknowledge', 'name': 'verifnote',
                    'label': [
                        'You answered ',
                        {'@lookup': 'foo'},
                        ' to the foo question'
                    ]}
            ]})
    assert _c['survey'][0]['label'] == 'You answered ${foo} to the foo question'


def test_flatten_to_spreadsheet_content():
    _e = {
        'survey': [
            {'type': 'text', 'name': 'q1',
                'label': ['lang1'],
             },
        ],
        'choices': [
            {'list_name': 'xyz',
                'name': 'x',
                'label': ['X']},
            {'list_name': 'xyz',
                'name': 'y',
                'label': ['Y']},
            {'list_name': 'xyz',
                'name': 'z',
                'label': ['Z']},
        ],
        'settings': {
            'xyz': 'abc',
        },
        'translated': ['label'],
        'translations': ['lang1'],
    }
    _c = flatten_to_spreadsheet_content(_e)
    assert isinstance(_c, OrderedDict)
    assert _c.keys() == ['survey', 'choices', 'settings']


def test_col_order():
    assert _order_cols([
            'label',
            'type',
            'name',
        ]) == ['type', 'name', 'label']


def test_flatten_translated_label_with_xpath():
    _c = flatten_content({'survey': [
                {'type': 'acknowledge', 'name': 'verifnote',
                    'label': [
                        [
                            'You answered ',
                            {'@lookup': 'foo'},
                            ' to the foo question'
                        ],
                        [
                            'U ansrd ',
                            {'@lookup': 'foo'},
                            ' 2da foo q'
                        ],
                    ]},
            ],
            'translated': ['label'],
            'translations': ['en', 'txtspk'],
            })
    row = _c['survey'][0]
    assert 'label' not in row
    assert row['label::en'] == 'You answered ${foo} to the foo question'
    assert row['label::txtspk'] == 'U ansrd ${foo} 2da foo q'
