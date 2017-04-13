# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

import unittest
from formpack import FormPack
from .fixtures import build_fixture, build_pack


def test_submission_counts_match():
    fp = build_pack('restaurant_profile')

    report = fp.autoreport(versions=fp.versions.keys())
    stats = report.get_stats(fp.submissions)
    assert stats.submissions_count == len(fp.submissions)
    assert stats.submission_counts_by_version == {
        u'rpv1': 1,
        u'rpV2': 1,
        u'rpV3': 2,
        u'rpV4': 4,
    }
