# coding: utf-8
from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

from formpack import FormPack
from .fixtures import build_fixture


def test_submission_counts_match():
    title, schemas, submissions = build_fixture('restaurant_profile')
    fp = FormPack(schemas, title)

    report = fp.autoreport(versions=fp.versions.keys())
    stats = report.get_stats(submissions)
    assert stats.submissions_count == len(submissions)
    assert stats.submission_counts_by_version == {
        'rpv1': 1,
        'rpV2': 1,
        'rpV3': 2,
        'rpV4': 4,
    }
