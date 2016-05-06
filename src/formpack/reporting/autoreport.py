# coding: utf-8

from __future__ import (unicode_literals, print_function, absolute_import,
                        division)


from operator import itemgetter

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
                            values = list(field.parse_values(raw_value))
                            counter.update(values)
                            counter['__submissions__'] += len(values)
                        else:
                            counter[None] += 1

        for field in fields:
            yield (field,
                   field.get_labels(lang)[0],
                   field.get_stats(metrics[field.name], lang=lang))

    def _disaggregate_stats(self, submissions, fields, versions, lang, split_by):

        # Remove the split_by field from the values to get stats on
        fields = [field for field in fields if field.name != split_by]

        # Mapping {field_name1: {
        #                  'value1': Counter(
        #                      (splitter1, x),
        #                      (splitter2, y)
        #                       ...
        #                  ),
        #                  value2: ...
        #              },
        #              field_name2...},
        #         ...}
        #

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
                splitter = entry.pop(split_by, None)

                for field in fields:

                    if field.has_stats:

                        raw_value = entry.get(field.path)

                        if raw_value is not None:
                            values = field.parse_values(raw_value)
                        else:
                            values = (None,)

                        value_metrics = metrics[field.name]

                        for value in values:
                            counters = value_metrics[value]
                            counters[splitter] += 1

                            if value is not None:
                                counters['__submissions__'] += 1

        for field in fields:
            stats = field.get_disaggregated_stats(metrics[field.name], lang=lang)
            yield (field, field.get_labels(lang)[0], stats)

    def get_stats(self, submissions, fields=(), lang=None, split_by=None):

        versions = self.versions

        all_fields = self.formpack.get_fields_for_versions(versions)
        all_fields = [field for field in all_fields if field.has_stats]

        fields = set(fields)
        if not fields:
            fields = all_fields
        else:
            fields.add(split_by)
            fields = [field for field in all_fields if field.name in fields]

        if split_by:
            try:
                split_by_field = next(f for f in fields if f.name == split_by)
                split_by = split_by_field.path
            except StopIteration:
                raise ValueError('No field matching name "%s" '
                                 'for split_by' % split_by)

            return self._disaggregate_stats(submissions, fields,
                                         versions, lang, split_by)

        return self._calculate_stats(submissions, fields, versions, lang)
