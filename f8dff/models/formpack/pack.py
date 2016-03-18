# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

import json
import difflib

from collections import OrderedDict

from .version import FormVersion
from ...models.formpack.utils import get_version_identifiers


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
        except KeyError:
            raise KeyError('formpack with version [%s] not found' % str(index))
        except IndexError:
            raise IndexError('version at index %d is not available' % index)

    def _stats(self):
        _stats = OrderedDict()
        _stats['id_string'] = self.id_string
        _stats['versions'] = len(self.versions)
        _stats['submissions'] = self.submissions_count()
        _stats['row_count'] = len(self[-1]._v.get('content', {})
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

    def submissions_count(self):
        sc = 0
        for v in self.versions.values():
            sc += v.submissions_count()
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
            for submission in version.submissions:
                yield submission

    def export(self, header_lang=None, translation=None,
               group_sep=None, version=-1):
        '''Create an export for a given version of the form '''
        return Export(self[version], header_lang=header_lang,
                      translation=translation, group_sep=group_sep,
                      dataset_name='submissions')


class Export(object):

    def __init__(self, form_version, translation="_default",
                 header_lang=None, group_sep="/",
                 dataset_name="submissions"):

        self.submissions = form_version.submissions
        self.sections = form_version.sections
        self.translation = translation
        self.group_sep = group_sep
        self.dataset_name = dataset_name

        header_lang = header_lang or translation
        self.labels = form_version.get_labels(header_lang, group_sep)

        self.reset()

    def __iter__(self):
        return self.get_all_formated_submissions()

    def reset(self):
        """ Reset sections and indexes to initial values """

        # Current section and indexes in the process of generating the export
        # Those values are state used in format_one_submission to know
        # where we are in the submission tree. This mean this class is NOT
        # thread safe.
        self._indexes = {n: dict(current=1, parent=None) for n in self.sections}

    def get_all_formated_submissions(self):
        """ Return the a generators yielding formatted chunks of the data set"""
        self.reset()
        for submission in self.submissions:
            yield self.format_one_submission([submission.data],
                                             self.dataset_name)

    def format_one_submission(self, submission, current_section):

        # 'section' is the name of what will become sheets in xls.
        # If you don't have repeat groups, there is only one section
        # containing all the formatted data.
        # If you have repeat groups, you will have one section per repeat
        # group.
        section = self.sections[current_section]

        # 'chunks' is a mapping of section names with associated formatted data
        # for one submission. It's used to handle repeat groups.
        # Without repeat groups, chunks has only one section mapping to a
        # list of one row.
        #
        # However, if you have repeat groups, chunks will looks like this:
        #
        # {'first_section': [[A, B, C, index=i]],
        #  'second_section': [
        #       [D, E, F, index=x, parent_index=i],
        #       [D, E, F, index=y, parent_index=i],
        #       [D, E, F, index=z, parent_index=i],
        #  'third_section': [
        #       [G, H, parent_index=x],
        #       [G, H, parent_index=x],
        #       [G, H, parent_index=y],
        #       [G, H, parent_index=y],
        #       [G, H, parent_index=z],
        #       [G, H, parent_index=z],
        #  ]}
        #
        chunks = OrderedDict()

        # 'rows' will contain all the formatted entries for the current
        # section. If you don't have repeat-group, there is only one section
        # with a row of size one.
        # But if you have repeat groups, then rows will contain one row for
        # each entry the user submitted. Of course, for the first section,
        # this will always contains only one row.
        rows = chunks[current_section] = []

        # Link between the parent and its children in a sub-section.
        # Indeed, with repeat groups, entries are nested. Since we flatten
        # them out, we need a way to tell the end user which entries was
        # previously part of a bigger entry. The index is like an auto-increment
        # id that we generate on the fly on the parent, and add it to
        # the children like a foreign key.
        indexes = self._indexes[current_section]

        # Deal with only one level of nesting of the submission, since
        # this method is later called recursively for each repeat group.
        # Each level correspond to one section, so eventually one sheet
        # in an xls doc. Althougt the first level will have only one entries,
        # when repeat groups are involved, deeper levels can have an
        # arbitrary number of entries depending of the user input.
        for entry in submission:

            # Format one entry and add it to the rows for this section
            row = []
            for field in section.fields.values():
                cell = field.format(entry.get(field.path), self.translation)
                row.append(cell)
            rows.append(row)

            # Process all repeat groups of this level
            for child_section in section.children:
                # Because submissions are nested, we flatten them out by reading
                # the whole submission tree recursively, formatting the entries,
                # and adding the results to the list of rows for this section.
                chunk = self.format_one_submission(submission[child_section],
                                                   child_section)
                chunks.update(chunk)

            # Set links between sections
            if section.children:
                row.append(indexes['current'])

            if section.children:
                row.append(section.parent.name)
                row.append(indexes['parent'])

            indexes['current'] += 1

        return chunks

    def to_dict(self):
        '''
            This defeats the purpose of using generators, but it's useful for tests
        '''

        d = OrderedDict()

        for section, fields in self.labels.items():
            d[section] = {'fields': list(fields), 'data': []}

        for chunk in self:
            for section_name, rows in chunk.items():
                d[section_name]['data'].extend(rows)

        return d
