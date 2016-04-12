# coding: utf-8

from __future__ import (unicode_literals, print_function, absolute_import,
                        division)


try:
    from cyordereddict import OrderedDict
except ImportError:
    from collections import OrderedDict

from collections import Counter

from ..submission import FormSubmission


class AutoReport(object):

    def __init__(self, form_versions):
        self.versions = form_versions

    def get_fields_for_all_versions(self):
        """ Return 2 mappings containing fields

            This is needed because when making an report for several
            versions of the same form, fields get added, removed, and
            edited. Hence we pre-generate mappings containing fields
             for all versions so we can use them later as a
            canvas to keep the export coherent.

            Labels are used as column headers.

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
                new_fields = section.fields.items()

                for i, (new_field_name, new_field_obj) in enumerate(new_fields):

                    # The field already exists, let's replace it with the
                    # last version
                    if new_field_name in processed_field_names:
                        final_list_copy = enumerate(list(final_field_list))
                        for y, (name, field) in final_list_copy:
                            if name == new_field_name:
                                final_list_copy[y] = field
                                break
                        continue

                    # The field needs to be inserted at the proper place.
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
                                    final_field_list[y] = field
                                    break
                            break
                    else:
                        # We could not find a following_new_field,
                        # so ad it at the end
                        final_field_list.append(new_field_obj)

                    processed_field_names.add(new_field_obj)

        return [field for field in final_field_list if field.has_stats]

    def get_stats(self, submissions, fields=()):

        all_fields = self.get_fields_for_all_versions()
        fields = set(fields)
        versions = self.versions

        if not fields:
            fields = all_fields
        else:
            fields = [field for field in all_fields if field.name in fields]

        metrics = OrderedDict((field.name, Counter()) for field in fields)

        for version_id, entries in submissions:
            # Skip unrequested versions
            if version_id not in versions:
                continue

            # TODO: change this to use __version__
            for entry in entries:
                # TODO: do we really need FormSubmission ?
                entry = FormSubmission(entry).data
                for field in fields:
                    if field.has_stats:
                        counter = metrics[field.name]
                        counter[entry.get(field.path)] += 1

        for field in fields:
            yield (field.name, field.get_stats(metrics[field.name]))
