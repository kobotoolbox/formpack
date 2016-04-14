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

    def __init__(self, formpack, form_versions):
        self.formpack = formpack
        self.versions = form_versions

    def get_stats(self, submissions, fields=(), lang=None):

        versions = self.versions

        all_fields = self.formpack.get_fields_for_versions(versions)
        all_fields = [field for field in all_fields if field.has_stats]

        fields = set(fields)

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
            yield (field.get_labels(lang)[0],
                   field.get_stats(metrics[field.name]))
