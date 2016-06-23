# -*- coding: utf-8 -*-
from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

SPACE_PADDING = {
    u'+': u' + ',
    u'-': u' - ',
    u',': u', ',
    u'=': u' = ',
    u'>': u' > ',
    u'<': u' < ',
    u'<=': u' <= ',
    u'>=': u' >= ',
    u'!=': u' != ',
    u'and': u' and ',
    u'or': u' or ',
}

DEFAULT_FNS = {
    u'$lookup': lambda x: "${%s}" % x,
    u'$fn': lambda *args: args,
}


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
        elif isinstance(arr, basestring) or isinstance(arr, int) or \
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
                # handle keys that begin with '$' as transformable
                elif key.startswith('$'):
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
