# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)
from formpack import FormPack
from .fixtures import build_fixture

from formpack.utils.submission_utils import (
    flatten_kobocat_submission_dict,
    renest,
    _insert_at_indeces,
    _pluck_indeces,
)


def _build_pack(key):
    title, schemas, submissions = build_fixture(key)
    return FormPack(schemas, title, submissions=submissions)


def test_field_paths():
    fp = _build_pack('grouped_questions')
    v1 = fp.versions.values()[0]
    s1 = v1.sections.values()[0]
    fields = s1.fields
    assert fields.keys() == [u'q1', u'g1q1', u'g1sg1q1', u'g1q2', u'g2q1', u'qz']

    paths = [ff.path for ff in fields.values()]
    # these are the paths that exports are expecting
    assert paths == [
        u'q1', u'g1/g1q1', u'g1/sg1/g1sg1q1', u'g1/g1q2', u'g2/g2q1', u'qz'
    ]
    g1sg1q1 = fields['g1sg1q1']
    assert g1sg1q1._parent is not None
    assert g1sg1q1._parent.name == 'sg1'

    sg1 = g1sg1q1._parent
    assert sg1._parent is not None
    assert sg1._parent.name == 'g1'

    g1 = sg1._parent
    assert g1._parent.name == 'Grouped questions'
