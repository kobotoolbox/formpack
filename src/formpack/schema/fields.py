# coding: utf-8

from __future__ import (unicode_literals, print_function, absolute_import,
                        division)

import re
from operator import itemgetter

try:
    xrange = xrange
except NameError:  # python 3
    xrange = range

try:
    from cyordereddict import OrderedDict
except ImportError:
    from collections import OrderedDict

import statistics

from .datadef import FormDataDef, FormChoice


class FormField(FormDataDef):
    """ A form field definition knowing how to find and format data """

    def __init__(self, name, labels, data_type, hierarchy=None,
                 section=None, can_format=True, has_stats=None,
                 *args, **kwargs):

        self.data_type = data_type
        self.section = section
        self.can_format = can_format

        hierarchy = list(hierarchy) if hierarchy is not None else [None]
        self.hierarchy = hierarchy + [self]

        # warning: the order of the super() call matters
        super(FormField, self).__init__(name, labels, *args, **kwargs)

        if has_stats is not None:
            self.has_stats = has_stats
        else:
            self.has_stats = data_type != "note"

        self.empty_result = self.format('', lang=None)

        # do not include the root section in the path
        self.path = '/'.join(info.name for info in self.hierarchy[1:])

    def get_labels(self, lang=None, group_sep="/",
                   hierarchy_in_labels=False, multiple_select="both"):
        """ Return a list of labels for this field.

            Most fields have only one label, so the list contains only one item,
            but some fields can multiple values, and one label for each
            value.
        """
        args = lang, group_sep, hierarchy_in_labels, multiple_select
        return [self._get_label(*args)]

    # TODO: remove multiple_select ?
    def _get_label(self, lang=None, group_sep='/',
                   hierarchy_in_labels=False, multiple_select="both",
                   _hierarchy_end=None):
        """Return the label for this field

        Args:
            lang (str, optional): Lang to translte the label to if possible.
            group_sep (str, optional): Group to seperate 2 levels of hierarchy
            hierarchy_in_labels (bool, optional):
                Label is the full hierarchy of the field
            multiple_select (str, optional):
                For multiple select, choose the type of display.
            _hierarchy_end (USub, optional):
                By pass to allow the reuse of this method while excluding self
                from the hierarchy.

        Returns:
            str: The label as "label", "Label" or "Parent / Parent / Label"
                 with "/" being the group separator.
        """

        if hierarchy_in_labels:
            path = []
            for level in self.hierarchy[1:_hierarchy_end]:
                path.append(level.labels.get(lang) or level.name)
            return group_sep.join(path)

        return self.labels.get(lang, self.name)

    def __repr__(self):
        args = (self.__class__.__name__, self.name, self.data_type)
        return "<%s name='%s' type='%s'>" % args

    @classmethod
    def from_json_definition(cls, definition, hierarchy=None,
                             section=None, field_choices={}):
        """Return an instance of a Field class matching this JSON field def

        Depending of the data datype extracted from the field definition,
        this method will return an instance of a different class.

        Args:
            definition (dict): Description
            group (FormGroup, optional): The group this field is into
            section (FormSection, optional): The section this field is into
            field_choices (dict, optional):
                A mapping of all the FormChoice instances available for
                this form.

        Returns:
            Union[FormChoiceField, FormChoiceField,
                  FormChoiceFieldWithMultipleSelect, FormField]:
                  The FormField instance matching this definiton.
        """
        name = definition['name']
        labels = cls._extract_json_labels(definition)
        data_type = definition['type']
        choice = None

        # Normalize some common data_type aliases
        data_type = re.sub('^select one', 'select_one', data_type)
        data_type = re.sub('^select multiple', 'select_multiple', data_type)
        data_type = re.sub('^location$', 'geopoint', data_type)

        # Get the data type. If it has a foreign key, instanciate a subclass
        # dedicated to handle choices and pass it the choices matching this fk
        if " " in data_type:
            data_type, choice_id = data_type.split(' ')[:2]  # ignore deprecated 'or_other' value
            choice = field_choices[choice_id]

        data_type_classes = {
            "select_one": FormChoiceField,
            "select_multiple": FormChoiceFieldWithMultipleSelect,
            "geopoint": FormGPSField,
            "date": DateField,
            "text": TextField,
            "barcode": TextField,
            # calculate is usually not text but for our purpose it's good
            # enough
            "calculate": TextField,
            "acknowledge": TextField,
            "integer": NumField,
            'decimal': NumField
        }

        args = {
            'name': name,
            'labels': labels,
            'data_type': data_type,
            'hierarchy': hierarchy,
            'section': section,
            'choice': choice
        }
        return data_type_classes.get(data_type, cls)(**args)

    def format(self, val, lang=None, context=None):
        return {self.name: val}

    def get_stats(self, metrics, lang=None, limit=100):

        not_provided = metrics.pop(None, 0)
        provided = metrics.pop('__submissions__', 0)

        return {
            'total_count': not_provided + provided,
            'not_provided': not_provided,
            'provided': provided,
            'show_graph': False
        }

    def parse_values(self, raw_values):
        yield raw_values


class TextField(FormField):

    def get_stats(self, metrics, lang=None, limit=100):

        stats = super(TextField, self).get_stats(metrics, lang, limit)

        top = metrics.most_common(limit)
        total = stats['total_count']
        percentage = [(key, "%.2f" % (val * 100 / total)) for key, val in top]

        stats.update({
            'frequency': top,
            'percentage': percentage,
        })

        return stats


class DateField(FormField):
    def get_stats(self, metrics, lang=None, limit=100):
        """ Return total count for all, and freq and % for 'date' date types

            Dates are sorted from old to new.
        """

        stats = super(DateField, self).get_stats(metrics, lang, limit)

        if self.data_type != "date":
            return stats

        top = sorted(metrics.items(), key=itemgetter(0))[:limit]
        total = stats['total_count']
        percentage = [(key, "%.2f" % (val * 100 / total)) for key, val in top]

        stats.update({
            'frequency': top,
            'percentage': percentage,
            'show_graph': True
        })

        return stats



class NumField(FormField):

    def flatten_dataset(self, dataset):
        """ Generate sorted numbers as listed in the given metrics counter

            Cast the value to the propoer datatype in caste it's been provided
            as text.

        """
        for value, freq in sorted(dataset.items()):
            for x in xrange(freq):
                yield value

    def get_stats(self, metrics, lang=None, limit=100):

        stats = super(NumField, self).get_stats(metrics, lang, limit)

        stats.update({
            'median': '<N/A>',
            'mean': '<N/A>',
            'mode': '<N/A>',
            'stdev': '<N/A>'
        })

        try:
            # require a non empty dataset
            stats['mean'] = statistics.mean(self.flatten_dataset(metrics))
            stats['median'] = statistics.median(self.flatten_dataset(metrics))
            # requires at least 2 values in the dataset
            stats['stdev'] = statistics.stdev(self.flatten_dataset(metrics),
                                              xbar=stats['mean'])
            # requires a non empty dataset and a unique mode
            stats['mode'] = statistics.mode(self.flatten_dataset(metrics))
        except statistics.StatisticsError:
            pass

        return stats

    def parse_values(self, raw_values):
        if self.data_type == "integer":
            yield int(raw_values)
        else:
            yield float(raw_values)


class CopyField(FormField):
    """ Just copy the data over. No translation. No manipulation """
    def __init__(self, name, hierarchy=(None,), section=None, *args, **kwargs):
        super(CopyField, self).__init__(name, labels=None,
                                        data_type=name,
                                        hierarchy=(None,),
                                        section=section,
                                        can_format=True,
                                        has_stats=False,
                                        *args, **kwargs)

    def get_labels(self, *args, **kwargs):
        """ Labels are the just the value name. Groups are ignored """
        return [self.name]


class FormGPSField(FormField):

    def __init__(self, name, labels, data_type, hierarchy=None,
                 section=None, choice=None, *args, **kwargs):
        super(FormGPSField, self).__init__(name, labels, data_type,
                                           hierarchy, section, *args, **kwargs)

    def get_labels(self, lang=None, group_sep='/',
                   hierarchy_in_labels=False, multiple_select="both"):
        """Return a list of labels for this field.

        Most fields have only one label, so the list contains only one item,
        but some fields can multiple values, and one label for each
        value.

        """

        label = self._get_label(lang, group_sep, hierarchy_in_labels=False)

        labels = [label]

        components = {'suffix': label}
        pattern = '_{suffix}_{data_type}'

        prefix = self._get_label(lang, group_sep, hierarchy_in_labels,
                                 _hierarchy_end=-1)

        if hierarchy_in_labels and prefix:
            components['group_sep'] = group_sep
            components['prefix'] = prefix
            pattern = '{prefix}{group_sep}' + pattern

        for data_type in ('latitude', 'longitude', 'altitude', 'precision'):
            label = pattern.format(data_type=data_type, **components)
            labels.append(label)

        return labels

    def get_value_names(self, multiple_select="both"):
        """ Return the list of field identifiers used by this field"""
        names = []
        names.append(self.name)

        for data_type in ('latitude', 'longitude', 'altitude', 'precision'):
            names.append('_%s_%s' % (self.name, data_type))

        return names

    def format(self, val, lang=None, *args, **kwargs):
        """Same than other format(), but dealing with 2 to 4 values

        The GPS value can contain 2, 3 or 4 numerical separated by a
        spaces: latitude, longitude altitude (optional) precision (optional)

        If a value is not present, we set it to an empty string since
        the column will be in the final export anyway.


        Args:
          val (str): The value from the submission.
          lang (str, optional): Not used. Part of the parent API.
          group_sep (str, optional): Not used. Part of the parent API.
          hierarchy_in_labels (bool, optional): Not used. Part of the parent API.
          multiple_select (str, optional): Not used. Part of the parent API.

        Returns:
          dict: The 4 values as {'_name_': raw initial value,
                                 '_name_latitude': latitude,
                                 etc.}

        """

        values = [val, "", "", "", ""]
        for i, value in enumerate(val.split(), 1):
            values[i] = value

        return dict(zip(self.value_names, values))


class FormChoiceField(FormField):
    """  Same as FormField, but link the data to a FormChoice """

    def __init__(self, name, labels, data_type, hierarchy=None,
                 section=None, choice=None, *args, **kwargs):
        self.choice = choice or FormChoice(name)
        super(FormChoiceField, self).__init__(name, labels, data_type,
                                              hierarchy, section,
                                              *args, **kwargs)

    def get_translation(self, val, lang=None):
        try:
            return self.choice.options[val]['labels'][lang]
        except KeyError:
            return val

    def format(self, val, lang=None, multiple_select="both"):
        if lang:
            val = self.get_translation(val, lang)
        return {self.name: val}

    def get_stats(self, metrics, lang=None, limit=100):

        stats = super(FormChoiceField, self).get_stats(metrics, lang, limit)
        total = stats['total_count']

        top = metrics.most_common(limit)
        top = [(self.get_translation(val, lang), freq) for val, freq in top]

        percentage = []
        for val, freq in top:
            freq = "%.2f" % (freq * 100 / total)
            percentage.append((val, freq))

        stats.update({
            'frequency': top,
            'percentage': percentage,
            'show_graph': True
        })

        return stats


class FormChoiceFieldWithMultipleSelect(FormChoiceField):
    """  Same as FormChoiceField, but you can select several answer """

    def __init__(self, *args, **kwargs):
        super(FormChoiceFieldWithMultipleSelect, self).__init__(*args, **kwargs)
        # reset empty result so it doesn't contain '0'
        self.empty_result = dict.fromkeys(self.empty_result, '')

    def _get_option_label(self, lang=None, group_sep='/',
                          hierarchy_in_labels=False, option=None):
        """ Return the label for this field and this option in particular """

        label = self._get_label(lang, group_sep, hierarchy_in_labels)
        option_label = option['labels'].get(lang, option['name'])
        group_sep = group_sep or "/"
        return label + group_sep + option_label

    def get_labels(self, lang=None, group_sep='/',
                   hierarchy_in_labels=False, multiple_select="both"):
        """ Return a list of labels for this field.

            Most fields have only one label, so the list contains only one item,
            but some fields can multiple values, and one label for each
            value.
        """
        labels = []
        if multiple_select in ("both", "summary"):
            labels.append(self._get_label(lang, group_sep, hierarchy_in_labels))

        if multiple_select in ("both", "details"):
            for option in self.choice.options.values():
                args = (lang, group_sep, hierarchy_in_labels, option)
                labels.append(self._get_option_label(*args))

        return labels

    def get_value_names(self, multiple_select="both"):
        """ Return the list of field identifiers used by this field"""
        names = []
        if multiple_select in ("both", "summary"):
            names.append(self.name)

        if multiple_select in ("both", "details"):
            for option_name in self.choice.options.keys():
                names.append(self.name + '/' + option_name)
        return names

    def __repr__(self):
        data = (self.name, self.data_type)
        return "<FormChoiceFieldWithMultipleSelect name='%s' type='%s'>" % data

    # maybe try to cache those
    def format(self, val, lang=None,
               group_sep="/", hierarchy_in_labels=False,
               multiple_select="both"):
        """ Same than other format(), with an option for multiple_select layout

                multiple_select:
                "both": add the summary column and a colum for each value
                "summary": only the summary column
                "details": only the details column
        """
        cells = dict.fromkeys(self.value_names, "0")
        if multiple_select in ("both", "summary"):
            res = []
            for v in val.split():
                try:
                    res.append(self.choice.options[v]['labels'][lang])
                except:
                    res.append(v)
            cells[self.name] = " ".join(res)

        if multiple_select in ("both", "details"):
            for choice in val.split():
                cells[self.name + "/" + choice] = "1"
        return cells

    def parse_values(self, raw_values):
        for x in raw_values.split():
            yield x
