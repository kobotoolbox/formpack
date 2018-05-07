# coding: utf-8

from __future__ import (unicode_literals, print_function, absolute_import,
                        division)


try:
    from cyordereddict import OrderedDict
except ImportError:
    from collections import OrderedDict

import openpyxl

from ..submission import FormSubmission
from ..schema import CopyField
from ..utils.string import unicode, unique_name_for_xls
from ..utils.flatten_content import flatten_tag_list
from ..constants import UNSPECIFIED_TRANSLATION, TAG_COLUMNS_AND_SEPARATORS


class Export(object):

    def __init__(self, formpack, form_versions, lang=UNSPECIFIED_TRANSLATION,
                 group_sep="/", hierarchy_in_labels=False,
                 version_id_keys=[],
                 multiple_select="both", copy_fields=(), force_index=False,
                 title="submissions", tag_cols_for_header=None):

        self.formpack = formpack
        self.lang = lang
        self.group_sep = group_sep
        self.title = title
        self.versions = form_versions
        self.copy_fields = copy_fields
        self.force_index = force_index
        self.herarchy_in_labels = hierarchy_in_labels
        self.version_id_keys = version_id_keys
        self.__r_groups_submission_mapping_values = {}

        if tag_cols_for_header is None:
            tag_cols_for_header = []
        self.tag_cols_for_header = tag_cols_for_header

        # If some fields need to be arbitrarly copied, add them
        # to the first section
        if copy_fields:
            for version in iter(form_versions.values()):
                first_section = next(iter(version.sections.values()))
                for name in copy_fields:
                    dumb_field = CopyField(name, section=first_section)
                    first_section.fields[name] = dumb_field

        # this deals with merging all form versions headers and labels
        params = (
            lang, group_sep, hierarchy_in_labels, multiple_select,
            tag_cols_for_header,
        )
        res = self.get_fields_labels_tags_for_all_versions(*params)
        self.sections, self.labels, self.tags = res

        self.reset()

        # Some cache to improve perfs on large datasets
        self._row_cache = {}
        self._empty_row = {}

        for section_name, fields in self.sections.items():
            self._row_cache[section_name] = OrderedDict.fromkeys(fields, '')
            self._empty_row[section_name] = dict(self._row_cache[section_name])

    def parse_submissions(self, submissions):
        """Return the a generators yielding formatted chunks of the data set"""
        self.reset()
        versions = self.versions
        for entry in submissions:
            version_id = None

            # find the first version_id present in the submission
            for _key in self.version_id_keys:
                if _key in entry:
                    version_id = entry.get(_key)
                    break

            try:
                section = versions[version_id].sections[self.title]
                submission = FormSubmission(entry)
                yield self.format_one_submission([submission.data], section)
            except KeyError:
                pass


    def reset(self):
        """ Reset sections and indexes to initial values """

        # Current section and indexes in the process of generating the export
        # Those values are state used in format_one_submission to know
        # where we are in the submission tree. This mean this class is NOT
        # thread safe.
        self._indexes = {n: 1 for n in self.sections}
        self.__r_groups_submission_mapping_values = {}
        # N.B: indexes are not affected by form versions

    def get_fields_labels_tags_for_all_versions(self,
                                                lang=UNSPECIFIED_TRANSLATION,
                                                group_sep="/",
                                                hierarchy_in_labels=False,
                                                multiple_select="both",
                                                tag_cols_for_header=None):
        """ Return 3 mappings containing field, labels, and tags by section

            This is needed because when making an export for several
            versions of the same form, fields get added, removed, and
            edited. Hence we pre-generate mappings containing labels,
            fields, and tags for all versions so we can use them later as a
            canvas to keep the export coherent.

            Labels are used as column headers.

            Field are used to create rows of data from submission.

            Tags specified by `tag_cols_for_header` are included as additional
            column headers (in CSV and XLSX exports only).
        """

        if tag_cols_for_header is None:
            tag_cols_for_header = []
        try:
            tag_cols_and_seps = {
                col: TAG_COLUMNS_AND_SEPARATORS[col]
                    for col in tag_cols_for_header
            }
        except KeyError as e:
            raise RuntimeError(
                '{} is not in TAG_COLUMNS_AND_SEPARATORS'.format(e.message))

        section_fields = OrderedDict()  # {section: [(name, field), (name...))]}
        section_labels = OrderedDict()  # {section: [field_label, field_label]}
        section_tags = OrderedDict()  # {section: [{column_name: tag_string, ...}, ...]}

        all_fields = self.formpack.get_fields_for_versions(self.versions)
        all_sections = {}

        # List of fields we generate ourself to add at the very ends
        # of the field list
        auto_fields = OrderedDict()

        for field in all_fields:
            section_fields.setdefault(field.section.name, []).append(
                (field.name, field)
            )
            section_labels.setdefault(field.section.name, []).append(
                field.get_labels(lang, group_sep,
                                 hierarchy_in_labels,
                                 multiple_select)
            )
            all_sections[field.section.name] = field.section

        for section_name, section in all_sections.items():
            # Append optional additional fields
            auto_field_names = auto_fields[section_name] = []
            if section.children or self.force_index:
                auto_field_names.append('_index')

            if section.parent:
                auto_field_names.append('_parent_table_name')
                auto_field_names.append('_parent_index')
                # Add extra fields
                for copy_field in self.copy_fields:
                    auto_field_names.append(
                        "_submission_{}".format(copy_field))

        # Flatten field labels and names. Indeed, field.get_labels()
        # and self.names return a list because a multiple select field can
        # have several values. We needed them grouped to insert them at the
        # proper index, but now we want just list of all of them.

        # Flatten all the names for all the value of all the fields
        for section, fields in list(section_fields.items()):
            name_lists = []
            tags = []
            for _field_data in fields:
                if len(_field_data) != 2:
                    # e.g. [u'location', u'_location_latitude',...]
                    continue
                (field_name, field) = _field_data
                name_lists.append(field.value_names)

                # Add the tags for this field. If the field has multiple
                # labels, add the tags once for each label
                tags.extend(
                    [flatten_tag_list(field.tags, tag_cols_and_seps)] *
                        len(field.value_names)
                )


            names = [name for name_list in name_lists for name in name_list]

            # add auto fields:
            names.extend(auto_fields[section])
            tags.extend([{}] * len(auto_fields[section]))

            section_fields[section] = names
            section_tags[section] = tags

        # Flatten all the labels for all the headers of all the fields
        for section, labels in list(section_labels.items()):
            labels = [label for label_group in labels for label in label_group]

            # add auto fields (names and labels are the same)
            labels.extend(auto_fields[section])

            section_labels[section] = labels

        return section_fields, section_labels, section_tags

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

        # Some local aliases to get better perfs
        _section_name = current_section.name
        _lang = self.lang
        _empty_row = self._empty_row[_section_name]
        _indexes = self._indexes
        row = self._row_cache[_section_name]
        _fields = tuple(current_section.fields.values())

        # 'rows' will contain all the formatted entries for the current
        # section. If you don't have repeat-group, there is only one section
        # with a row of size one.
        # But if you have repeat groups, then rows will contain one row for
        # each entry the user submitted. Of course, for the first section,
        # this will always contains only one row.
        rows = chunks[_section_name] = []

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

            # We don't build a new dict everytime, instead, we reuse the
            # previous one, but we reset it, to gain some perfs.
            row.update(_empty_row)

            for field in _fields:
                # TODO: pass a context to fields so they can all format ?
                if field.can_format:

                    try:
                        # get submission value for this field
                        val = entry[field.path]
                        # get a mapping of {"col_name": "val", ...}
                        cells = field.format(val, _lang)

                        # save fields value if they match parent mapping fields.
                        # Useful to map children to their parent when flattening groups.
                        if field.path in self.copy_fields:
                            if _section_name not in self.__r_groups_submission_mapping_values:
                                self.__r_groups_submission_mapping_values[_section_name] = {}
                            self.__r_groups_submission_mapping_values[_section_name].update(cells)

                    except KeyError:
                        cells = field.empty_result

                    # fill in the canvas
                    row.update(cells)

            # Link between the parent and its children in a sub-section.
            # Indeed, with repeat groups, entries are nested. Since we flatten
            # them out, we need a way to tell the end user which entries was
            # previously part of a bigger entry. The index is like an auto-increment
            # id that we generate on the fly on the parent, and add it to
            # the children like a foreign key.
            # TODO: remove that for HTML export
            if '_index' in row:
                row['_index'] = _indexes[_section_name]

            if '_parent_table_name' in row:
                row['_parent_table_name'] = current_section.parent.name
                row['_parent_index'] = _indexes[row['_parent_table_name']]
                extra_mapping_values = self.__get_extra_mapping_values(current_section.parent)
                if extra_mapping_values:
                    for extra_mapping_field in self.copy_fields:
                        row[
                            u"_submission_{}".format(extra_mapping_field)
                        ] = extra_mapping_values.get(extra_mapping_field, "")

            rows.append(list(row.values()))

            # Process all repeat groups of this level
            for child_section in current_section.children:
                # Because submissions are nested, we flatten them out by reading
                # the whole submission tree recursively, formatting the entries,
                # and adding the results to the list of rows for this section.
                nested_data = entry.get(child_section.path)
                if nested_data:
                    chunk = self.format_one_submission(entry[child_section.path],
                                                       child_section)
                    for key, value in chunk.iteritems():
                        if key in chunks:
                            chunks[key].extend(value)
                        else:
                            chunks[key] = value

            _indexes[_section_name] += 1

        return chunks

    def get_header_rows_for_tag_cols(self, section_name):
        rows = []
        for tag_col in self.tag_cols_for_header:
            row = []
            found_tag = False
            for field_tags in self.tags[section_name]:
                try:
                    row.append(field_tags[tag_col])
                except KeyError:
                    # Perfectly acceptable for a field not to have
                    # a particular tag
                    row.append('')
                else:
                    found_tag = True

            if found_tag:
                rows.append(row)

        return rows

    def to_dict(self, submissions):
        '''
            This defeats the purpose of using generators, but it's useful for tests
        '''

        d = OrderedDict()

        for section, labels in self.labels.items():
            d[section] = {'fields': list(labels), 'data': []}

        for chunk in self.parse_submissions(submissions):
            for section_name, rows in chunk.items():
                d[section_name]['data'].extend(rows)

        return d

    def to_csv(self, submissions, sep=";", quote='"'):
        '''
            Return a generator yielding csv lines.

            We don't use the csv module to avoid buffering the lines
            in memory.
        '''

        sections = list(self.labels.items())

        # if len(sections) > 1:
        #     raise RuntimeError("CSV export does not support repeatable groups")

        def format_line(line, sep, quote):
            line = [unicode(x) for x in line]
            return quote + (quote + sep + quote).join(line) + quote

        section, labels = sections[0]
        yield format_line(labels, sep, quote)

        # Include specified tag columns as extra header rows
        tag_rows = self.get_header_rows_for_tag_cols(section)
        for tag_row in tag_rows:
            yield format_line(tag_row, sep, quote)

        for chunk in self.parse_submissions(submissions):
            for section_name, rows in chunk.items():
                if section == section_name:
                    for row in rows:
                        yield format_line(row, sep, quote)

    def to_table(self, submissions):

        table = OrderedDict(((s, [list(l)]) for s, l in self.labels.items()))

        # build the table
        for chunk in self.parse_submissions(submissions):
            for section_name, rows in chunk.items():
                section = table[section_name]
                for row in rows:
                    section.append(row)

        return table

    def to_xlsx(self, filename, submissions):

        workbook = openpyxl.Workbook(write_only=True)

        sheets = {}

        sheet_name_mapping = {}

        for chunk in self.parse_submissions(submissions):
            for section_name, rows in chunk.items():
                try:
                    sheet_name = sheet_name_mapping[section_name]
                except KeyError:
                    sheet_name = unique_name_for_xls(
                        section_name, sheet_name_mapping.values())
                    sheet_name_mapping[section_name] = sheet_name
                try:
                    current_sheet = sheets[sheet_name]
                except KeyError:
                    current_sheet = workbook.create_sheet(title=sheet_name)
                    sheets[sheet_name] = current_sheet

                    current_sheet.append(self.labels[section_name])

                    # Include specified tag columns as extra header rows
                    tag_rows = self.get_header_rows_for_tag_cols(section_name)
                    for tag_row in tag_rows:
                        current_sheet.append(tag_row)

                for row in rows:
                    current_sheet.append(row)

        workbook.save(filename)

    def to_html(self, submissions):
        '''
            Yield lines of and HTML table strings.
        '''

        yield "<table>"

        sections = list(self.labels.items())

        yield "<thead>"

        section, labels = sections[0]
        yield "<tr><th>" + "</th><th>".join(labels) + "</th></tr>"

        yield "</thead>"

        yield "<tbody>"

        for chunk in self.parse_submissions(submissions):
            for section_name, rows in chunk.items():
                if section == section_name:
                    for row in rows:
                        row = [unicode(x) for x in row]
                        yield "<tr><td>" + "</td><td>".join(row) + "</td></tr>"

        yield "</tbody>"

        yield "</table>"

    def __get_extra_mapping_values(self, section):
        """
        Tries to find a match within self.__r_groups_submission_mapping_values dict
        with the name of parent section.
        If there are no matches, it tries with the grandparent until a match is found
        (or no grandparents are found)

        :param section: FormSection
        :return: dict
        """

        if section:
            values = self.__r_groups_submission_mapping_values.get(section.name)
            if values is None:
                return self.__get_extra_mapping_values(getattr(section, "parent"))
            else:
                return values

        return None
