# -*- coding: utf-8 -*-
from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

from formpack.utils.array_to_xpath import array_to_xpath, DEFAULT_FNS

_fns = {}


def test_custom_directive():
    assert u'dlrow olleh' == array_to_xpath({
        u'@string_reverse': u'hello world'
    }, {
        u'@string_reverse': lambda args: [args[::-1]]
    })


def test_equiv_1():
    inp = []
    expected = ""
    assert expected == array_to_xpath(inp, _fns)


def test_equiv_2():
    inp = [u'a', u'b']
    expected = "ab"
    assert expected == array_to_xpath(inp, _fns)


def test_equiv_3():
    inp = [u'a', {u'something': u'b'}, u'c']
    expected = "abc"
    assert expected == array_to_xpath(inp, _fns)


def test_equiv_4():
    inp = [u'a', {u'something_b': u'b', u'something_c': u'c'}, u'd', [[u'e', u'f', {u'x': u'g'}]]]
    expected = "abcdefg"
    assert expected == array_to_xpath(inp, _fns)


def test_equiv_5():
    inp = [u'a', {u'# pound sign starts a comment': u'never added'}, u'b']
    expected = "ab"
    assert expected == array_to_xpath(inp, _fns)


def test_equiv_6():
    inp = [u'a', [u'(', u')']]
    expected = "a()"
    assert expected == array_to_xpath(inp, _fns)


def test_equiv_7():
    inp = [u'a', [u'(', [u'1', u'2', u'3'], u')']]
    expected = "a(123)"
    assert expected == array_to_xpath(inp, _fns)


def test_equiv_8():
    inp = [u'a', [u'(', [u'x', u'+', u'y', u',', u'z'], u')'], u'b']
    expected = "a(x + y, z)b"
    assert expected == array_to_xpath(inp, _fns)


def test_equiv_9():
    inp = [u'a', [u'(', [u'x', u'+', u'y', u',', u'z'], u')']]
    expected = "a(x + y, z)"
    assert expected == array_to_xpath(inp, _fns)


def test_equiv_10():
    inp = [{u'@lookup': u'abc'}]
    expected = "${abc}"
    assert expected == array_to_xpath(inp, _fns)


def test_equiv_11():
    inp = [{u'@lookup': u'abc'}]
    expected = "${abc}"
    assert expected == array_to_xpath(inp, _fns)


def test_equiv_12():
    inp = [{u'@response_not_equal': [u'question_a', u"'a'"]}]
    expected = "${question_a} != 'a'"
    assert expected == array_to_xpath(inp, _fns)


def test_equiv_13():
    inp = [{u'@and': [[{u'@lookup': u'a'}, u'=', u"'a'"], [{u'@lookup': u'b'}, u'=', u"'b'"], [{u'@lookup': u'c'}, u'=', u"'c'"]]}, u'and', {u'@or': [[{u'@lookup': u'x'}, u'=', u"'x'"], [{u'@lookup': u'y'}, u'=', u"'y'"]]}]
    expected = "${a} = 'a' and ${b} = 'b' and ${c} = 'c' and ${x} = 'x' or ${y} = 'y'"
    assert expected == array_to_xpath(inp, _fns)


def test_equiv_14():
    inp = [{u'aa__q1': [{u'@lookup': u'question_a'}, u'!=', u"'a'"]}, u'and', [u'${question_b}', u'<=', 123], u'and', [{u'@not_multiselected': [u'question_c', u"'option_2'"]}], u'and', [{u'@lookup': u'question_d'}, u'=', u"'option_2'"]]
    expected = "${question_a} != 'a' and ${question_b} <= 123 and not(selected(${question_c}, 'option_2')) and ${question_d} = 'option_2'"
    assert expected == array_to_xpath(inp, _fns)


def test_lookup():
    assert array_to_xpath([{'@lookup': 'someval'}]) == '${someval}'


def test_response_not_equal():
    assert array_to_xpath([{'@response_not_equal': ['abc', '123']}]
                          ) == '${abc} != 123'


def test_join():
    assert array_to_xpath([{'@join': ['and', ['a', 'b']]}]) == 'a and b'


def test_and():
    assert array_to_xpath([{'@and': ['abc', 'def']}]) == 'abc and def'


def test_or():
    assert array_to_xpath([{'@or': ['a', 'b']}]) == 'a or b'


def test_not():
    assert array_to_xpath([{'@not': ['x']}]) == 'not(x)'


def test_predicate():
    assert array_to_xpath([{'@predicate': ['abc']}]) == '[abc]'


def test_parens():
    assert array_to_xpath([{'@parens': ['123', '+', '456']}]) == '(123 + 456)'


def test_axis():
    assert array_to_xpath([{'@axis': ['aa', 'bb']}]) == 'aa::bb'


def test_position():
    assert array_to_xpath([{'@position': ['abc']}]) == 'position(abc)'


def test_selected_at():
    assert array_to_xpath([{'@selected_at': ['x', 'y']}]) == 'selected-at(x, y)'


def test_count_selected():
    assert array_to_xpath([{'@count_selected': ['.']}]) == 'count-selected(.)'


def test_multiselected():
    assert array_to_xpath([{'@multiselected': ['abc', 'xyz']}]) == 'selected(${abc}, xyz)'


def test_not_multiselected():
    assert array_to_xpath([{'@not_multiselected': ['abc', 'xyz']}]) == 'not(selected(${abc}, xyz))'


default_fn_tests = {
    u'@lookup': test_lookup,
    u'@response_not_equal': test_response_not_equal,
    u'@join': test_join,
    u'@and': test_and,
    u'@or': test_or,
    u'@not': test_not,
    u'@predicate': test_predicate,
    u'@parens': test_parens,
    u'@axis': test_axis,
    u'@position': test_position,
    u'@selected_at': test_selected_at,
    u'@count_selected': test_count_selected,
    u'@multiselected': test_multiselected,
    u'@not_multiselected': test_not_multiselected,
}


def test_all_transformation_fns_covered():
    '''
    this ensures that all of the default transformation functions have an
    associated test defined.
    '''
    assert set(default_fn_tests.keys()) == set(DEFAULT_FNS.keys())
