# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)
from tabulate import tabulate
from collections import defaultdict

from formpack import FormPack
from .fixtures import build_fixture


def _build_pack(key):
    title, schemas, submissions = build_fixture(key)
    return FormPack(schemas, title)


def _fixture_iterator(fix_name):
    fp = _build_pack(fix_name)
    v1 = fp.versions.values()[0]

    def _iteropts(**opts):
        return list(v1.columns(**opts))
    return _iteropts


def _version_to_names(v, **opts):
    return [_field_to_hierarchies(field) for field in v.columns(**opts)]


def _field_to_hierarchies(field):
    return [s.name for s in field.ancestors]


def _field_to_labels(field):
    return [
        ss.labels[0]
        for ss in filter(lambda x: x is not None and not x.is_root,
                         field.ancestors)
    ]


def _version_to_labels(v, **opts):
    return [_field_to_labels(field) for field in v.columns(**opts)]


def test_four_simp_keys_grouped():
    fp = _build_pack('four_simple_questions_grouped')
    v1 = fp.versions.values()[0]

    fields = []
    for field in v1.columns():
        fields.append(field)

    assert len(list(v1.columns(include_groups=False))) == 5

    assert _version_to_names(v1) == [
        [u'simplest_group', u'ack'],
        [u'simplest_group', u'group_eh5jq27', u'val1'],
        [u'simplest_group', u'group_eh5jq27', u'num1'],
        [u'simplest_group', u'group_qu2xm07', u's1'],
        [u'simplest_group', u'group_qu2xm07', u's_many'],
    ]

    assert _version_to_labels(v1, )[1] == [
         [u'ack'],
         [u'values', u'val1'],
         [u'values', u'num1'],
         [u'selects', u's1'],
         [u'selects', u's_many'],
    ][1]


def test_orother_version_keys():
    fp = _build_pack('or_other')
    version = fp.versions.values()[0]
    assert [s.name for s in version.columns()] == [
        's1',
    ]

    _with_other_fields = [
        s.name
        for s in version.columns(expand_custom_other_fields=True)
    ]

    assert _with_other_fields == [
        's1',
        's1_other',
    ]


def test_col_filtering_by_start_name():
    g_iterfields = _fixture_iterator('grouped_repeatable')
    assert len(g_iterfields(
                include_groups=True,
                start='household_location',
                count=2,
                )) == 2


def test_col_filtering_by_start_int():
    g_iterfields = _fixture_iterator('grouped_repeatable')
    assert len(g_iterfields(
                include_groups=True,
                start=0,
                count=2,
                )) == 2

    # reached end of survey
    assert len(g_iterfields(
                include_groups=True,
                start=2,
                count=5,
                )) == 4


def test_grouped_repeatable():
    fp = _build_pack('grouped_repeatable')
    v1 = fp.versions.values()[0]

    def _iteropts(**opts):
        return list(v1.columns(**opts))

    assert [
        qq.type
        for qq in _iteropts(include_groups=False, include_group_ends=False)
        ] == [
            'start',
            'end',
            'text',
            'text',
        ]

    paths = [
        qq.path
        for qq in _iteropts(include_groups=False, include_group_ends=False)
        ]
    exp_paths = ['start',
                 'end',
                 'household_visit/household_location',
                 #               "houshold" typo
                 'household_visit/houshold_member_repeat/household_member_name']
    assert exp_paths == paths

    paths = [qq.path
        for qq in _iteropts(include_groups=True, include_group_ends=False)
        ]
    exp_paths = ['start',
                 'end',
                 'household_visit',
                 'household_visit/household_location',
                 #               "houshold" typo
                 'household_visit/houshold_member_repeat',
                 'household_visit/houshold_member_repeat/household_member_name']
    assert exp_paths == paths

    def _pth(x):
        if hasattr(qq, 'related_group'):
            return '~{}'.format(qq.related_group.path)
        else:
            return qq.path
    qs = _iteropts(include_groups=True, include_group_ends=True)
    assert qs[-1].related_group is qs[2]

    paths = [
        _pth(qq)
        for qq in _iteropts(include_groups=True, include_group_ends=True)
    ]
    exp_paths = ['start',
                 'end',
                 'household_visit',
                 'household_visit/household_location',
                 'household_visit/houshold_member_repeat',
                 'household_visit/houshold_member_repeat/household_member_name',
                 '~household_visit/houshold_member_repeat',
                 '~household_visit',
                 ]
    assert exp_paths == paths


def test_iterfields_repeat():
    fp = _build_pack('grouped_repeatable')
    v1 = fp.versions.values()[0]

    def _iteropts(**opts):
        return list(v1._tree.iterfields(**opts))
    zz = _iteropts(include_groups=True, include_group_ends=False)


def test_iterfields():
    fp = _build_pack('four_simple_questions_grouped')
    v1 = fp.versions.values()[0]

    def _iteropts(**opts):
        return list(v1._tree.iterfields(**opts))

    _ancestor_lengths = [
        len(item.ancestors)
        for item in _iteropts(include_groups=True)
    ]
    assert _ancestor_lengths == [
        2,
        2,
        3, 3,
        2,
        3, 3,
    ]

    assert len(_iteropts()) == 5
    assert len(_iteropts(include_groups=True)) == 7
    assert len(_iteropts(include_groups=True,
                         include_group_ends=True)) == 9


# This does work, but could be moved somewhere else as a CLI utility
'''
def print_fixture_table(fixture_name, path=False, _type=False,
                        names=None,
                        start=None,
                        count=None):
    title, schemas, submissions = build_fixture(fixture_name)
    fp = FormPack(schemas, title, submissions=submissions)
    vers = fp.latest_version
    trows = []

    for labeled in vers.columns(
                expand_custom_other_fields=True,
                start=start,
                count=count,
                names=names,
                include_groups=True,
                include_group_ends=True,
            ):
        arr = [
            '| {}{}'.format(
                '  '*(len(labeled.ancestors)-1),
                '{}: {}'.format(
                    labeled.type,
                    labeled.name,
                    ) if labeled.name else labeled.type,
            ),
        ]
        if _type:
            arr.append(labeled.type)
        if path:
            arr.append(labeled.path)
        trows.append(arr)

    cols = ['item']
    if _type:
        cols.append('type')
    if path:
        cols.append('path')
    print('\n' + tabulate(trows, cols))
'''