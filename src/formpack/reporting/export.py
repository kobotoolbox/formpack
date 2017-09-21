# coding: utf-8

from __future__ import (unicode_literals, print_function, absolute_import,
                        division)


try:
    from cyordereddict import OrderedDict
except ImportError:
    from collections import OrderedDict

from pyexcelerate import Workbook

from ..submission import FormSubmission
from ..schema import CopyField
from ..utils.string import unicode, unique_name_for_xls


# Copied from onadata/apps/viewer/models/parsed_instance.py; see HACK below
import base64, re
def _decode_from_mongo(key):
    re_dollar = re.compile(r"^%s" % base64.b64encode("$"))
    re_dot = re.compile(r"\%s" % base64.b64encode("."))
    return reduce(lambda s, c: c[0].sub(c[1], s),
                  [(re_dollar, '$'), (re_dot, '.')], key)
# End copy from onadata/apps/viewer/models/parsed_instance.py


class Export(object):

    def __init__(self, form_versions, lang=None,
                 group_sep="/", hierarchy_in_labels=False,
                 multiple_select="both", copy_fields=(), force_index=False,
                 title="submissions"):

        self.lang = lang
        self.group_sep = group_sep
        self.title = title
        self.versions = form_versions
        self.copy_fields = copy_fields
        self.force_index = force_index
        self.herarchy_in_labels = hierarchy_in_labels

        # If some fields need to be arbitrarly copied, add them
        # to the first section
        if copy_fields:
            first_version = next(iter(form_versions.values()))
            first_section = next(iter(first_version.sections.values()))
            for name in copy_fields:
                dumb_field = CopyField(name, section=first_section)
                first_section.fields[name] = dumb_field

        # this deals with merging all form versions headers and labels
        params = (lang, group_sep, hierarchy_in_labels, multiple_select)
        res = self.get_fields_and_labels_for_all_versions(*params)
        self.sections, self.labels = res

        self.reset()

        # Some cache to improve perfs on large datasets
        self._row_cache = {}
        self._empty_row = {}

        for section_name, fields in self.sections.items():
            self._row_cache[section_name] = OrderedDict.fromkeys(fields, '')
            self._empty_row[section_name] = dict(self._row_cache[section_name])

    def parse_submissions(self, submissions):
        """ Return the a generators yielding formatted chunks of the data set"""
        self.reset()
        versions = self.versions
        for version_id, entries in submissions:
            try:
                section = versions[version_id].sections[self.title]
                for entry in entries:
                    # TODO: do we really need FormSubmission ?
                    submission = FormSubmission(entry)
                    yield self.format_one_submission([submission.data], section)
            except KeyError:  # this versions is NOT requested in the export
                pass

    def reset(self):
        """ Reset sections and indexes to initial values """

        # Current section and indexes in the process of generating the export
        # Those values are state used in format_one_submission to know
        # where we are in the submission tree. This mean this class is NOT
        # thread safe.
        self._indexes = {n: 1 for n in self.sections}
        # N.B: indexes are not affected by form versions

    def get_fields_and_labels_for_all_versions(self, lang=None, group_sep="/",
                                                hierarchy_in_labels=False,
                                                multiple_select="both"):
        """ Return 2 mappings containing field and labels by section

            This is needed because when making an export for several
            versions of the same form, fields get added, removed, and
            edited. Hence we pre-generate mappings containing labels
            and fields for all versions so we can use them later as a
            canvas to keep the export coherent.

            Labels are used as column headers.

            Field are used to create rows of data from submission.
        """

        # TODO: refactor this to use FormPack.get_fields_for_versions

        section_fields = OrderedDict()  # {section: [(name, field), (name...))]}
        section_labels = OrderedDict()  # {section: [field_label, field_label]}
        processed_fields = {}  # Used to avoid expensive lookups

        versions = list(self.versions.values())

        # List of fields we generate ourself to add at the very ends
        # of the field list
        auto_fields = OrderedDict()

        # Create the initial field mappings from the first form version
        for section_name, section in versions[0].sections.items():

            # Field mapping to the section containing them
            section_fields[section_name] = list(section.fields.items())

            # Field labels list mapping to the section containing them
            one_section_labels = section_labels[section_name] = []
            for field in section.fields.values():
                labels = field.get_labels(lang, group_sep,
                                          hierarchy_in_labels,
                                          multiple_select)
                one_section_labels.append(labels)

            # Set of processed field names for fast lookup
            field_names = section_fields[section_name]
            processed_fields[section_name] = set(field_names)

            # Append optional additional fields
            auto_field_names = auto_fields[section_name] = []
            if section.children or self.force_index:
                auto_field_names.append('_index')

            if section.parent:
                auto_field_names.append('_parent_table_name')
                auto_field_names.append('_parent_index')

        # Process any new field added in the next versions
        # The hard part is to insert it at a position that makes sense
        for version in versions[1:]:
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
                    labels = field.get_labels(lang, group_sep,
                                              hierarchy_in_labels,
                                              multiple_select)
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
                            base_fields = list(base_fields_list)
                            for y, (name, field) in enumerate(base_fields):
                                if name == following_new_field:
                                    base_fields_list.insert(y, new_field)
                                    base_fields_labels.insert(y, labels)
                                    break
                            break
                    else:  # We could not find one, so ad it at the end
                        base_fields_list.append(new_field_name)
                        base_fields_labels.append(labels)

                    processed_field_names.add(new_field_name)

        # Flatten field labels and names. Indeed, field.get_labels()
        # and self.names return a list because a multiple select field can
        # have several values. We needed them grouped to insert them at the
        # proper index, but now we want just list of all of them.

        # Flatten all the names for all the value of all the fields
        for section, fields in list(section_fields.items()):
            name_lists = (field.value_names for field_name, field in fields)
            names = [name for name_list in name_lists for name in name_list]

            # add auto fields:
            names.extend(auto_fields[section])

            section_fields[section] = names

        # Flatten all the labels for all the headers of all the fields
        for section, labels in list(section_labels.items()):
            labels = [label for label_group in labels for label in label_group]

            # add auto fields (names and labels are the same)
            labels.extend(auto_fields[section])

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
            # HACK: Deal with KC's base64 encoding of characters illegal in
            # Mongo key names. This should not remain in formpack; the grotty
            # submission data should be cleaned before it arrives here
            entry = {
                _decode_from_mongo(key): val for key, val in entry.items()
            }

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
                    chunks.update(chunk)

            _indexes[_section_name] += 1

        return chunks

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

        workbook = Workbook()

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
                    cursor = sheets[sheet_name]
                    current_sheet = cursor['sheet']
                except KeyError:
                    current_sheet = workbook.new_sheet(sheet_name)
                    cursor = sheets[sheet_name] = {
                        "sheet": current_sheet,
                        "row": 2,
                    }

                    for i, label in enumerate(self.labels[section_name], 1):
                        current_sheet.set_cell_value(1, i, label)

                for row in rows:
                    y = cursor["row"]
                    for i, cell in enumerate(row, 1):
                        current_sheet.set_cell_value(y, i, cell)
                    cursor["row"] += 1

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

