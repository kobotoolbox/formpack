# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)
import json
import pytest

from formpack.utils.replace_aliases import (replace_aliases, dealias_type,
                                            settings_header_columns,
                                            survey_header_columns,
                                            )


def test_expand_select_one():
    s1 = {'survey': [{'type': 'select1 dogs'}]}
    replace_aliases(s1)
    assert s1['survey'][0]['type'] == 'select_one dogs'


def test_select_one_aliases_replaced():
    assert dealias_type('select1 dogs') == 'select_one dogs'
    assert dealias_type('select one dogs') == 'select_one dogs'
    assert dealias_type('select1 dogs') == 'select_one dogs'
    assert dealias_type('select_one dogs') == 'select_one dogs'


def test_true_false_value_replaced():
    # only replaced on columns with TF_COLUMNS
    s1 = {'survey': [
        {'type': 'text', 'required': val} for val in [
            True, 'True', 'yes', 'true()', 'TRUE',
            False, 'NO', 'no', 'false()', 'FALSE'
        ]
    ]}
    replace_aliases(s1)
    tfs = [row['required'] for row in s1['survey']]
    assert tfs == [True] * 5 + [False] * 5


def test_select_multiple_aliases_replaced():
    assert dealias_type('select all that apply from x') == 'select_multiple x'
    assert dealias_type('select all that apply dogs') == 'select_multiple dogs'
    assert dealias_type('select many dogs') == 'select_multiple dogs'
    assert dealias_type('select multiple dogs') == 'select_multiple dogs'
    assert dealias_type('select_many dogs') == 'select_multiple dogs'
    assert dealias_type('select_multiple dogs') == 'select_multiple dogs'


def test_misc_types():
    assert dealias_type('begin group') == 'begin group'
    assert dealias_type('end group') == 'end group'
    assert dealias_type('begin repeat') == 'begin repeat'
    assert dealias_type('end repeat') == 'end repeat'
    assert dealias_type('begin_group') == 'begin group'
    assert dealias_type('end_group') == 'end group'
    assert dealias_type('begin_repeat') == 'begin repeat'
    assert dealias_type('end_repeat') == 'end repeat'


def _fail_type(_type):
    with pytest.raises(ValueError) as e:
        dealias_type(_type, strict=True)


def test_fail_unknown_types():
    _fail_type('idk')


def test_select_one_external_replaced():
    assert dealias_type('select one external x') == 'select_one_external x'


def _setting(settings_key, expected):
    _s = {}
    _s[settings_key] = 'value'
    _o = {'survey': [], 'settings': [_s]}
    replace_aliases(_o)
    assert len(_o['settings'].keys()) == 1
    assert _o['settings'].keys()[0] == expected


def test_settings_get_replaced():
    _setting('title', 'form_title')
    _setting('set form title', 'form_title')
    _setting('set form id', 'id_string')
    _setting('form_id', 'id_string')
    # no change
    _setting('form_title', 'form_title')
    _setting('sms_keyword', 'sms_keyword')


def _assert_column_converted_to(original, desired):
    row = {}
    row[original] = 'ABC'
    surv = {'survey': [row]}
    replace_aliases(surv)
    assert len(surv['survey'][0].keys()) == 1
    assert surv['survey'][0].keys()[0] == desired


def test_survey_header_replaced():
    _assert_column_converted_to('required', 'required')
    _assert_column_converted_to('bind::required', 'required')
    _assert_column_converted_to('bind::relevant', 'relevant')
