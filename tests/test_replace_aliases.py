# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)
import json
import pytest

from formpack.utils.replace_aliases import (replace_aliases, dealias_type,
                                            settings_header_columns,
                                            survey_header_columns,
                                            )


def test_replace_select_one():
    s1 = {'survey': [{'type': 'select1 dogs'}]}
    replace_aliases(s1, in_place=True)
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
    replace_aliases(s1, in_place=True)
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
    assert dealias_type('begin group') == 'begin_group'
    assert dealias_type('end group') == 'end_group'
    assert dealias_type('begin repeat') == 'begin_repeat'
    assert dealias_type('end repeat') == 'end_repeat'
    assert dealias_type('begin_group') == 'begin_group'
    assert dealias_type('end_group') == 'end_group'
    assert dealias_type('begin_repeat') == 'begin_repeat'
    assert dealias_type('end_repeat') == 'end_repeat'
    assert dealias_type('imei') == 'deviceid'
    assert dealias_type('gps') == 'geopoint'


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
    _o = {'survey': [], 'settings': _s}
    replace_aliases(_o, in_place=True)
    assert len(_o['settings'].keys()) == 1
    assert _o['settings'].keys()[0] == expected


def test_settings_get_replaced():
    _setting('title', 'form_title')
    _setting('set form title', 'form_title')
    _setting('set form id', 'id_string')
    _setting('form_id', 'id_string')
    _setting('id_string', 'id_string')
    # no change
    _setting('form_title', 'form_title')
    _setting('sms_keyword', 'sms_keyword')


def test_custom_allowed_types():
    ex1 = replace_aliases({'survey': [{'type': 'x_y_z_a_b_c'}]}, allowed_types={
            'xyzabc': 'x_y_z_a_b_c'
        })
    assert ex1['survey'][0]['type'] == 'xyzabc'

    ex2 = replace_aliases({'survey': [{'type': 'xyzabc'}]}, allowed_types={
            'xyzabc': ['x_y_z_a_b_c'],
        })
    assert ex2['survey'][0]['type'] == 'xyzabc'

    ex3 = replace_aliases({'survey': [{'type': 'xyzabc'}]}, allowed_types={
            'xyzabc': True,
        })
    assert ex3['survey'][0]['type'] == 'xyzabc'


def test_list_name_renamed():
    ex1 = replace_aliases({'choices': [{'list name': 'mylist'}]})
    assert ex1['choices'][0].keys() == ['list_name']

# when formpack exports support choice['value'] as the identifier for the choice, then we
# will use choice['value']; until then, we will do the opposite; since both are accepted
# aliases in pyxform
# def test_choice_name_becomes_value():
#     ex1 = replace_aliases({'choices': [{'list_name': 'mylist', 'name': 'myvalue'}]})
#     c1 = ex1['choices'][0]
#     assert 'value' in c1
#     assert c1['value'] == 'myvalue'


def test_choice_value_becomes_name__temp():
    'in the meantime, we ensure that "value" alias is changed to "name"'
    ex1 = replace_aliases({'choices': [{'list_name': 'mylist', 'value': 'myvalue'}]})
    c1 = ex1['choices'][0]
    assert 'name' in c1
    assert c1['name'] == 'myvalue'


def _assert_column_converted_to(original, desired):
    row = {}
    row[original] = 'ABC'
    surv = {'survey': [row]}
    replace_aliases(surv, in_place=True)
    assert len(surv['survey'][0].keys()) == 1
    assert surv['survey'][0].keys()[0] == desired


def test_survey_header_replaced():
    _assert_column_converted_to('required', 'required')
    _assert_column_converted_to('bind::required', 'required')
    _assert_column_converted_to('bind::relevant', 'relevant')
