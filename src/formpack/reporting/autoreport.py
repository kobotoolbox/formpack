# coding: utf-8
from __future__ import (division, print_function, absolute_import,
                        unicode_literals)

import logging
from collections import defaultdict

from ..constants import UNSPECIFIED_TRANSLATION
from ..submission import FormSubmission
from ..utils.ordered_collection import OrderedCounter


class AutoReportStats(object):

    def __init__(self, autoreport, stats, submissions_count,
                 submission_counts_by_version):
        self.autoreport = autoreport
        self.stats = stats
        self.submissions_count = submissions_count
        self.submission_counts_by_version = submission_counts_by_version

    def __iter__(self):
        return self.stats


class AutoReport(object):

    def __init__(self, formpack, form_versions):
        self.formpack = formpack
        self.versions = form_versions

    def _get_version_id_from_submission(self, submission):
        """
        Get the version ID from the provided submission, or `None` if not found.

        :param dict submission: An individual data submission.
        :rtype: `formpack.utils.string.str_types` or NoneType
        """
        version_id_keys = set(self.formpack.version_id_keys()).\
            intersection(set(submission.keys()))
        if len(version_id_keys) == 0:
            return None
        elif len(version_id_keys) > 1:
            possible_versions_dict = {v_id_ky: submission[v_id_ky] for v_id_ky in version_id_keys}
            raise ValueError('Submission version ambiguous. Multiple possible version ID keys: {}.'
                             .format(possible_versions_dict))
        version_id_key = version_id_keys.pop()

        version_id = submission.get(version_id_key)
        return version_id

    def _calculate_stats(self, submissions, fields, versions, lang):

        metrics = {field.name: OrderedCounter() for field in fields}

        submissions_count = 0
        submission_counts_by_version = OrderedCounter()

        for entry in submissions:

            version_id = self._get_version_id_from_submission(entry)
            if version_id not in versions:
                continue

            submissions_count += 1
            submission_counts_by_version[version_id] += 1

            # TODO: do we really need FormSubmission ?
            entry = FormSubmission(entry).data
            for field in fields:
                if field.has_stats:
                    counter = metrics[field.name]
                    raw_value = entry.get(field.path)
                    if raw_value is not None:
                        try:
                            values = list(field.parse_values(raw_value))
                        except ValueError as e:
                            # TODO: Remove try/except when
                            # https://github.com/kobotoolbox/formpack/issues/151
                            # is fixed?
                            logging.warning(str(e), exc_info=True)
                            # Treat the bad value as a blank response
                            counter[None] += 1
                        else:
                            counter.update(values)
                            counter['__submissions__'] += 1
                    else:
                        counter[None] += 1

        def stats_generator():
            for field in fields:
                yield (field,
                       field.get_labels(lang)[0],
                       field.get_stats(metrics[field.name], lang=lang))

        return AutoReportStats(self, stats_generator(), submissions_count,
                               submission_counts_by_version)

    def _disaggregate_stats(self, submissions, fields, versions, lang, split_by_field):

        # We want only the most used values so we build a separate counter
        # for it to filter them
        splitters_rank = OrderedCounter()
        # Extract the split_by field from the values to get stats on

        # total number of submissions
        submissions_count = 0
        submission_counts_by_version = OrderedCounter()

        fields = [f for f in fields if f != split_by_field]

        # Then we map fields, values and splitters:
        #          {field_name1: {
        #                  'value1': OrderedCounter(
        #                      (splitter1, x),
        #                      (splitter2, y)
        #                       ...
        #                  ),
        #                  value2: ...
        #              },
        #              field_name2...},
        #         ...}
        #
        metrics = {f.name: defaultdict(OrderedCounter) for f in fields}

        for sbmssn in submissions:

            # Skip unrequested versions
            version_id = self._get_version_id_from_submission(sbmssn)
            if version_id not in versions:
                continue

            # TODO: change this to use __version__

            submissions_count += 1
            submission_counts_by_version.update([version_id])

            # TODO: do we really need FormSubmission ?

            # since we are going to pop one entry, we make a copy
            # of it to avoid side effect
            entry = dict(FormSubmission(sbmssn).data)
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
        for val, _ in splitters_rank.most_common(6):
            if val is None:
                continue
            if hasattr(split_by_field, 'get_translation'):
                trans = split_by_field.get_translation(val, lang)
            else:
                trans = val
            top_splitters.append((val, trans))

        if len(top_splitters) > 5:
            top_splitters.pop()

        # TODO: Figure out a better way of reproducibly ordering values.
        top_splitters.sort(key=lambda val_: val_[0])

        def stats_generator():
            for field in fields:
                stats = field.get_disaggregated_stats(metrics[field.name], lang=lang,
                                                      top_splitters=top_splitters)
                yield (field, field.get_labels(lang)[0], stats)

        return AutoReportStats(self, stats_generator(), submissions_count,
                               submission_counts_by_version)

    def get_stats(self, submissions, fields=(), lang=UNSPECIFIED_TRANSLATION, split_by=None):

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
