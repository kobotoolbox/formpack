# coding: utf-8
from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

import json

from formpack.validators import validate_row


def test_row_validator():

    rows = [
        {'type': 'text', 'name': 'x', 'label': 'z'},
        {'type': 'select_one', 'name': 'x', 'select_from_list_name': 'y', 'label': 'z'},
        {'type': 'select_multiple', 'name': 'x', 'select_from_list_name': 'y', 'label': 'z'},
        {'type': 'select_one_external', 'name': 'x', 'select_from_list_name': 'y', 'label': 'z'},
        {'appearance': 'label', 'type': 'select_one', 'name': 'ER_int_group2', 'select_from_list_name': 'emotion'},
        {'type': 'note', 'name': 'x', 'media::image': 'y'},
        # no names needed
        {'type': 'end_group'},
        {'type': 'end_repeat'},
        {'type': 'begin_group', 'name': 'x', 'appearance': 'field-list'},
    ]
    for i, row in enumerate(rows):
        validate_row(row, i)


def test_row_validator_fails():
    rows = [
        # no list_name
        {'type': 'select_one', 'name': 'x', 'label': 'z'},

        # no name
        {'type': 'text', 'label': 'x'},

        # no label; no longer enforced because label can be either 'media::image', 'appearance', or 'label'
        # {'type': 'text', 'name': 'x'},
    ]
    for i, row in enumerate(rows):
        failed = False
        try:
            validate_row(row, i)
        except Exception as e:
            failed = True
        if not failed:
            raise AssertionError('row passed validator: {}'.format(json.dumps(row)))
