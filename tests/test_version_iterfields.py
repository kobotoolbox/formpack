# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)
from tabulate import tabulate
from collections import defaultdict

from formpack import FormPack
from .fixtures import build_fixture


def _build_pack(key):
    title, schemas, submissions = build_fixture(key)
    return FormPack(schemas, title, submissions=submissions)


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
def print_fixture_table(fixture_name, path=False, _type=False,
                        kuid=False,
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
        if kuid:
            _kuid = labeled.src.get('$kuid', None)
            arr.append(_kuid)
        trows.append(arr)

    cols = ['item']
    if _type:
        cols.append('type')
    if path:
        cols.append('path')
    if kuid:
        cols.append('kuid')
    print('\n' + tabulate(trows, cols))

import yaml
from copy import deepcopy
from pprint import pprint
import json

import copy


class Handler:
    def __init__(self, *args, **kwargs):
        self._kwargs = kwargs
        _cur = kwargs.pop('_cur', None)
        if _cur:
            raise Exception('cur is not none')

    def __repr__(self):
        kw = copy.deepcopy(self._kwargs)
        category = kw.pop('category')
        return '<Handler "{}" {}>'.format(category, repr(kw))


class FieldMapping:
    def input_key(self):
        return self.INPUT_KEY

    def output_key(self):
        return self.OUTPUT_KEY

    def transformation(self, value):
        return value


class FormhubUUID(FieldMapping):
    INPUT_KEY = '_uuid'
    OUTPUT_KEY = 'UUID'


class SubmissionTime(Handler):
    pass

def test_iterate_through_simple_survey():
    fp = _build_pack('four_simp_questions')
    v1 = fp.versions.values()[0]
    opts = {
        'ignore': [
            '_notes',
            '_bamboo_dataset_id',
            '_tags',
            '_attachments',
            '_submitted_by',
            '_geolocation',
            '_id',
            '__version__',
            '_uuid',
            '_xform_id_string',
        ],
        'field_mapped': {
            'meta/instanceID': Handler,
            'formhub/uuid': Handler,
            '_status': Handler,
            '_submission_time': SubmissionTime,
        },
    }
    for submission in [fp.submissions[0]]:
        for field_submission in v1.format_submission_iterator(submission, **opts):
            print(field_submission)


def test_iterate_through_nested_repeat_submission():
    print_fixture_table('repeat_repeat', path=True, kuid=True)
    fp = _build_pack('repeat_repeat')
    v1 = fp.versions.values()[0]
    outt = []
    subs = []

    expected = [[u'e6b3a76c', [0], u'xx'],
                [u'53c4140e', [0, 0], u'aa'],
                [u'116d1cd6', [0, 0], u'bb'],
                [u'53c4140e', [0, 1], u'cc'],
                [u'116d1cd6', [0, 1], u'dd'],
                [u'53c4140e', [0, 2], u'ee'],
                [u'116d1cd6', [0, 2], u'ff'],
                [u'e6b3a76c', [1], u'gg'],
                [u'53c4140e', [1, 0], u'hh'],
                [u'116d1cd6', [1, 0], u'ii'],
                [u'53c4140e', [1, 1], u'jj'],
                [u'116d1cd6', [1, 1], u'kk'],
                [u'53c4140e', [1, 2], u'll'],
                [u'116d1cd6', [1, 2], u'mm'],
                [u'53c4140e', [1, 3], u'nn'],
                [u'116d1cd6', [1, 3], u'oo'],
                [u'e6b3a76c', [2], u'pp'],
                [u'53c4140e', [2, 0], u'qq'],
                [u'116d1cd6', [2, 0], u'rr'],
                [u'53c4140e', [2, 1], u'ss'],
                [u'116d1cd6', [2, 1], u'tt'],
                [u'42a69d1b', [], u'pickles tomatoes'],
                [u'77a73545', [], u'other'],
                [u'db77bd6f', [], u'2017-03-29T18:14:08.000-05:00'],
                [u'729cd22d', [], u'aa'],
                [u'd48216e8', [], u'2017-03-29T18:13:02.000-05:00']]

    expected = [[u'e6b3a76c',
                [0],
                u'xx',
                u'household_visit/houshold_member_name[]/household_member_name'],
                [u'53c4140e',
                [0, 0],
                u'aa',
                u'household_visit/houshold_member_name[]/group_fv0pt65[]/what_is_an_example_of_a_nice_word'],
                [u'116d1cd6',
                [0, 0],
                u'bb',
                u'household_visit/houshold_member_name[]/group_fv0pt65[]/why_is_this_word_nice'],
                [u'53c4140e',
                [0, 1],
                u'cc',
                u'household_visit/houshold_member_name[]/group_fv0pt65[]/what_is_an_example_of_a_nice_word'],
                [u'116d1cd6',
                [0, 1],
                u'dd',
                u'household_visit/houshold_member_name[]/group_fv0pt65[]/why_is_this_word_nice'],
                [u'53c4140e',
                [0, 2],
                u'ee',
                u'household_visit/houshold_member_name[]/group_fv0pt65[]/what_is_an_example_of_a_nice_word'],
                [u'116d1cd6',
                [0, 2],
                u'ff',
                u'household_visit/houshold_member_name[]/group_fv0pt65[]/why_is_this_word_nice'],
                [u'e6b3a76c',
                [1],
                u'gg',
                u'household_visit/houshold_member_name[]/household_member_name'],
                [u'53c4140e',
                [1, 0],
                u'hh',
                u'household_visit/houshold_member_name[]/group_fv0pt65[]/what_is_an_example_of_a_nice_word'],
                [u'116d1cd6',
                [1, 0],
                u'ii',
                u'household_visit/houshold_member_name[]/group_fv0pt65[]/why_is_this_word_nice'],
                [u'53c4140e',
                [1, 1],
                u'jj',
                u'household_visit/houshold_member_name[]/group_fv0pt65[]/what_is_an_example_of_a_nice_word'],
                [u'116d1cd6',
                [1, 1],
                u'kk',
                u'household_visit/houshold_member_name[]/group_fv0pt65[]/why_is_this_word_nice'],
                [u'53c4140e',
                [1, 2],
                u'll',
                u'household_visit/houshold_member_name[]/group_fv0pt65[]/what_is_an_example_of_a_nice_word'],
                [u'116d1cd6',
                [1, 2],
                u'mm',
                u'household_visit/houshold_member_name[]/group_fv0pt65[]/why_is_this_word_nice'],
                [u'53c4140e',
                [1, 3],
                u'nn',
                u'household_visit/houshold_member_name[]/group_fv0pt65[]/what_is_an_example_of_a_nice_word'],
                [u'116d1cd6',
                [1, 3],
                u'oo',
                u'household_visit/houshold_member_name[]/group_fv0pt65[]/why_is_this_word_nice'],
                [u'e6b3a76c',
                [2],
                u'pp',
                u'household_visit/houshold_member_name[]/household_member_name'],
                [u'53c4140e',
                [2, 0],
                u'qq',
                u'household_visit/houshold_member_name[]/group_fv0pt65[]/what_is_an_example_of_a_nice_word'],
                [u'116d1cd6',
                [2, 0],
                u'rr',
                u'household_visit/houshold_member_name[]/group_fv0pt65[]/why_is_this_word_nice'],
                [u'53c4140e',
                [2, 1],
                u'ss',
                u'household_visit/houshold_member_name[]/group_fv0pt65[]/what_is_an_example_of_a_nice_word'],
                [u'116d1cd6',
                [2, 1],
                u'tt',
                u'household_visit/houshold_member_name[]/group_fv0pt65[]/why_is_this_word_nice'],
                [u'42a69d1b', [], u'pickles tomatoes', u'select_mult'],
                [u'77a73545', [], u'other', u'did_it_go_well'],
                [u'db77bd6f', [], u'2017-03-29T18:14:08.000-05:00', u'end'],
                [u'729cd22d', [], u'aa', u'household_visit/household_address'],
                [u'd48216e8', [], u'2017-03-29T18:13:02.000-05:00', u'start']]

    for (n, submission) in enumerate(fp.submissions):
        subs.append(deepcopy(submission))
        xxxyz = v1.format_submission(submission)
        if n == 0:
            outt.append(xxxyz)
    pprint(outt[0])
    assert outt[0] == expected

    # for (n, _outtie) in enumerate(outt[0]):
    #     # pprint(_outtie)
    #     try:
    #         assert expected[0][n] == _outtie
    #     except IndexError:
    #         print(json.dumps(subs[n], indent=2))
    #         raise Exception('fail')

    # assert outt[0] == 
    # print(json.dumps(fp.submissions, indent=2))
