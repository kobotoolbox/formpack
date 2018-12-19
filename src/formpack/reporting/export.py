# coding: utf-8

from __future__ import (unicode_literals, print_function, absolute_import,
                        division)

from inspect import isclass

try:
    from cyordereddict import OrderedDict
except ImportError:
    from collections import OrderedDict

from collections import defaultdict

import zipfile
import xlsxwriter

from ..submission import FormSubmission
from ..schema import CopyField
from ..utils.spss import spss_labels_from_variables_dict
from ..utils.string import unicode, unique_name_for_xls
from ..utils.flatten_content import flatten_tag_list
from ..constants import UNSPECIFIED_TRANSLATION, TAG_COLUMNS_AND_SEPARATORS


class Export(object):

    def __init__(self, formpack, form_versions, lang=UNSPECIFIED_TRANSLATION,
                 group_sep="/", hierarchy_in_labels=False,
                 version_id_keys=[],
                 multiple_select="both", copy_fields=(), force_index=False,
                 title="submissions", tag_cols_for_header=None):
        """

        :param formpack: FormPack
        :param form_versions: OrderedDict
        :param lang: string, False (`constants.UNSPECIFIED_TRANSLATION`), or
            None (`constants.UNTRANSLATED`).
        :param group_sep: bool.
        :param hierarchy_in_labels: bool.
        :param version_id_keys: list.
        :param multiple_select: string.
        :param copy_fields: tuple. It can be a mix of strings and
            `schema.fields.*CopyFields` classes (e.g.
            `ValidationStatusCopyField`)
        :param force_index: bool.
        :param title: string
        :param tag_cols_for_header: list
        """

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

        # If some fields need to be arbitrarily copied, add them
        # to the first section
        if copy_fields:
            for version in iter(form_versions.values()):
                first_section = next(iter(version.sections.values()))
                for copy_field in copy_fields:
                    if isclass(copy_field):
                        dumb_field = copy_field(section=first_section)
                    else:
                        dumb_field = CopyField(copy_field, section=first_section)
                    first_section.fields[dumb_field.name] = dumb_field

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
                (field.contextual_name, field)
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
                    if isclass(copy_field):
                        auto_field_names.append(
                            "_submission_{}".format(copy_field.FIELD_NAME))
                    else:
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
                    [flatten_tag_list(field.tags, tag_cols_and_seps)]
                    * len(field.value_names)
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
                        if isclass(extra_mapping_field):
                            row[
                                u"_submission_{}".format(extra_mapping_field.FIELD_NAME)
                            ] = extra_mapping_values.get(extra_mapping_field, "")
                        else:
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
        workbook = xlsxwriter.Workbook(filename, {'constant_memory': True})
        workbook.use_zip64()

        sheets = {}

        sheet_name_mapping = {}

        sheet_row_positions = defaultdict(lambda: 0)
        def _append_row_to_sheet(sheet_, data):
            # XlsxWriter doesn't have a method like this built in, so we have
            # to keep track of the current row for each sheet
            row_index = sheet_row_positions[sheet_]
            sheet_.write_row(
                row=row_index,
                col=0,
                data=data
            )
            row_index += 1
            sheet_row_positions[sheet_] = row_index

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
                    current_sheet = workbook.add_worksheet(sheet_name)
                    sheets[sheet_name] = current_sheet

                    _append_row_to_sheet(
                        current_sheet,
                        self.labels[section_name]
                    )

                    # Include specified tag columns as extra header rows
                    tag_rows = self.get_header_rows_for_tag_cols(section_name)
                    for tag_row in tag_rows:
                        _append_row_to_sheet(current_sheet, tag_row)

                for row in rows:
                    _append_row_to_sheet(current_sheet, row)

        workbook.close()

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

    def to_spss_labels(self, output_file):
        '''
        Write SPSS commands that set question and choice labels, creating a ZIP
        file containing one SPSS file per translation. This includes *no* data!

        :param output_file: a file-like object opened for writing
        '''
        all_versions = self.formpack.versions.values()
        all_translations = set()
        map(all_translations.update, [v.translations for v in all_versions])
        all_fields = self.formpack.get_fields_for_versions()

        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as z_out:
            for translation in all_translations:
                '''
                For each translation, we need to produce a dictionary like:
                    {
                        'question_name1': {
                            'label': 'I am the label of question 1!',
                            'values': {
                                'option1': 'Label option 1',
                                'option2': 'Label option 2'
                            }
                        },
                        'question_name2': {
                            'label': 'I am question 2, unconstrained by
                                     'predetermined values!'
                        }
                    }
                '''
                question_dict = OrderedDict()
                for field in all_fields:
                    # Even with `multiple_select='summary'`, we can still get
                    # multiple names and labels per question for things like
                    # `FormGPSField` (`geopoint`)
                    xml_names = field.get_labels(lang=UNSPECIFIED_TRANSLATION,
                                                 multiple_select='summary')
                    assert xml_names[0] == field.name
                    labels = field.get_labels(lang=translation,
                                              multiple_select='summary')
                    for name, label in zip(xml_names, labels):
                        question_dict[name] = {
                            'label': label,
                            'data_type': field.data_type,
                        }
                    if hasattr(field, 'choice'):
                        choices = OrderedDict()
                        for option in field.choice.options.keys():
                            choices[option] = field.get_translation(
                                val=option, lang=translation
                            )
                        question_dict[field.name]['values'] = choices
                # Convert the question/choice names and labels into SPSS
                # commands
                spss_label_commands = spss_labels_from_variables_dict(
                    question_dict)
                # Write the SPSS commands into a file for this particular
                # language
                title = self.formpack.title
                if translation:
                    rest_of_filename = ' - '.join(
                        ('', translation, 'SPSS labels.sps')
                    )
                else:
                    rest_of_filename = ' - '.join(
                        ('', 'SPSS labels.sps')
                    )
                # TODO: move this constant
                MAXIMUM_FILENAME_LENGTH = 240
                overrun = (
                    len(title)
                        + len(rest_of_filename)
                        - MAXIMUM_FILENAME_LENGTH
                )
                if overrun > 0:
                    # TODO: trim the title in a right-to-left-friendly way
                    # TODO: deal with excessively long language names
                    title = ellipsize(title, len(title) - overrun)
                filename = title + rest_of_filename
                z_out.writestr(
                    # `utf-8-sig` includes the BOM, which SPSS needs to
                    # recognize the encoding
                    filename, spss_label_commands.encode('utf-8-sig')
                )
