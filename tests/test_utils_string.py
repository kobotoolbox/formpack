# coding: utf-8
from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

from formpack.utils.string import orderable_with_none


def test_sort_list_with_none():
    list_to_sort = ['foo', 'bar', None]
    sorted_list = sorted(list_to_sort, key=orderable_with_none)
    expected_list = [None, 'bar', 'foo']

    assert orderable_with_none(None).__class__.__name__ == '__OrderableNone'
    assert isinstance(orderable_with_none('foo'), str)
    assert sorted_list == expected_list
