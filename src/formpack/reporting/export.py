# coding: utf-8
import json
import re
import zipfile
from collections import defaultdict, OrderedDict
from inspect import isclass
from typing import (
    Dict,
    Generator,
    Iterator,
    Optional,
)

import xlsxwriter

from ..constants import (
    GEO_QUESTION_TYPES,
    TAG_COLUMNS_AND_SEPARATORS,
    UNSPECIFIED_TRANSLATION,
    UNSPECIFIED_HEADER_LANG,
)
from ..schema import CopyField, FormField
from ..submission import FormSubmission
from ..utils.exceptions import FormPackExcelError, FormPackGeoJsonError
from ..utils.flatten_content import flatten_tag_list
from ..utils.geojson import field_and_response_to_geometry
from ..utils.iterator import get_first_occurrence
from ..utils.replace_aliases import EXTENDED_MEDIA_TYPES
from ..utils.spss import spss_labels_from_variables_dict
from ..utils.string import unique_name_for_xls
from ..utils.text import get_valid_filename


class Export:
    def __init__(
        self,
        formpack,
        form_versions,
        lang=UNSPECIFIED_TRANSLATION,
        group_sep='/',
        hierarchy_in_labels=False,
        version_id_keys=[],
        multiple_select='both',
        copy_fields=(),
        force_index=False,
        title='submissions',
        tag_cols_for_header=None,
        header_lang=UNSPECIFIED_HEADER_LANG,
        filter_fields=(),
        xls_types_as_text=True,
        include_media_url=False,
    ):
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
        lang_header
        :param header_lang: string, False (`constants.UNSPECIFIED_TRANSLATION`), or
            None (`constants.UNTRANSLATED`), if not set, default value equal lang arg.
        :param filter_fields: list
        :param xls_types_as_text: bool
        :param include_media_url: bool
        """

        self.formpack = formpack
        self.analysis_form = formpack.analysis_form
        self.lang = lang
        self.header_lang = self.lang if header_lang == UNSPECIFIED_HEADER_LANG else header_lang
        self.group_sep = group_sep
        self.title = title
        self.versions = form_versions
        self.multiple_select = multiple_select
        self.copy_fields = copy_fields
        self.force_index = force_index
        self.herarchy_in_labels = hierarchy_in_labels
        self.version_id_keys = version_id_keys
        self.filter_fields = filter_fields
        self.xls_types_as_text = xls_types_as_text
        self.include_media_url = include_media_url
        self.__r_groups_submission_mapping_values = {}

        if tag_cols_for_header is None:
            tag_cols_for_header = []
        self.tag_cols_for_header = tag_cols_for_header

        _filter_fields = []
        for item in self.filter_fields:
            item = re.sub(r'^_supplementalDetails/', '', item)
            _filter_fields.append(item)
        self.filter_fields = _filter_fields

        # If some fields need to be arbitrarily copied, add them
        # to the first section
        if copy_fields:
            for version in iter(form_versions.values()):
                first_section = next(iter(version.sections.values()))
                for copy_field in copy_fields:
                    if isclass(copy_field):
                        dumb_field = copy_field(section=first_section)
                    else:
                        dumb_field = CopyField(
                            copy_field, section=first_section
                        )
                    first_section.fields[dumb_field.name] = dumb_field

        # Some copy fields are classes, some strings -- collect their field
        # names for later use
        self.copy_field_names = [
            getattr(copy_field, 'FIELD_NAME', copy_field)
            for copy_field in self.copy_fields
        ]

        # this deals with merging all form versions headers and labels
        res = self.get_fields_labels_tags_for_all_versions(
            lang,
            group_sep,
            hierarchy_in_labels,
            self.header_lang,
            tag_cols_for_header,
        )
        self.sections, self.labels, self.tags = res

        self.reset()

        # Some cache to improve perfs on large datasets
        self._row_cache = {}
        self._empty_row = {}

        for section_name, fields in self.sections.items():
            self._row_cache[section_name] = OrderedDict.fromkeys(fields, '')
            self._empty_row[section_name] = dict(self._row_cache[section_name])

    def get_version_for_submission(self, submission):
        """
        Return the `FormVersion` for this submission, or `None` if none can be
        found
        """
        version_id = None
        # find the first version_id present in the submission
        for _key in self.version_id_keys:
            if _key in submission:
                version_id = submission.get(_key)
                break
        try:
            return self.versions[version_id]
        except KeyError:
            return None

    def parse_one_submission(self, submission, version=None):
        """
        Parse a single submission and return a formatted 'chunks' structure;
        see format_one_submission() for details

        Args:
            version (FormVersion): optional, explicit version to use for this
                submission instead of inferring the version from the submission
                itself
        """
        if not version:
            version = self.get_version_for_submission(submission)
        if not version:
            # TODO: somehow include this submission anyway; see
            # https://github.com/kobotoolbox/formpack/issues/164
            return None
        # `format_one_submission()` will recurse through all the sections; get
        # the first one to start
        section = get_first_occurrence(version.sections.values())
        submission = FormSubmission(submission)
        return self.format_one_submission([submission.data], section)

    def parse_submissions(self, submissions):
        """
        Return a generator yielding formatted 'chunks' for each submission from
        the data set
        """
        self.reset()
        for submission in submissions:
            formatted_chunks = self.parse_one_submission(submission)
            if not formatted_chunks:
                continue
            yield formatted_chunks

    def reset(self):
        """
        Reset sections and indexes to initial values
        """

        # Current section and indexes in the process of generating the export
        # Those values are state used in format_one_submission to know
        # where we are in the submission tree. This mean this class is NOT
        # thread safe.
        self._indexes = {n: 1 for n in self.sections}
        self.__r_groups_submission_mapping_values = {}
        # N.B: indexes are not affected by form versions

    def get_fields_labels_tags_for_all_versions(
        self,
        lang=UNSPECIFIED_TRANSLATION,
        group_sep='/',
        hierarchy_in_labels=False,
        header_lang=UNSPECIFIED_TRANSLATION,
        tag_cols_for_header=None,
    ):
        """
        Return 3 mappings containing field, labels, and tags by section

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
                '{} is not in TAG_COLUMNS_AND_SEPARATORS'.format(e.message)
            )

        all_fields = self.formpack.get_fields_for_versions(self.versions)

        # Ensure that fields are filtered if they've been specified, otherwise
        # carry on as usual
        if self.analysis_form:
            all_fields = self.analysis_form.insert_analysis_fields(all_fields)

        if self.filter_fields:
            all_fields = [
                field
                for field in all_fields
                if field.path in self.filter_fields
            ]

        # Collect all the sections regardless if they contain any fields
        all_sections = {}
        for version in self.versions.values():
            all_sections.update(version.sections)

        # {section: [field_object, field_object, …], …}
        # {section: [field_label, field_label, …], …}
        # {section: [{column_name: tag_string, …}, …]}
        section_fields = OrderedDict((s, []) for s in all_sections)
        section_labels = OrderedDict((s, []) for s in all_sections)
        section_tags = OrderedDict((s, []) for s in all_sections)

        # List of fields we generate ourselves to add at the very end
        # of the field list
        auto_fields = OrderedDict()

        for field in all_fields:
            section_fields.setdefault(field.section.name, []).append(field)
            section_labels.setdefault(field.section.name, []).append(
                field.get_labels(
                    lang=header_lang,
                    group_sep=group_sep,
                    hierarchy_in_labels=hierarchy_in_labels,
                    multiple_select=self.multiple_select,
                    include_media_url=self.include_media_url,
                )
            )

        for section_name, section in all_sections.items():
            # Append optional additional fields
            auto_field_names = auto_fields[section_name] = []
            if section.children or self.force_index:
                auto_field_names.append('_index')

            if section.parent:
                auto_field_names.append('_parent_table_name')
                auto_field_names.append('_parent_index')
                # Add extra fields
                for copy_field in self.copy_field_names:
                    auto_field_names.append('_submission_{}'.format(copy_field))

        # Flatten field labels and names. Indeed, field.get_labels()
        # and self.names return a list because a multiple select field can
        # have several values. We needed them grouped to insert them at the
        # proper index, but now we want just list of all of them.

        # Flatten all the names for all the value of all the fields
        for section, fields in section_fields.items():
            name_lists = []
            tags = []
            for field in fields:
                value_names = field.get_value_names(
                    multiple_select=self.multiple_select,
                    include_media_url=self.include_media_url,
                )
                name_lists.append(value_names)

                # Add the tags for this field. If the field has multiple
                # labels, add the tag for the first label *only*. Insert blanks
                # for the subsequent fields. See
                # https://github.com/kobotoolbox/formpack/issues/208
                tags.extend([flatten_tag_list(field.tags, tag_cols_and_seps)])
                tags.extend([{}] * (len(value_names) - 1))

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

    def format_one_submission(
        self,
        submission,
        current_section,
        attachments=None,
    ):

        # 'current_section' is the name of what will become sheets in xls.
        # If you don't have repeat groups, there is only one section
        # containing all the formatted data.
        # If you have repeat groups, you will have one section per repeat
        # group. Section are hierarchical, and can have a parent and one
        # or more children. format_one_submission() is called recursively
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

        def _get_attachment(val, field, attachments):
            """
            Filter attachments for filenames that match the submission field's
            value
            """
            # Not all submissions will have attachments and we only want to
            # consider media types
            if (
                field.data_type not in EXTENDED_MEDIA_TYPES
                or not attachments
                or val is None
            ):
                return []

            _val = get_valid_filename(val)
            return [
                f
                for f in attachments
                if re.match(fr'^.*/{_val}$', f['filename']) is not None
            ]

        if self.analysis_form:
            _fields = self.analysis_form.insert_analysis_fields(_fields)

        # Ensure that fields are filtered if they've been specified, otherwise
        # carry on as usual
        if self.filter_fields:
            _fields = tuple(
                field for field in _fields if field.path in self.filter_fields
            )

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

            attachments = entry.get('_attachments') or attachments

            for field in _fields:
                # TODO: pass a context to fields so they can all format ?
                if field.can_format:
                    # get submission value for this field
                    val = field.get_value_from_entry(entry)
                    # get the attachment for this field
                    attachment = _get_attachment(val, field, attachments)
                    # get a mapping of {"col_name": "val", ...}
                    cells = field.format(
                        val=val,
                        lang=_lang,
                        multiple_select=self.multiple_select,
                        xls_types_as_text=self.xls_types_as_text,
                        attachment=attachment,
                        include_media_url=self.include_media_url,
                    )

                    # save fields value if they match parent mapping fields.
                    # Useful to map children to their parent when flattening groups.
                    if field.path in self.copy_field_names:
                        if (
                            _section_name
                            not in self.__r_groups_submission_mapping_values
                        ):
                            self.__r_groups_submission_mapping_values[
                                _section_name
                            ] = {}
                        self.__r_groups_submission_mapping_values[
                            _section_name
                        ].update(cells)

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
                extra_mapping_values = self.__get_extra_mapping_values(
                    current_section.parent
                )
                if extra_mapping_values:
                    for extra_mapping_field in self.copy_field_names:
                        row[
                            '_submission_{}'.format(extra_mapping_field)
                        ] = extra_mapping_values.get(extra_mapping_field, '')

            rows.append(list(row.values()))

            # Process all repeat groups of this level
            for child_section in current_section.children:
                # Because submissions are nested, we flatten them out by reading
                # the whole submission tree recursively, formatting the entries,
                # and adding the results to the list of rows for this section.
                nested_data = entry.get(child_section.path)
                if nested_data:
                    chunk = self.format_one_submission(
                        entry[child_section.path],
                        child_section,
                        attachments=attachments,
                    )
                    for key, value in iter(chunk.items()):
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
        """
        This defeats the purpose of using generators, but it's useful for tests
        """

        d = OrderedDict()

        for section, labels in self.labels.items():
            d[section] = {'fields': list(labels), 'data': []}

        for chunk in self.parse_submissions(submissions):
            for section_name, rows in chunk.items():
                d[section_name]['data'].extend(rows)

        return d

    def to_csv(self, submissions, sep=';', quote='"'):
        """
        Return a generator yielding csv lines.

        We don't use the csv module to avoid buffering the lines
        in memory.
        """

        sections = list(self.labels.items())

        # if len(sections) > 1:
        #     raise RuntimeError("CSV export does not support repeatable groups")

        def escape_quote(value, quote):
            """
            According to https://www.ietf.org/rfc/rfc4180.txt,

                If double-quotes are used to enclose fields, then a
                double-quote appearing inside a field must be escaped by
                preceding it with another double quote.

            We will follow this convention by doubling `quote` wherever it
            appears in `value`, regardless of what `quote` is. Perhaps this
            is not the best idea.
            """
            return value.replace(quote, quote * 2)

        def format_line(line, sep, quote):
            line = [escape_quote(str(x), quote) for x in line]
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

    def to_geojson(
        self,
        submissions: Iterator,
        flatten: bool = True,
        geo_question_name: Optional[str] = None,
    ) -> Generator:
        """
        Returns a GeoJSON `FeatureCollection` as a generator object, where each
        submission is a `Feature` with `geometry` taken from the response to
        the question. All question/response pairs are included in the
        `properties` of each `Feature` if they are not a geo question
        themselves or are not empty. As with `to_csv()`, repeating groups are
        not included. There are two modes that the method can run in:
        `flatten=True` and `flatten=False`. If `True`, all geo responses will
        be a `Feature` within a single `FeatureCollection` — regardless of
        whether there are multiple geo questions within a single survey
        response. If `False`, each survey response will have its own
        `FeatureCollection` and all geo responses within that survey will be
        `Feature`s within that.

        Example:

        If `flatten=True`:
            {
                "type": "FeatureCollection",
                "name": "name of the first section",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [
                                longitude,
                                latitude,
                                altitude
                            ]
                        },
                        "properties": {
                            ...
                        },
                    },
                    {
                        ...
                    },
                    ...
                ]
            }
        """

        # Force to text otherwise might fail JSON serializing
        self.xls_types_as_text = True
        # Format as summary for multiple select question types
        self.multiple_select = 'summary'

        # Consider the first section only (discard repeating groups)
        first_section_name = get_first_occurrence(self.sections.keys())
        labels = self.labels[first_section_name]
        sections = self.sections[first_section_name]

        # Set up some convenient properties when `yield`ing
        feature_array_preamble = '\n'.join(
            [
                '{',
                '"type": "FeatureCollection",',
                '"name": "{name}",'.format(name=first_section_name),
                '"features": [',
            ]
        )
        feature_array_epilogue = '\n]\n}'
        array_preamble = '[\n'
        array_epilogue = '\n]'
        comma_newline = ',\n'
        newline = '\n'

        if flatten:
            yield feature_array_preamble
        else:
            yield array_preamble

        self.reset()  # since we're not using `parse_submissions()`

        first = True
        for submission in submissions:
            if not flatten:
                if first:
                    yield feature_array_preamble
                    first = False
                else:
                    yield comma_newline + feature_array_preamble

            # We need direct access to the field objects (available inside the
            # version) and the unformatted submission data
            version = self.get_version_for_submission(submission)
            formatted_chunks = self.parse_one_submission(submission, version)
            if not formatted_chunks:
                continue

            all_fields = version.sections[first_section_name].fields.values()
            all_geo_fields = [
                f for f in all_fields if f.data_type in GEO_QUESTION_TYPES
            ]
            all_geo_field_names = [f.name for f in all_geo_fields]

            all_geo_field_labels = []
            for field in all_geo_fields:
                all_geo_field_labels += field.get_labels(lang=self.lang)

            # Iterate through all geo questions and format only those that have
            # been answered
            first_geo = True
            for geo_field in all_geo_fields:
                # Handle the API query param of geo_question_name if present by
                # skipping all geo fields that don't match the specified
                # question rather than filtering outside of the loop
                if (
                    geo_question_name is not None
                    and geo_question_name != geo_field.name
                ):
                    continue

                rows = formatted_chunks[first_section_name]
                for row in rows:
                    try:
                        geo_response = submission[geo_field.path]
                    except KeyError:
                        # Discard submissions with missing geo data
                        continue
                    try:
                        feature_geometry = field_and_response_to_geometry(
                            geo_field, geo_response
                        )
                    except FormPackGeoJsonError:
                        # Discard submissions with invalid geo data
                        continue
                    except RuntimeError:
                        # If we're here, the field has an non-geo type. Continue in
                        # the hope that other submissions belong to better versions
                        # of the form
                        continue

                    feature_properties = OrderedDict()
                    for name, label, row_value in zip(sections, labels, row):
                        # Skip all geo fields, including the current one, as
                        # it's unnecessary to repeat in the Feature's
                        # properties. Also skip over fields that are blank
                        if (
                            label in all_geo_field_names
                            or label in all_geo_field_labels
                            or not row_value
                        ):
                            continue

                        feature_properties.update({label: row_value})

                    feature = {
                        'type': 'Feature',
                        'geometry': feature_geometry,
                        'properties': feature_properties,
                    }

                    if flatten:
                        if first:
                            separator = newline
                            first = False
                        else:
                            separator = comma_newline
                    else:
                        if first_geo:
                            separator = newline
                            first_geo = False
                        else:
                            separator = comma_newline
                    yield separator + json.dumps(feature)

            if not flatten:
                yield feature_array_epilogue

        if flatten:
            yield feature_array_epilogue
        else:
            yield array_epilogue

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
        workbook = xlsxwriter.Workbook(
            filename,
            {
                'constant_memory': True,
                'default_date_format': 'yyyy-mm-dd',
                'remove_timezone': True,
            },
        )
        workbook.use_zip64()

        sheets = {}

        sheet_name_mapping = {}

        sheet_row_positions = defaultdict(lambda: 0)

        def _append_row_to_sheet(sheet_, data):
            # XlsxWriter doesn't have a method like this built in, so we have
            # to keep track of the current row for each sheet
            row_index = sheet_row_positions[sheet_]
            for col_index, cell_value in enumerate(data):
                # Call `write()` directly to facilitate error handling (as
                # opposed to `write_row()`)
                error = sheet_.write(row_index, col_index, cell_value)
                if error == 0:
                    continue
                else:
                    # Fall back on writing as a string if there are problems
                    # like having too many URLs in the worksheet (see #309)
                    error = sheet_.write_string(
                        row_index, col_index, cell_value
                    )
                # https://xlsxwriter.readthedocs.io/worksheet.html#write_string
                if error == -1:
                    # Fail now if the data set doesn't fit into an Excel file
                    raise FormPackExcelError(
                        f'Row {row_index} or column {col_index} is out of'
                        ' worksheet bounds'
                    )
                if error == -2:
                    # If the value was truncated silently, prepend a warning
                    # and write again
                    cell_value = (
                        '<WARNING: Truncated to Excel limit of 32767'
                        ' characters!>'
                        + cell_value
                    )
                    sheet_.write_string(row_index, col_index, cell_value)

            row_index += 1
            sheet_row_positions[sheet_] = row_index

        for chunk in self.parse_submissions(submissions):
            for section_name, rows in chunk.items():
                try:
                    sheet_name = sheet_name_mapping[section_name]
                except KeyError:
                    sheet_name = unique_name_for_xls(
                        section_name, sheet_name_mapping.values()
                    )
                    sheet_name_mapping[section_name] = sheet_name
                try:
                    current_sheet = sheets[sheet_name]
                except KeyError:
                    current_sheet = workbook.add_worksheet(sheet_name)
                    sheets[sheet_name] = current_sheet

                    _append_row_to_sheet(
                        current_sheet, self.labels[section_name]
                    )

                    # Include specified tag columns as extra header rows
                    tag_rows = self.get_header_rows_for_tag_cols(section_name)
                    for tag_row in tag_rows:
                        _append_row_to_sheet(current_sheet, tag_row)

                for row in rows:
                    _append_row_to_sheet(current_sheet, row)

        workbook.close()

    def to_html(self, submissions):
        """
        Yield lines of and HTML table strings.
        """

        yield '<table>'

        sections = list(self.labels.items())

        yield '<thead>'

        section, labels = sections[0]
        yield '<tr><th>' + '</th><th>'.join(labels) + '</th></tr>'

        yield '</thead>'

        yield '<tbody>'

        for chunk in self.parse_submissions(submissions):
            for section_name, rows in chunk.items():
                if section == section_name:
                    for row in rows:
                        row = [str(x) for x in row]
                        yield '<tr><td>' + '</td><td>'.join(row) + '</td></tr>'

        yield '</tbody>'

        yield '</table>'

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
                return self.__get_extra_mapping_values(
                    getattr(section, 'parent')
                )
            else:
                return values

        return None

    def to_spss_labels(self, output_file):
        """
        Write SPSS commands that set question and choice labels, creating a ZIP
        file containing one SPSS file per translation. This includes *no* data!

        :param output_file: a file-like object opened for writing
        """
        all_versions = self.formpack.versions.values()
        all_translations = set()
        for v in all_versions:
            all_translations.update(v.translations)

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
                    xml_names = field.get_labels(
                        lang=UNSPECIFIED_TRANSLATION, multiple_select='summary'
                    )
                    assert xml_names[0] == field.name
                    labels = field.get_labels(
                        lang=translation, multiple_select='summary'
                    )
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
                    question_dict
                )
                # Write the SPSS commands into a file for this particular
                # language
                title = self.formpack.title
                if translation:
                    rest_of_filename = ' - '.join(
                        ('', translation, 'SPSS labels.sps')
                    )
                else:
                    rest_of_filename = ' - '.join(('', 'SPSS labels.sps'))
                # TODO: move this constant
                MAXIMUM_FILENAME_LENGTH = 240
                overrun = (
                    len(title) + len(rest_of_filename) - MAXIMUM_FILENAME_LENGTH
                )
                if overrun > 0:
                    # TODO: trim the title in a right-to-left-friendly way
                    # TODO: deal with excessively long language names
                    title = ellipsize(title, len(title) - overrun)
                filename = title + rest_of_filename
                z_out.writestr(
                    # `utf-8-sig` includes the BOM, which SPSS needs to
                    # recognize the encoding
                    filename,
                    spss_label_commands.encode('utf-8-sig'),
                )
