# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

from formpack import FormPack
from .fixtures import build_fixture

title, schemas, submissions = build_fixture('unknown_columns')


def test_export_with_unknown_columns():
    fp = FormPack(schemas, title)

    export_options = {
        'versions': 'unk1',
        'retain_unmatched_values': True,
    }

    export = fp.export(**export_options).to_dict(submissions)
    assert export.values()[0]['fields'] == [u'question1']
    first_submission = [u'S1 R1', 'S1 R2 ?']
    assert export.values()[0]['data'][0] == first_submission
    second_submission = [u'S2 R1', 'S2 R2 ?', 'S2 R3 ?']
    assert export.values()[0]['data'][1] == second_submission
