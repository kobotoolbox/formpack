# -*- coding: utf-8 -*-
from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

from functools import reduce

from .string import unicode, str_types


SPACE_PADDING = {
    '+': ' + ',
    '-': ' - ',
    ',': ', ',
    '=': ' = ',
    '>': ' > ',
    '<': ' < ',
    '<=': ' <= ',
    '>=': ' >= ',
    '!=': ' != ',
    'and': ' and ',
    'or': ' or ',
}


def _case_fn(args):
    if len(args) < 1:
        raise ValueError('empty @case expression')

    def _pop_arg():
        return False if len(args) == 0 else args.pop()

    # last item in args specifies the default value
    expr = _pop_arg()

    arg = _pop_arg()
    while arg:
        if len(arg) != 2:
            raise ValueError(
                'Each item in a @case expression (except the default)'
                ' must be an array with a lenth of 2.'
            )
        expr = {
            '@if': arg + [expr]
        }
        arg = _pop_arg()
    return [expr]


DEFAULT_FNS = {
    '@lookup': lambda x: "${%s}" % x,
    '@response_not_equal': lambda args: [{'@lookup': args[0]}, '!=', args[1]],
    '@join': lambda p: reduce(lambda x, v: x + [v, p[0]], p[1], [])[:-1],
    '@and': lambda args: {'@join': ['and', args]},
    '@or': lambda args: {'@join': ['or', args]},
    '@not': lambda args: ['not', {'@parens': args}],
    '@if': lambda args: ['if', {'@comma_parens': [args]}],
    '@predicate': lambda args: ['[', args, ']'],
    '@parens': lambda args: ['('] + args + [')'],
    '@comma_parens': lambda args: {
        '@parens': reduce(
                lambda arr, itm: arr + [itm, ','], args[0], []
            )[:-1]
    },
    '@axis': lambda args: [args[0], '::', args[1]],
    '@position': lambda args: ['position', {'@parens': [args]}],
    '@selected_at': lambda args: ['selected-at', {'@comma_parens': [args]}],
    '@count_selected': lambda args: ['count-selected', {'@parens': args}],
    '@multiselected': lambda args: [['selected', {'@parens': [
                                     {'@lookup': args[0]}, ',', args[1]]}]],
    '@not_multiselected': lambda p: {'@not': [{'@multiselected': p}]},
    '@case': _case_fn,
}

# this will be phased out shortly, since most fields are expandable in some way
EXPANDABLE_FIELD_TYPES = ['relevant', 'constraint', 'calculation', 'repeat_count']


def array_to_xpath(outer_arr, fns={}):
    flattened = array_to_xpath.array_to_flattened_array(outer_arr, fns)
    return array_to_xpath.flattened_array_to_padded_string(flattened)


def array_to_flattened_array(outer_arr, _fns):
    fns = DEFAULT_FNS.copy()
    fns.update(_fns)

    def arr2x(arr):
        if isinstance(arr, list):
            # recurse
            for item in arr:
                arr2x(item)
        elif isinstance(arr, str_types) or isinstance(arr, int) or \
                isinstance(arr, float):
            # parameter is string or number and can be added directly
            out.append(arr)
        elif isinstance(arr, dict):
            keys = sorted(arr.keys())
            if len(keys) > 0:
                # parameter is object and should be expanded
                _needs_parse = True
            for key in keys:
                # skip keys that begin with '#' as comments
                if key.startswith('#'):
                    continue
                # handle keys that begin with '@' as transformable
                elif key.startswith('@'):
                    if key not in fns:
                        raise ValueError('Transform function not found: %s'
                                         % key)
                    arr2x(fns[key](arr[key]))
                else:
                    arr2x(arr[key])
    # a boolean to break out of the while loop
    _needs_parse = True
    while _needs_parse:
        out = []
        _needs_parse = False
        arr2x(outer_arr)
        # _needs_parse will be true iff an object was present and
        # needed to be expanded
        outer_arr = out
    return outer_arr


def flattened_array_to_padded_string(flattened):
    out_string = ""
    for n in range(0, len(flattened)):
        p = flattened[n]
        if p in SPACE_PADDING:
            out_string += SPACE_PADDING[p]
        else:
            out_string += unicode(p)
    return out_string


array_to_xpath.array_to_flattened_array = array_to_flattened_array
array_to_xpath.flattened_array_to_padded_string = \
    flattened_array_to_padded_string
