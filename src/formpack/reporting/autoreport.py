# coding: utf-8

from __future__ import (unicode_literals, print_function, absolute_import,
                        division)


try:
    from cyordereddict import OrderedDict
except ImportError:
    from collections import OrderedDict

from ..submission import FormSubmission


class AutoReport(object):

    def __init__(self, form_versions):

        # this deals with merging all form versions headers and labels
        header_lang = header_lang or translation
        params = (header_lang, group_sep, hierarchy_in_labels, multiple_select)
        res = self.get_fields_and_labels_for_all_versions(*params)
        self.sections, self.labels = res

        self.reset()


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

    def get_fields_and_labels_for_all_versions(self):
        """ Return 2 mappings containing field and labels by section

            This is needed because when making an export for several
            versions of the same form, fields get added, removed, and
            edited. Hence we pre-generate mappings conteaining labels
            and field for all version so we can use them later as a
            canvas to keep the export coherent.

            Labels are used as column headers.

            Field are used to create rows of data from submission.
        """

        final_field_list = []  # [(name, field), (name...))]
        processed_field_names = set()  # avoid expensive look ups
        versions = list(self.versions.values())

        # Create the initial field mappings from the first form version
        for section in versions[0].sections.values():
            final_field_list.extend(section.fields.values())
            processed_field_names.update(section.fields.keys())

        # Process any new field added in the next versions
        # The hard part is to insert it at a position that makes sense
        for version in versions[1:]:
            for section_name, section in version.sections.items():

                # Potential new fields we want to add
                new_fields = list(section.fields.items())

                for i, (new_field_name, new_field_obj) in enumerate(new_fields):

                    # We take this new field, and look for all new fields after
                    # it to find the first one that is already in the base
                    # fields. Then we get its index, so we can insert our fresh
                    # new field right before it. This gives us a coherent
                    # order of fields so that they are always, at worst,
                    # adjacent to the last field they used to be to.
                    for following_new_field in new_fields[i+1:]:
                        if following_new_field in processed_field_names:
                            final_list_copy = enumerate(list(final_field_list))
                            for y, (name, field) in final_list_copy:
                                if name == following_new_field:
                                    final_field_list[y] = new_field_obj
                                    break
                            break
                    else:  # We could not find one, so at it at the end
                        final_field_list.append(new_field_obj)

                    processed_field_names.add(new_field_obj)

        return processed_field_names

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
        _translation = self.translation
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
                        cells = field.format(val, _translation)
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
                row['_parent_table_name'] = str(current_section.parent.name)
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
