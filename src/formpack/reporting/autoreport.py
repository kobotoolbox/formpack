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


class AutoReportStats(object):

    def __init__(self, autoreport, stats, submissions_count):
        self.autoreport = autoreport
        self.stats = stats
        self.submissions_count = submissions_count

    def __iter__(self):
        return self.stats


class AutoReport(object):

    def __init__(self, formpack, form_versions):
        self.formpack = formpack
        self.versions = form_versions

    def _calculate_stats(self, submissions, fields, versions, lang):

        metrics = {field.name: Counter() for field in fields}

        submissions_count = 0

        for version_id, entries in submissions:

            # Skip unrequested versions
            if version_id not in versions:
                continue

            # TODO: change this to use __version__
            for entry in entries:

                submissions_count += 1

                # TODO: do we really need FormSubmission ?
                entry = FormSubmission(entry).data
                for field in fields:
                    if field.has_stats:
                        counter = metrics[field.name]
                        raw_value = entry.get(field.path)
                        if raw_value is not None:
                            values = list(field.parse_values(raw_value))
                            counter.update(values)
                            counter['__submissions__'] += 1
                        else:
                            counter[None] += 1

        def stats_generator():
            for field in fields:
                yield (field,
                       field.get_labels(lang)[0],
                       field.get_stats(metrics[field.name], lang=lang))

        return AutoReportStats(self, stats_generator(), submissions_count)

    def _disaggregate_stats(self, submissions, fields, versions, lang, split_by_field):

        # We want only the most used values so we build a separate counter
        # for it to filter them
        splitters_rank = Counter()
        # Extract the split_by field from the values to get stats on

        # total number of submissions
        submissions_count = 0

        fields = [f for f in fields if f != split_by_field]

        # Then we map fields, values and splitters:
        #          {field_name1: {
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

                submissions_count += 1

                # TODO: do we really need FormSubmission ?

                # since we are going to pop one entry, we make a copy
                # of it to avoid side effect
                entry = dict(FormSubmission(entry).data)
                splitter = entry.pop(split_by_field.path, None)

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

                # collect stats for the split_by field
                if splitter is not None:
                    values = split_by_field.parse_values(splitter)
                else:
                    values = (None, )

                splitters_rank.update(values)

        # keep the 5 most encountered split_by value
        top_splitters = []
        for val, count in splitters_rank.most_common(6):
            if val is None:
                continue
            if hasattr(split_by_field, 'get_translation'):
                trans = split_by_field.get_translation(val, lang)
            else:
                trans = val
            top_splitters.append((val, trans))

        if len(top_splitters) > 5:
            top_splitters.pop()

        def stats_generator():
            for field in fields:
                stats = field.get_disaggregated_stats(metrics[field.name], lang=lang,
                                                      top_splitters=top_splitters)
                yield (field, field.get_labels(lang)[0], stats)

        return AutoReportStats(self, stats_generator(), submissions_count)

    def get_stats(self, submissions, fields=(), lang=None, split_by=None):

        all_fields = self.formpack.get_fields_for_versions(self.versions)
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
            except StopIteration:
                raise ValueError('No field matching name "%s" '
                                 'for split_by' % split_by)

            return self._disaggregate_stats(submissions, fields,
                                            self.versions, lang, split_by_field)

        return self._calculate_stats(submissions, fields, self.versions, lang)

