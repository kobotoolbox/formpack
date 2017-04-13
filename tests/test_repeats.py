# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)
from formpack import FormPack
from .fixtures import build_pack

from formpack.utils.submission_utils import (
    flatten_kobocat_submission_dict,
    renest,
    _insert_at_indeces,
    _pluck_indeces,
)

import json


def test_simplest_repeat():
    fp = build_pack('simplest_repeat')
    v1 = fp.versions.values()[0]
    submission = fp.submissions[0]
    x1 = flatten_kobocat_submission_dict(submission)
    xr = renest(x1)

    class ExportBunch:
        def __init__(self, tree_branch, _is_root):
            self._is_root = _is_root
            self.fields = []
            self.tree_branch = tree_branch
            self.data = []
            for item in tree_branch.iterfields(include_groups=True,
                                               traverse_repeats=False):
                if item.type == 'repeat':
                    self.fields.append(ExportBunch(item, _is_root=False))
                else:
                    self.fields.append(item)

        @property
        def iterfields(self):
            for field in self.fields:
                _is_nested = isinstance(field, ExportBunch)
                indeces = (0,)
                yield (_is_nested, field, indeces)

        def dump_fields(self):
            return [
                field.dump_fields() if _is_nested else field._full_path
                for (_is_nested, field) in self.iterfields
            ]

        def format_field(self, field, submission, cur_indeces):
            if cur_indeces in submission[field._full_path]:
                key = (field._full_path,) + cur_indeces
                value = submission[field._full_path][cur_indeces]
                return (key, value)

        def gather_data(self, submission, cur_indeces=None):
            out = {}
            if cur_indeces is None:
                cur_indeces = tuple()

            for (_is_nested, field, _indeces) in self.iterfields:
                if _is_nested:
                    cur_index = 0
                    full_indeces = cur_indeces + (cur_index,)
                    key = (field.tree_branch._full_path,) + full_indeces
                    values = field.gather_data(submission, full_indeces)
                    while values:
                        cur_index += 1
                        key = (field.tree_branch._full_path,) + full_indeces
                        values = field.gather_data(submission, full_indeces)
                        full_indeces = cur_indeces + (cur_index,)
                else:
                    (key, val) = self.format_field(field, submission, cur_indeces)
                    if val in [False, None]:
                        return False
                    else:
                        out[key] = val
            return out

    _exp = ExportBunch(v1._tree, _is_root=True)

    shouldbe = {
        ('r1[]', 0): {
            ('r1[]/q1',): 1,
            ('r1[]/r2[]', 0): {
                ('r1[]/r2[]/q2',): 2,
            },
            ('r1[]/r2[]', 1): {
                ('r1[]/r2[]/q2',): 3,
            },
        },
        ('r1[]', 1): {
            ('r1[]/q1',): 4,
            ('r1[]/r2[]', 0): {
                ('r1[]/r2[]/q2',): 5,
            },
            ('r1[]/r2[]', 1): {
                ('r1[]/r2[]/q2',): 6,
            },
            ('r1[]/r2[]', 2): {
                ('r1[]/r2[]/q2',): 7,
            },
        },
        ('r1[]', 2): {
            ('r1[]/q1',): 8,
            ('r1[]/r2[]', 0): {
                ('r1[]/r2[]/q2',): 9
            }
        }
    }
    _out = _exp.gather_data(xr)
    import pprint
    pprint.pprint(_out)
    assert _out.keys() == shouldbe.keys()
