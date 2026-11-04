# coding: utf-8
from collections import OrderedDict
from operator import is_

from ..constants import UNSPECIFIED_TRANSLATION, UNTRANSLATED


class FormDataDef:
    """
    Any object composing a form. It's only used with a subclass.
    """

    def __init__(self, name, labels=None, has_stats=False, *args, **kwargs):
        self.name = name
        self.labels = labels or {}
        self.has_stats = has_stats

    def __repr__(self):
        return "<%s name='%s'>" % (self.__class__.__name__, self.name)

    def get_value_names(self):
        return [self.name]

    @classmethod
    def from_json_definition(cls, definition, translations=None):
        labels = cls._extract_json_labels(definition, translations)
        return cls(definition['name'], labels)

    @classmethod
    def _extract_json_labels(cls, definition, translations):
        """
        Extract translation labels from the JSON data definition
        """
        label = definition.get('label')
        if label:
            labels = OrderedDict(zip(translations, label))
        else:
            labels = {}
        return labels


class FormGroup(FormDataDef):  # useful to get __repr__
    pass


class FormSection(FormDataDef):
    """
    The tabular representation of a repeatable group of fields
    """

    def __init__(
        self,
        name='submissions',
        labels=None,
        fields=None,
        parent=None,
        children=(),
        hierarchy=(None,),
        *args,
        **kwargs
    ):

        if labels is None:
            labels = {UNTRANSLATED: 'submissions'}

        super().__init__(name, labels, *args, **kwargs)
        self.fields = fields or OrderedDict()
        self.parent = parent
        self.children = list(children)

        self.hierarchy = list(hierarchy) + [self]
        # do not include the root section in the path
        self.path = '/'.join(info.name for info in self.hierarchy[1:])

    @classmethod
    def from_json_definition(
        cls, definition, hierarchy=(None,), parent=None, translations=None
    ):
        labels = cls._extract_json_labels(definition, translations)
        return cls(
            definition['name'], labels, hierarchy=hierarchy, parent=parent
        )

    def get_label(self, lang=UNSPECIFIED_TRANSLATION):
        return [self.labels.get(lang) or self.name]

    def __repr__(self):
        parent_name = getattr(self.parent, 'name', None)
        return "<FormSection name='%s' parent='%s'>" % (self.name, parent_name)


class SharedChoiceOptions:
    """
    Keep one copy of each distinct choice and of each distinct list of choices
    across the versions of a form.

    A form can hold tens of thousands of choices, and its versions mostly
    repeat them. Sharing relies on nothing writing to an option or to a list
    after creating it: `merge_choice()` assigns a new list instead of updating
    the current one.
    """

    def __init__(self):
        self._options = {}
        self._latest_lists = {}

    def get_option(self, name, labels, translations):
        """
        Return the option for these values, which a previous version may have
        created already.

        Only text and empty values are shared, because Python treats `1`, `1.0`
        and `True` as equal, while an export shows them differently.
        """

        if not self._can_share(name, labels):
            return self._build_option(name, labels, translations)

        key = (name, translations, tuple(labels))
        option = self._options.get(key)
        if option is None:
            option = self._build_option(name, labels, translations)
            self._options[key] = option
        return option

    def get_list(self, list_name, options):
        """
        Return the previous version's options for this list when they are the
        same objects in the same order, so that one list stays in memory.
        """

        latest = self._latest_lists.get(list_name)
        # `is_` rather than `==`, because `1 == 1.0` would merge two options
        # that an export shows differently. `get_option()` already returns the
        # same object for the same values
        if (
            latest is not None
            and len(latest) == len(options)
            and all(map(is_, latest.values(), options.values()))
        ):
            return latest

        self._latest_lists[list_name] = options
        return options

    @staticmethod
    def _build_option(name, labels, translations):
        return {
            'labels': OrderedDict(zip(translations, labels)),
            'name': name,
        }

    @staticmethod
    def _can_share(name, labels):
        return (
            isinstance(name, str)
            and isinstance(labels, list)
            and all(label is None or isinstance(label, str) for label in labels)
        )


class FormChoice(FormDataDef):
    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)
        self.name = name
        self.options = OrderedDict()

    @classmethod
    def all_from_json_definition(
        cls, definition, translation_list, shared_options=None
    ):
        if shared_options is None:
            shared_options = SharedChoiceOptions()
        translations = tuple(translation_list)

        all_choices = {}
        for choice_definition in definition:
            choice_name = choice_definition.get('name')
            choice_key = choice_definition.get('list_name')
            if not choice_name or not choice_key:
                continue

            if choice_key not in all_choices:
                all_choices[choice_key] = FormChoice(choice_key)
            choices = all_choices[choice_key]

            # apparently choices dont need a label if they have an image
            if 'label' in choice_definition:
                _label = choice_definition['label']
            else:
                _label = choice_definition.get('image')
            if isinstance(_label, str):
                _label = [_label]
            elif _label is None:
                _label = []
            choices.options[choice_name] = shared_options.get_option(
                choice_name, _label, translations
            )

        # A list that holds the same options as in the previous version reuses
        # that list, so that only one copy of it stays in memory
        for choices in all_choices.values():
            choices.options = shared_options.get_list(
                choices.name, choices.options
            )
        return all_choices

    @property
    def translations(self):
        for option in self.options.values():
            for translation in option['labels'].keys():
                yield translation
