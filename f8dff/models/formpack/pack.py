# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

import json
import difflib

from collections import OrderedDict

import xlsxwriter

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
        return Export([self[version]], header_lang=header_lang,
                      translation=translation, group_sep=group_sep,
                      dataset_name='submissions')


class Export(object):

    def __init__(self, form_versions, translation="_default", header_lang=None,
                 group_sep="/", multiple_select="both",
                 not_applicable_marker="<N/A>",
                 dataset_name="submissions"):

        self.translation = translation
        self.group_sep = group_sep
        self.dataset_name = dataset_name
        self.versions = form_versions
        self.not_applicable_marker = not_applicable_marker

        # this deals with merging all form versions headers and labels
        header_lang = header_lang or translation
        params = (header_lang, group_sep, multiple_select)
        res = self.get_fields_and_labels_for_all_versions(*params)
        self.sections, self.labels = res

        self.reset()

    def __iter__(self):
        return self.get_all_formated_submissions()

    def get_all_formated_submissions(self):
        """ Return the a generators yielding formatted chunks of the data set"""
        self.reset()
        for version in self.versions:
            first_section = version.sections[self.dataset_name]
            for submission in version.submissions:
                yield self.format_one_submission([submission.data],
                                                 first_section)

    def reset(self):
        """ Reset sections and indexes to initial values """

        # Current section and indexes in the process of generating the export
        # Those values are state used in format_one_submission to know
        # where we are in the submission tree. This mean this class is NOT
        # thread safe.
        self._indexes = {n: 1 for n in self.sections}
        # N.B: indexes are not affected by form versions

    def get_fields_and_labels_for_all_versions(self, lang, group_sep,
                                                multiple_select="both"):
        """ Return 2 mappings containing field and labels by section

            This is needed because when making an export for several
            versions of the same form, fields get added, removed, and
            edited. Hence we pre-generate mappings conteaining labels
            and field for all version so we can use them later as a
            canvas to keep the export coherent.

            Labels are used as column headers.

            Field are used to create rows of data from submission.
        """

        section_fields = OrderedDict()  # {section: [(name, field), (name...))]}
        section_labels = OrderedDict()  # {section: [field_label, field_label]}
        processed_fields = {}  # Used to avoid expensive lookups

        # Create the initial field mappings from the first form version
        for section_name, section in self.versions[0].sections.items():

            # Field mapping to the section containing them
            section_fields[section_name] = list(section.fields.items())

            # Field labels list mapping to the section containing them
            one_section_labels = section_labels[section_name] = []
            for field in section.fields.values():
                labels = field.get_labels(lang, group_sep, multiple_select)
                one_section_labels.append(labels)

            # Set of processed field names for fast lookup
            field_names = section_fields[section_name]
            processed_fields[section_name] = set(field_names)

        # Process any new field added in the next versions
        # The hard part is to insert it at a position that makes sense
        for version in self.versions[1:]:
            for section_name, section in version.sections.items():

                # List of fields and labels we already got for this section
                # from all previous versions
                base_fields_list = section_fields[section_name]
                processed_field_names = processed_fields[section_name]
                base_fields_labels = section_labels[section_name]

                # Potential new fields we want to add
                new_fields = list(section.fields.keys())

                for i, new_field in enumerate(new_fields):

                    new_field_name, _ = new_field

                    # Extract the labels for this field, language, group
                    # separator and muliple_select policy
                    labels = field.get_labels(lang, group_sep, multiple_select)
                    # WARNING, labels is a list of labels for this field
                    # since multiple select answers can span on several columns

                    # We already processed that field and don't need to add it
                    # But we replace the labels for it by the last
                    # version available
                    if new_field_name in processed_field_names:
                        base_labels = enumerate(list(base_fields_labels))
                        for i, (name, field) in base_labels:
                            if name == new_field_name:
                                base_fields_labels[i] = labels
                                break
                        continue

                    # If the field appear at the start, append it at the
                    # begining of the lists
                    if i == 0:
                        base_fields_list.insert(0, new_field_name)
                        base_fields_labels.insert(0, labels)
                        continue

                    # For any other field, we need a more advanced position
                    # logic.
                    # We take this new field, and look for all new fields after
                    # it to find the first one that is already in the base
                    # fields. Then we get its index, so we can insert our fresh
                    # new field right before it. This gives us a coherent
                    # order of fields so that they are always, at worst,
                    # adjacent to the last field they used to be to.
                    for following_new_field in new_fields[i+1:]:
                        if following_new_field in processed_field_names:
                            base_fields = enumerate(list(base_fields_list))
                            for i, (name, field) in enumerate(base_fields):
                                if name == following_new_field:
                                    base_fields_list.insert(i, new_field)
                                    base_fields_labels.insert(i, labels)
                                    break
                            break
                    else:  # We could not find one, so at it at the end
                        base_fields_list.append(new_field_name)
                        base_fields_labels.append(i, labels)

                    processed_field_names.add(new_field_name)

        # Flatten field labels and names. Indeed, field.get_labels()
        # and self.names return a list because a multiple select field can
        # have several values. We needed them grouped to insert them at the
        # proper index, but now we want just list of all of them.

        # Flatten all the names for all the value of all the fields
        for section, fields in list(section_fields.items()):
            name_lists = (field.value_names for field_name, field in fields)
            names = [name for name_list in name_lists for name in name_list]
            section_fields[section] = names

        # Flatten all the labels for all the headers of all the fields
        for section, labels in list(section_labels.items()):
            labels = [label for label_group in labels for label in label_group]
            section_labels[section] = labels

        return section_fields, section_labels

    def format_one_submission(self, submission, current_section):

        # 'current_section' is the name of what will become sheets in xls.
        # If you don't have repeat groups, there is only one section
        # containing all the formatted data.
        # If you have repeat groups, you will have one section per repeat
        # group. Section are hierarchical, and can have a parent and one
        # or more children. format_one_submission() is called recursivelly
        # with each section to process them all.

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
        rows = chunks[current_section.name] = []

        # Deal with only one level of nesting of the submission, since
        # this method is later called recursively for each repeat group.
        # Each level correspond to one section, so eventually one sheet
        # in an xls doc. Althougt the first level will have only one entries,
        # when repeat groups are involved, deeper levels can have an
        # arbitrary number of entries depending of the user input.
        for entry in submission:

            # Format one entry and add it to the rows for this section

            # Create an empty canvas with column names and empty values
            # This is done to handle mulitple form versions in parallel which
            # may more or less columns than each others.
            row = OrderedDict.fromkeys(self.sections[current_section.name],
                                       self.not_applicable_marker)
            for field in current_section.fields.values():
                # TODO: pass a context to fields so they can all format ?
                if field.can_format:
                    # get submission value for this field
                    val = entry.get(field.path)
                    # get a mapping of {"col_name": "val", ...}
                    cells = field.format(val, self.translation)
                    # fill in the canvas
                    row.update(cells)

            # Link between the parent and its children in a sub-section.
            # Indeed, with repeat groups, entries are nested. Since we flatten
            # them out, we need a way to tell the end user which entries was
            # previously part of a bigger entry. The index is like an auto-increment
            # id that we generate on the fly on the parent, and add it to
            # the children like a foreign key.
            # TODO: remove that for HTML export
            if current_section.children:
                row['_index'] = self._indexes[current_section.name]

            if current_section.parent:
                row['_parent_table_name'] = current_section.parent.name
                row['_parent_index'] = self._indexes[current_section.parent.name]

            rows.append(list(row.values()))

            # Process all repeat groups of this level
            for child_section in current_section.children:
                # Because submissions are nested, we flatten them out by reading
                # the whole submission tree recursively, formatting the entries,
                # and adding the results to the list of rows for this section.
                chunk = self.format_one_submission(entry[child_section.path],
                                                   child_section)
                chunks.update(chunk)

            self._indexes[current_section.name] += 1

        return chunks

    def to_dict(self):
        '''
            This defeats the purpose of using generators, but it's useful for tests
        '''

        d = OrderedDict()

        for section, labels in self.labels.items():
            d[section] = {'fields': list(labels), 'data': []}

        for chunk in self:
            for section_name, rows in chunk.items():
                d[section_name]['data'].extend(rows)

        return d

    def to_csv(self, sep=";", quote='"'):
        '''
            Return a generator yielding csv lines.

            We don't use the csv module to avoid buffering the lines
            in memory.
        '''

        sections = list(self.labels.items())

        if len(sections) > 1:
            raise RuntimeError("CSV export does not support repeatable groups")

        def format_line(line, sep, quote):
            return quote + (quote + sep + quote).join(line) + quote

        section, labels = sections[0]
        yield format_line(labels, sep, quote)

        for chunk in self:
            for section_name, rows in chunk.items():
                for row in rows:
                    yield format_line(row, sep, quote)

    def to_xlsx(self, filename):

        workbook = xlsxwriter.Workbook(filename, {'constant_memory': True})

        sheets = {}

        for chunk in self:
            for section_name, rows in chunk.items():

                try:
                    cursor = sheets[section_name]
                    current_sheet = cursor['sheet']
                except KeyError:
                    current_sheet = workbook.add_worksheet(section_name)
                    cursor = sheets[section_name] = {
                        "sheet": current_sheet,
                        "row": 0,
                    }

                    for i, label in enumerate(self.labels[section_name]):
                        current_sheet.write(0, i, label)
                    cursor["row"] = 1

                for row in rows:
                    y = cursor["row"]
                    for i, cell in enumerate(row):
                        current_sheet.write(y, i, cell)
                    cursor["row"] += 1

        workbook.close()
