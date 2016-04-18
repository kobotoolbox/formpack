# coding: utf-8

from __future__ import (unicode_literals, print_function, absolute_import,
                        division)


try:
    from cyordereddict import OrderedDict
except ImportError:
    from collections import OrderedDict

from collections import Counter, defaultdict

from ..submission import FormSubmission


class AutoReport(object):

    def __init__(self, formpack, form_versions):
        self.formpack = formpack
        self.versions = form_versions

    def _calculate_stats(self, submissions, fields, versions, lang):

        metrics = {field.name: Counter() for field in fields}

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
                        raw_value = entry.get(field.path)
                        if raw_value is not None:
                            values = field.parse_values(entry.get(field.path))
                            counter.update(values)
                            counter['__submissions__'] += 1
                        else:
                            counter[None] += 1

        for field in fields:
            yield (field.get_labels(lang)[0],
                   field.get_stats(metrics[field.name], lang=lang))

    def _aggregate_stats(self, submissions, fields, versions, lang, group_by):

        # Remove the group_by field from the values to get stats on
        fields = [field for field in fields if field.name != group_by]

        # Mapping {field_name: {groupby_value1: stats,
        #                       groupby_value2: stats...},
        #          ...}
        metrics = {f.name: defaultdict(Counter) for f in fields}

        for version_id, entries in submissions:

            # Skip unrequested versions
            if version_id not in versions:
                continue

            # TODO: change this to use __version__
            for entry in entries:
                # TODO: do we really need FormSubmission ?

                # since we are going to pop one entry, we make a copy
                # of it to avoid side effect
                entry = dict(FormSubmission(entry).data)
                group = entry.pop(group_by, None)

                for field in fields:

                    if field.has_stats:

                        counter = metrics[field.name][group]
                        raw_value = entry.get(field.path)

                        if raw_value is not None:
                            values = field.parse_values(entry.get(field.path))
                            counter.update(values)
                            counter['__submissions__'] += 1
                        else:
                            counter[None] += 1

        for field in fields:
            stats = []
            # TODO: use views for python 2 and 3
            for group, values in metrics[field.name].items():
                stats.append((group, field.get_stats(values, lang=lang)))

            yield (field.get_labels(lang)[0], stats)

    def get_stats(self, submissions, fields=(), lang=None, group_by=None):

        versions = self.versions

        all_fields = self.formpack.get_fields_for_versions(versions)
        all_fields = [field for field in all_fields if field.has_stats]

        fields = set(fields)
        if not fields:
            fields = all_fields
        else:
            fields.add(group_by)
            fields = [field for field in all_fields if field.name in fields]

        if group_by:
            try:
                group_by_field = next(f for f in fields if f.name == group_by)
                group_by = group_by_field.path
            except StopIteration:
                raise ValueError('No field matching name "%s" '
                                 'for group_by' % group_by)

            return self._aggregate_stats(submissions, fields,
                                         versions, lang, group_by)

        return self._calculate_stats(submissions, fields, versions, lang)
