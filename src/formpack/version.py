# coding: utf-8

from __future__ import (unicode_literals, print_function, absolute_import,
                        division)


try:
    from cyordereddict import OrderedDict
except ImportError:
    from collections import OrderedDict

from .validators import validate_content

from .constants import UNTRANSLATED, UNSPECIFIED_TRANSLATION
from .submission import FormSubmission
from .utils.xform_tools import formversion_pyxform
from .utils import parse_xml_to_xmljson, normalize_data_type
from .errors import SchemaError
from .utils.flatten_content import flatten_content
from .schema import _field_from_dict
from .schema import (FormField,
                     FormGroup,
                     FormRoot,
                     FormSection,
                     OrOtherField,
                     FormChoice,
                     )
from .schema.tree import (FormTreeRoot,
                          FormTreeRepeat,
                          FormTreeGroup)

from .translated_item import TranslatedItem
from collections import (defaultdict, Counter)
from argparse import Namespace as Ns


def get_labels(choice_definition, translation_list):
    # choices dont need a label if they have an image
    if 'label' in choice_definition:
        _label = choice_definition['label']
    elif 'image' in choice_definition:
        _label = choice_definition['image']
    else:
        _label = None

    if isinstance(_label, basestring):
        _label = [_label]
    elif _label is None and len(translation_list) == 1:
        _label = [None]

    return OrderedDict(zip(translation_list, _label))


def choices_from_structures(definition, translation_list):
    all_choices = {}
    for choice_definition in definition:
        choice_name = choice_definition.get('$autovalue',
                                            choice_definition.get('name'))
        choice_key = choice_definition.get('list_name')
        if not choice_name or not choice_key:
            continue

        if choice_key not in all_choices:
            all_choices[choice_key] = {
                'name': choice_key,
                'options': OrderedDict(),
            }

        all_choices[choice_key]['options'][choice_name] = {
            'labels': get_labels(choice_definition, translation_list),
            'name': choice_name,
        }
    return all_choices.items()


class FieldMapping:
    def __init__(self, _from, _to):
        self._from = _from
        self._to = _to


class ParseContext:
    def __init__(self, _level, parent_context=None):
        self._counter = Counter()
        self._level = _level
        self.index = None
        self.index_chain = []
        if parent_context:
            parent_context._counter[_level] += 1
            self.index = parent_context._counter[_level] - 1
            ptr = parent_context
            self.index_chain = parent_context.index_chain + [self.index]

from pprint import pprint


class SubmittedValue:
    def __init__(self, **kwargs):
        self.category = kwargs.pop('category')
        self.field = kwargs.pop('_cur', None)
        self.kuid = self.field.src.get('$kuid') if self.field else None
        self.value = kwargs.pop('val', None)
        self.ctx = kwargs.pop('context', None)
        self.key = kwargs.pop('key', None)
        self._kw = Ns(**kwargs)

    def __repr__(self):
        if self.field:
            return '<SubmittedValue "{}" {}={}>'.format(self.category, self.field._full_path, self.value)
        else:
            return '<SubmittedValue "{}" {}={}>'.format(self.category, self.key, self.value)

    def append_to(self, submission):
        indeces = self.ctx.index_chain
        submission.append(
                [self.kuid, indeces, self.value, self.field._full_path]
            )

class FormVersion(object):
    @classmethod
    def verify_schema_structure(cls, struct):
        if 'content' not in struct:
            raise SchemaError('version content must have "content"')
        if 'survey' not in struct['content']:
            raise SchemaError('version content must have "survey"')
        validate_content(struct['content'])

    def format_submission(self, json_submission):
        submission = []
        for item in self.format_submission_iterator(json_submission):
            if item.category == 'found':
                item.append_to(submission)
        return submission

    def format_submission_iterator(self, json_submission, **opts):
        paths = {}
        ignore = opts.get('ignore', [])
        field_mapped = opts.get('field_mapped', {})
        caught = {
            '_geolocation': True,
        }
        for field in self.columns(include_groups=True):
            paths[field.path] = field

        def _parse(key, val, context):
            _cur = paths.get(key, False)
            category = None
            _constructor = SubmittedValue
            if key in caught:
                category = 'caught'
            elif key in ignore:
                category = 'ignored'
            elif key in field_mapped:
                _constructor = field_mapped[key]
                category = 'found'
            elif isinstance(val, list):
                for subitem in val:
                    _ccc = ParseContext(_cur, parent_context=context)
                    for (subkey, subval) in subitem.items():
                        for subitem in _parse(subkey, subval, _ccc):
                            yield subitem
            elif _cur:
                category = 'found'
            else:
                category = 'lost'

            if category != 'ignored':
                yield _constructor(category=category,
                                   context=context,
                                   _cur=_cur,
                                   key=key,
                                   val=val,
                                   )

        for (key, val) in json_submission.iteritems():
            for item in _parse(key, val, ParseContext(self)):
                yield item

    def __init__(self, form_pack, schema):
        if 'name' in schema:
            raise ValueError('FormVersion should not have a name parameter. '
                             'consider using "title" or "id_string"')
        self.schema = schema
        self.form_pack = form_pack

        # slug of title
        self.root_node_name = self._get_root_node_name()

        # form version id, unique to this version of the form
        self.id = schema.get('version')
        self.date = schema.get('date_deployed')

        self.version_id_key = schema.get('version_id_key',
                                         form_pack.default_version_id_key)

        # form string id, unique to this form, shared accross versions
        self.id_string = schema.get('id_string')

        # TODO: set the title of the last version as the name of the first
        # section ?
        # Human readable title for this version
        self.title = schema.get('title', form_pack.title)

        # List of available language for translation. One translation does
        # not mean all labels are translated, but at least one.
        # One special translation not listed here is "_default", which
        # use either the only label available, or the field name.
        # This will be converted down the line to a list. We use an OrderedDict
        # to maintain order and remove duplicates, but will need indexing later
        self.translations = OrderedDict()

        # Sections separates fields from various level of nesting in case
        # we have repeat group. If you don't have repeat group, you have
        # only one section, if you have repeat groups, you will have one
        # section per repeat group. Sections eventually become sheets in
        # xls export.
        self.sections = OrderedDict()

        content = self.schema['content']

        self.translations = map(lambda t: t if t is not None else UNTRANSLATED,
                                content.get('translations', [None]))

        # TODO: put those parts in a separate method and unit test it
        survey = content.get('survey', [])

        fields_by_name = dict(map(lambda row:
                                  (row.get('$autoname', row.get('name')),
                                   row,
                                   ),
                                  survey))

        # Analyze the survey schema and extract the informations we need
        # to build the export: the sections, the choices, the fields
        # and translations for each of them.

        # Extract choices data.
        # Choices are the list of values you can choose from to answer a
        # specific question. They can have translatable labels.
        choices_definition = content.get('choices', ())

        field_choices = dict([
            (key, FormChoice(key, options=itm['options']))
            for (key, itm) in choices_from_structures(choices_definition,
                                                      list(self.translations))
        ])

        # Extract fields data
        group = None
        section = FormRoot(name=form_pack.title, src=False)
        _tree = FormTreeRoot(self)
        self._root_section = section
        self.sections[form_pack.title] = section

        # Those will keep track of were we are while traversing the
        # schema.
        # Hierarchy contains all the levels, mixing groups and sections,
        # including the first and last ones while stacks are just an history of
        # previous levels, and for either groups or sections.
        hierarchy = [section]
        group_stack = []
        section_stack = []

        for data_definition in survey:
            data_type = data_definition.get('type')
            if not data_type: # handle broken data type definition
                continue

            data_type = normalize_data_type(data_type)
            if '$autoname' in data_definition:
                data_definition['name'] = data_definition.get('$autoname')
            name = data_definition.get('name')

            # parse closing groups and repeat
            if data_type is None:
                continue

            if data_type == 'end_group':
                # We go up in one level of nesting, so we set the current group
                # to be what used to be the parent group. We also remote one
                # level in the hierarchy.
                hierarchy.pop()
                group = group_stack.pop()
                _tree.pop_group(repeat=False)
                continue

            if data_type == 'end_repeat':
                # We go up in one level of nesting, so we set the current
                # section to be what used to be the parent section
                hierarchy.pop()
                section = section_stack.pop()
                _tree.pop_group(repeat=True)
                continue

            # parse defintinitions of stuff having a name such as fields
            # or opening groups and repeats
            if name is None:
                continue

            if data_type == 'begin_group':
                group_stack.append(group)

                labels = TranslatedItem(data_definition.get('label', []),
                                        translations=self.translations,
                                        )

                group = FormGroup(data_definition['name'], labels,
                                  src=data_definition)
                group.set_parent(hierarchy[-1])
                _tree.push_group(group)
                section._children[group.name] = group

                # We go down in one level on nesting, so save the parent group.
                # Parent maybe None, in that case we are at the top level.
                hierarchy.append(group)
                continue

            if data_type == 'begin_repeat':
                # We go down in one level on nesting, so save the parent section.
                # Parent maybe None, in that case we are at the top level.
                parent_section = section

                labels = TranslatedItem(data_definition.get('label', []),
                                        translations=self.translations,
                                        )
                _repeat_name = data_definition.get('$autoname', data_definition.get('name'))
                section = FormSection(_repeat_name,
                                      labels,
                                      hierarchy=hierarchy,
                                      src=data_definition,
                                      parent=hierarchy[-1],
                                      )

                self.sections[section.name] = section
                parent_section._children[section.name] = section
                hierarchy.append(section)
                _tree.push_group(section, True)
                section_stack.append(parent_section)
                continue

            # If we are here, it's a regular field
            # Get the the data name and type
            field = _field_from_dict(data_definition,
                                     hierarchy, section,
                                     field_choices,
                                     parent=hierarchy[-1],
                                     translations=self.translations)
            _tree.push_field(field)
            section._children[field.name] = field

            _f = fields_by_name[field.name]
            _labels = TranslatedItem()

            if 'label' in _f:
                if not isinstance(_f['label'], list):
                    _f['label'] = [_f['label']]
                _labels = TranslatedItem(_f['label'],
                                         translations=self.translations)

            field.labels = _labels
            assert 'labels' not in _f
        self._tree = _tree

    def __repr__(self):
        return '<FormVersion %s>' % self._stats_str()

    def rows(self, include_groups=False):
        for row in self._root_section.rows:
            yield row

    def columns(self,
                start=None,
                count=None,
                names=None,
                **opts):
        _orother = opts.pop('expand_custom_other_fields', False)
        _split_gps = opts.pop('split_gps', False)
        _split_select_multiple = opts.pop('split_select_multiple', False)

        # allow filtering of gigantic surveys
        if names is not None:
            _gen = self._columns_filtered_by_name(names, **opts)
        elif start is not None:
            _gen = self._columns_filtered_by_index(start, count, **opts)
        else:
            _gen = self._tree.iterfields(**opts)

        for field in _gen:
            if _split_gps and field.type == 'geopoint':
                for subfield in field.split_gps():
                    yield subfield
            if _split_select_multiple and field.type == 'select_multiple':
                for subfield in field.split_select_multiple():
                    yield subfield
            else:
                yield field

            if _orother and field.src.get('_or_other'):
                yield OrOtherField(related_field=field)

    def _columns_filtered_by_name(self, names, **opts):
        for field in self._tree.iterfields(**opts):
            if field.name in names:
                yield field

    def _columns_filtered_by_index(self, start, count, **opts):
        _started = False
        _finished = False
        _start_index = isinstance(start, int)
        if not isinstance(count, int) or count < 1:
            # force count to be a positive int
            count = 1

        for (n, field) in enumerate(self._tree.iterfields(**opts)):
            if _start_index and n >= start:
                # "start" index has been reached
                _started = True
            elif not _start_index and field.name == start:
                # "start" name has been reached"
                _started = True

            if _started and not _finished:
                yield field
                count -= 1
                if count < 1:
                    _finished = True

    def _stats(self):
        _stats = OrderedDict()
        _stats['id_string'] = self._get_id_string()
        _stats['version'] = self.id
        _stats['date'] = self.date
        _stats['row_count'] = len(self.schema.get('content', {}).get('survey', []))
        # returns stats in the format [ key="value" ]
        return _stats

    def _stats_str(self):
        _stats = self._stats()
        return '\n\t'.join(map(lambda key: '%s="%s"' % (key, str(_stats[key])),
                               _stats.keys()))

    def to_dict(self, **opts):
        return flatten_content(self.schema['content'], **opts)

    # TODO: find where to move that
    def _load_submission_xml(self, xml):
        raise NotImplementedError("This doesn't work now that submissions "
                                  "are out of the class. Port it to Export.")
        _xmljson = parse_xml_to_xmljson(xml)
        _rootatts = _xmljson.get('attributes', {})
        _id_string = _rootatts.get('id_string')
        _version_id = _rootatts.get('version')
        if _id_string != self._get_id_string():
            raise ValueError('submission id_string does not match: %s != %s' %
                             (self._get_id_string(), _id_string))
        if _version_id != self.form_pack.id_string:
            raise ValueError('mismatching version id %s != %s' %
                             (self.form_pack.id_string, _version_id))
        self.submissions.append(FormSubmission.from_xml(_xmljson, self))

    def lookup(self, prop, default=None):
        result = getattr(self, prop, None)
        if result is None:
            result = self.form_pack.lookup(prop, default=default)
        return result

    def _get_root_node_name(self):
        return self.lookup('root_node_name', default='data')

    def _get_id_string(self):
        return self.lookup('id_string')

    def _get_title(self):
        '''
        if formversion has no name, uses form's name
        '''
        if self.title is None:
            return self.form_pack.title
        return self.title

    def get_labels(self, lang=UNTRANSLATED, group_sep=None):
        """ Returns a mapping of labels for {section: [field_label, ...]...}

            Sections and fields labels can be set to use their slug name,
            their lone label, or one of the translated labels.

            If a field is part of a group and a group separator is passed,
            the group label is retrieved, possibly translated, and
            prepended to the field label itself.
        """

        all_labels = OrderedDict()
        for section_name, section in self.sections.items():

            section_label = section.labels.get(lang) or section_name
            section_labels = all_labels[section_label] = []

            for field_name, field in section.fields.items():
                    section_labels.extend(field.get_labels(lang, group_sep))

        return all_labels

    def to_xml(self, warnings=None):
        # todo: collect warnings from pyxform compilation when a list is passed
        survey = formversion_pyxform(
            self.to_dict(remove_sheets=['translations', 'translated'],
                         )
                                     )
        title = self._get_title()

        if title is None:
            raise ValueError('cannot create xml on a survey with no title.')

        survey.update({
            'name': self.lookup('root_node_name', 'data'),
            'id_string': self.lookup('id_string'),
            'title': self.lookup('title'),
            'version': self.lookup('id'),
        })
        return survey._to_pretty_xml().encode('utf-8')
