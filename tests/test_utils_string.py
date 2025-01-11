# coding: utf-8
from formpack.utils.string import orderable_with_none, unique_name_for_xls


def test_sort_list_with_none():
    list_to_sort = ['foo', 'bar', None]
    sorted_list = sorted(list_to_sort, key=orderable_with_none)
    expected_list = [None, 'bar', 'foo']

    assert orderable_with_none(None).__class__.__name__ == '__OrderableNone'
    assert isinstance(orderable_with_none('foo'), str)
    assert sorted_list == expected_list

def test_excel_compatible_worksheet_names():

    # Truncate (with '...' by default)
    length_limit = [ # to <= 31 characters
        '123456789_123456789_123456789_12',
        '123456789_123456789_12345678...',
    ]
    assert unique_name_for_xls(length_limit[0], []) == length_limit[1]

    # Replace disallowed characters ([]:*?/\) with '_'
    char_safety = [
        '[hi]: *nice*? ok "/_o,o_\\"',
        '_hi__ _nice__ ok "__o,o__"',
    ]
    assert unique_name_for_xls(char_safety[0], []) == char_safety[1]

    # Replace leading or trailing apostrophes with '_'
    leading_trailing_apostrophes = [
        [ "'both'", '_both_' ],
        [ "'leading", '_leading'],
        [ "trailing'", 'trailing_'],
        [
            "'_'mixed'''",
            "__'mixed''_",
        ]
    ]
    for test in leading_trailing_apostrophes:
        assert unique_name_for_xls(test[0], []) == test[1]

