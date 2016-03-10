# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

import json
import difflib

from collections import OrderedDict

from .version import FormVersion
from f8dff.models.formpack.utils import get_version_identifiers


class FormPack:
    def __init__(self, *args, **kwargs):
        self.versions = OrderedDict()
        self.id_string = kwargs.get('id_string')
        if 'name' in kwargs:
            raise ValueError('FormPack cannot have name. consider '
                             'using id_string, title, or description')
        self._x = kwargs
        self.title = kwargs.get('title')
        self.asset_type = kwargs.get('asset_type')
        for v in kwargs.get('versions', []):
            self.load_version(v)
        if 'submissions_xml' in kwargs:
            self._load_submissions_xml(kwargs.get('submissions_xml'))

    def __repr__(self):
        return '<models.formpack.pack.FormPack %s>' % self._stats()

    def lookup(self, prop, default=None):
        # can't use a one liner because sometimes self.prop is None
        result = getattr(self, prop, default)
        if result is None:
            return default
        return result

    def __getitem__(self, index):
        try:
            if isinstance(index, int):
                return tuple(self.versions.values())[index]
            else:
                return self.versions[index]
        except IndexError:
            raise IndexError('formpack with version [%s] not found' % str(index))

    def _stats(self):
        _stats = OrderedDict()
        _stats['id_string'] = self.id_string
        _stats['versions'] = len(self.versions)
        _stats['submissions'] = self._submissions_count()
        _stats['row_count'] = len(self.versions[-1]._v.get('content', {})
                                                      .get('survey', []))
        # returns stats in the format [ key="value" ]
        return '\n\t'.join(map(lambda key: '%s="%s"' % (
                            key, str(_stats[key])), _stats.keys()))

    def _load_submissions_xml(self, submissions):
        for submission_xml in submissions:
            (id_string, version_id) = get_version_identifiers(submission_xml)
            if version_id not in self.versions:
                raise KeyError('version [%s] is not available' % version_id)
            cur_ver = self.versions[version_id]
            cur_ver._load_submission_xml(submission_xml)

    def load_version(self, form_version_data):
        form_version = FormVersion(form_version_data, self)
        version_id = form_version.version_id
        if version_id in self.versions:
            if version_id is None:
                raise ValueError('cannot have two versions without '
                                 'a "version" id specified')
            else:
                raise ValueError('cannot have duplicate version id: %s'
                                 % version_id)

        if form_version.id_string:
            if self.id_string and self.id_string != form_version.id_string:
                raise ValueError('Versions must of the same form must '
                                 'share an id_string: %s != %s' % (
                                    self.id_string,
                                    form_version.id_string,
                                 ))

            self.id_string = form_version.id_string
        if (self.title is None) and form_version.version_title:
            self.title = form_version.version_title
        self.versions[version_id] = form_version

    def version_diff(self, vn1, vn2):
        v1 = self.versions[vn1]
        v2 = self.versions[vn2]

        def summr(v):
            return json.dumps(v._v.get('content'),
                              indent=4,
                              sort_keys=True,
                              ).splitlines(1)
        out = []
        for line in difflib.unified_diff(summr(v1),
                                         summr(v2),
                                         fromfile="v%d" % vn1,
                                         tofile="v%d" % vn2,
                                         n=1):
            out.append(line)
        return ''.join(out)

    def _submissions_count(self):
        sc = 0
        for v in self.versions.values():
            sc += v._submissions_count()
        return sc

    def to_dict(self, **kwargs):
        out = {
            u'versions': [v.to_dict() for v in self.versions.values()],
        }
        if self.title is not None:
            out[u'title'] = self.title
        if self.id_string is not None:
            out[u'id_string'] = self.id_string
        if self.asset_type is not None:
            out[u'asset_type'] = self.asset_type
        return out

    def to_json(self, **kwargs):
        return json.dumps(self.to_dict(), **kwargs)

    def submissions_list(self):
        return list(self.submissions_gen())

    def submissions_gen(self):
        for version in self.versions.values():
            for submission in version._submissions:
                yield submission


    def _to_ss_generator(self, header_lang=None,
                            version=None):
        '''
        ss_generator means "spreadsheet" structure with generators
        instead of lists.

        for simplicity's sake, it will initially export a single version
        of the form (specified by ID)
        '''

        sheets = OrderedDict()

        # default to the latest version
        if version is None:
            version = -1

        export_version = self[version]

        column_formatters = export_version._formatters

        if header_lang is not None:
            names_and_labels = export_version.get_column_names_for_lang(header_lang)
            labels = [label for name, label in names_and_labels]
        else:
            labels = column_formatters.keys()

        def _generator():
            for submission in self.submissions_gen():
                row = []
                for (colname, formatter) in column_formatters.iteritems():
                    row.append(formatter.format(submission._data.get(colname)))
                yield row
        sheets['submissions'] = [labels, _generator()]
        return sheets

    def _export_to_lists(self, **kwargs):
        '''
        this defeats the purpose of using generators, but it's useful for tests
        '''
        gens = self._to_ss_generator(**kwargs)
        out = []
        for key in gens.keys():
            (headers, _gen) = gens[key]
            vals = list(_gen)
            out.append([key, [headers, vals]])
        return out
