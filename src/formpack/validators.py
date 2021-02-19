# coding: utf-8
from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

from jsonschema import validate

from .utils.replace_aliases import (
    LABEL_OPTIONAL_TYPES,
    MAIN_TYPES,
    SELECT_TYPES,
)

MAIN_SCHEMA = {
    'properties': {
        'type': {
            'type': 'string',
            'enum': MAIN_TYPES,
        },
        'name': {
            'type': 'string',
        },
        'label': {
            'type': ['array', 'string']
        },
    },
    'required': ['type', 'name'],
}

SELECT_SCHEMA = {
    'properties': {
        'type': {
            'type': 'string',
            'enum': SELECT_TYPES,
        },
        'name': {
            'type': 'string',
        },
        'label': {
            'type': ['array', 'string'],
        },
        'select_from_list_name': {
            'type': 'string',
        },
    },
    'required': ['type', 'name', 'select_from_list_name'],
}

LABEL_OPTIONAL_SCHEMA = {
    'properties': {
        'type': {
            'type': 'string',
            'enum': LABEL_OPTIONAL_TYPES,
        },
        'name': {
            'type': 'string',
        },
    },
    'required': ['type', 'name'],
}


_ROW_SCHEMA = {
        'type': 'object',
        'oneOf': [
            SELECT_SCHEMA,
            MAIN_SCHEMA,
            LABEL_OPTIONAL_SCHEMA,
            {
                'properties': {
                    'type': {
                        'type': 'string',
                        'enum': [
                            'end_group',
                            'end_repeat',
                        ]
                    }
                }
            }
        ]
    }

_ALL_ROW_COLUMNS = [
    'name',
    'type',
    'default',
    'required',
    'label',
    'kuid',
    'appearance',
]

_ALL_PROPS = {
    'type': 'object',
    'properties': dict([
        (col, {'type': [
            'string',
            'boolean',
            'array',
            'object',
            # null values probably should be filtered out?
            # 'null'
        ]})
        for col in _ALL_ROW_COLUMNS
    ])
}

ROW_SCHEMA = {
    'type': 'object',
    'allOf': [
        _ALL_PROPS,
        _ROW_SCHEMA,
    ]
}


def validate_row(row, row_number):
    validate(row, ROW_SCHEMA)


def validate_content(content):
    for i, row in enumerate(content['survey']):
        validate_row(row, row_number=i)
