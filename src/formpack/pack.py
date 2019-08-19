# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

import json
import difflib
from copy import deepcopy

try:
    from cyordereddict import OrderedDict
except ImportError:
    from collections import OrderedDict

from .version import FormVersion
from .utils import get_version_identifiers, str_types
from .reporting import Export, AutoReport
from .utils.expand_content import expand_content
from .utils.replace_aliases import replace_aliases
from .constants import UNSPECIFIED_TRANSLATION
from formpack.schema.fields import CopyField


class FormPack(object):

    def __init__(self, versions=None, title='Submissions', id_string=None,
                 default_version_id_key='__version__',
                 strict_schema=False,
                 root_node_name='data',
                 asset_type=None, submissions_xml=None):
        """


        :param versions: list. Versions of the asset. It must be sorted in ascending order. From oldest to newest.
        :param title: string. The human readable name of the form.
        :param id_string: The human readable id of the form.
        :param default_version_id_key: string. The name of the field in submissions which stores the version ID
        """
        # @TODO: Complete the signature for __init__

        if not versions:
            versions = []

        # accept a single version, but normalize it to an iterable
        if isinstance(versions, dict):
            versions = [versions]

        self.versions = OrderedDict()

        # the name of the field in submissions which stores the version ID
        self.default_version_id_key = default_version_id_key

        self.id_string = id_string
        self.root_node_name = root_node_name

        self.title = title
        self.strict_schema = strict_schema

        self.asset_type = asset_type

        self.load_all_versions(versions)

    # FIXME: Find a safe way to use this. Wrapping with try/except isn't enough
    # to fix https://github.com/kobotoolbox/formpack/issues/150
    #
    #def __repr__(self):
    #    return '<FormPack %s>' % self._stats()

    def version_id_keys(self, _versions=None):
        # if no parameter is passed, default to 'all'
        if _versions is None:
            _versions = self.versions
        _id_keys = []
        for version in self.versions.values():
            _id_key = version.version_id_key
            if _id_key not in _id_keys:
                _id_keys.append(_id_key)
        return _id_keys

    @property
    def available_translations(self):
        translations = set()
        for version in self.versions.values():
            translations.update(version.translations)
        return translations

    def lookup(self, prop, default=None):
        # can't use a one liner because sometimes self.prop is None
        result = getattr(self, prop, default)
        if result is None:
            return default
        return result

    def __getitem__(self, index):
        try:
            if isinstance(index, int):
                return tuple(self.versions.values())[index]
            else:
                return self.versions[index]
        except KeyError:
            raise KeyError('formpack with version [%s] not found' % str(index))
        except IndexError:
            raise IndexError('version at index %d is not available' % index)

    def _stats(self):
        _stats = OrderedDict()
        _stats['id_string'] = self.id_string
        _stats['versions'] = len(self.versions)
        # _stats['submissions'] = self.submissions_count()
        if self.versions:
            _stats['row_count'] = len(self[-1].schema.get('content', {})
                                                     .get('survey', []))
        # returns stats in the format [ key="value" ]
        return '\n\t'.join('%s="%s"' % item for item in _stats.items())

    def load_all_versions(self, versions):
        for schema in versions:
            self.load_version(deepcopy(schema))

    def load_version(self, schema):
        """ Load one version and attach it to this Formpack

            All the metadata parsing is delegated to the FormVersion class,
            hence several attributes for FormPack are populated on the fly
            while getting versions loaded:

                - title : the human readable name of the form. Match the one
                          from the most recent version.
                - id_string : the human readable id of the form. The same for
                              all versions of the same FormPack.

            Each version can be distinguish by its version_id, which is
            unique accross an entire FormPack. It can be None, but only for
            one version in the FormPack.
        """
        replace_aliases(schema['content'], in_place=True)
        expand_content(schema['content'], in_place=True)

        if self.strict_schema:
            FormVersion.verify_schema_structure(schema)

        form_version = FormVersion(self, schema)

        # NB: id_string are readable string unique to the form
        # while version id are id unique to one of the versions of the form

        # Avoid duplicate versions id
        if form_version.id in self.versions:
            if form_version.id is None:
                raise ValueError('cannot have two versions without '
                                 'a "version" id specified')

            raise ValueError('cannot have duplicate version id: %s'
                             % form_version.id)

        # If the form pack doesn't have an id_string, we get it from the
        # first form version. We also avoid heterogenenous id_string in versions
        if form_version.id_string:
            if self.id_string and self.id_string != form_version.id_string:
                raise ValueError('Versions must of the same form must '
                                 'share an id_string: %s != %s' % (
                                    self.id_string, form_version.id_string,
                                 ))

            self.id_string = form_version.id_string

        # If the form pack doesn't have an title, we get it from the
        # first form version.
        if form_version.title and not self.title:
            self.title = form_version.version_title

        self.versions[form_version.id] = form_version

    def version_diff(self, vn1, vn2):
        v1 = self.versions[vn1]
        v2 = self.versions[vn2]

        def summr(v):
            return json.dumps(v.schema.get('content'),
                              indent=4,
                              sort_keys=True,
                              ).splitlines(1)
        out = []
        for line in difflib.unified_diff(summr(v1),
                                         summr(v2),
                                         fromfile=vn1,
                                         tofile=vn2,
                                         n=1):
            out.append(line)
        return ''.join(out)

    @staticmethod
    def _combine_field_choices(older_version_field, current_field):
        """
        Updates `current_field.choice` so that it contains everything from
        `older_version_field.choice`. In the event of a conflict, `current_field.choice`
        wins. If either field does not have a `choice` attribute, do
        nothing

        :param older_version_field: FormField
        :param current_field: FormField
        :return: FormField. Updated new_field
        """

        try:
            older_version_choice = older_version_field.choice
            current_field.merge_choice(older_version_choice)
        except AttributeError:
            pass

        return current_field

    @staticmethod
    def _do_fields_match(older_versioned_field, current_field):
        return older_versioned_field.signature == current_field.signature

    def get_fields_for_versions(self, versions=-1, data_types=None):

        """
            Return a mapping containing fields

            This is needed because when making an report for several
            versions of the same form, fields get added, removed, and
            edited. Hence we pre-generate mappings containing fields
             for all versions so we can use them later as a
            canvas to keep the export coherent.

            Labels are used as column headers.

        :param versions: list
        :param data_types: list
        :return: list
        """
        # Cast data_types if it's not already a list
        if data_types is not None:
            if isinstance(data_types, str_types):
                data_types = [data_types]

        # tmp2 is a 2 dimensions list of `field`.
        # First dimension is the position of fields where they should be in the latest version
        # Second dimension is their position in the stack at the same position.
        # For example:
        #      ```
        #      latest_version = [field1, field3]
        #      version_just_before = [field2, field3]
        #      ```
        #
        # Index 0 of tmp2d will be `[field1, field2]`
        tmp2d = []
        # This dict is used to remember final position of each field.
        # Its keys are field_names and values are tuples of coordinates in tmp2d
        # Keeping example above:
        #       `positions[field1.name]` would be `(0, 0)`
        #       `positions[field2.name]` would be `(0, 1)`
        positions = {}

        # Create the initial field mappings from the first form version
        versions_desc = list(reversed(self._get_versions(versions).values()))

        # Copy fields need to be pushed at the end. So let's process them separately.
        copy_fields = []
        index = 0
        for section in versions_desc[0].sections.values():
            for field_name, field_object in section.fields.items():
                if isinstance(field_object, CopyField):
                    copy_fields.append(field_object)
                else:
                    positions[field_name] = (index, 0)
                    tmp2d.append([field_object])
                    index += 1

        for version in versions_desc[1:]:
            index = 0
            for section_name, section in version.sections.items():
                for field_name, field_object in section.fields.items():
                    if not isinstance(field_object, CopyField):
                        add_field = True
                        if field_name in positions:
                            position = positions[field_name]
                            latest_field_object = tmp2d[position[0]][position[1]]
                            # Because versions_desc are ordered from latest to oldest,
                            # we use current field object as the old one and the one already
                            # in position as the latest one.

                            if self._do_fields_match(field_object, latest_field_object):
                                new_object = self._combine_field_choices(
                                    field_object, latest_field_object)
                                tmp2d[position[0]][position[1]] = new_object
                                add_field = False
                            else:
                                field_object.use_unique_name = True

                        if add_field:
                            try:
                                current_index_list = tmp2d[index]
                                current_index_list.append(field_object)
                            except IndexError:
                                tmp2d.append([field_object])
                                # set index with upper bound of the tmp2d list
                                # in case index is greater than it.
                                # it can happen when current version has more items than newest one.
                                index = len(tmp2d) - 1

                            positions[field_object.contextual_name] = (index, len(tmp2d[index]) - 1)

                        index += 1

        all_fields = []

        # We need to flatten the 2d list before returning it.
        # First, we want to show existing fields (index 0 of each dimension)
        for first_dimension in tmp2d:
            field = first_dimension[0]
            if data_types:
                if field.data_type in data_types:
                    all_fields.append(field)
                    first_dimension.pop(0)
            else:
                all_fields.append(field)
                first_dimension.pop(0)

        # Then flatten tmp2d
        for first_dimension in tmp2d:
            for field in first_dimension:
                if data_types:
                    if field.data_type in data_types:
                        all_fields.append(field)
                else:
                    all_fields.append(field)

        # Finally, add copy fields at the end
        all_fields += copy_fields

        return all_fields

    def to_dict(self, **kwargs):
        out = {
            u'versions': [v.to_dict() for v in self.versions.values()],
        }
        if self.title is not None:
            out[u'title'] = self.title
        if self.id_string is not None:
            out[u'id_string'] = self.id_string
        if self.asset_type is not None:
            out[u'asset_type'] = self.asset_type
        return out

    def to_json(self, **kwargs):
        return json.dumps(self.to_dict(), **kwargs)

    def export(self, lang=UNSPECIFIED_TRANSLATION, group_sep='/', hierarchy_in_labels=False,
               versions=-1, multiple_select="both",
               force_index=False, copy_fields=(), title=None,
               tag_cols_for_header=None):
        '''Create an export for a given versions of the form'''

        versions = self._get_versions(versions)
        title = title or self.title
        return Export(self, versions, lang=lang, group_sep=group_sep,
                      hierarchy_in_labels=hierarchy_in_labels,
                      version_id_keys=self.version_id_keys(versions),
                      title=title, multiple_select=multiple_select,
                      force_index=force_index, copy_fields=copy_fields,
                      tag_cols_for_header=tag_cols_for_header)

    def autoreport(self, versions=-1):
        '''Create an automatic report for a given versions of the form'''
        return AutoReport(self, self._get_versions(versions))

    def _get_versions(self, versions):

        if versions is None:
            versions = -1

        if isinstance(versions, str_types + (int,)):
            versions = [versions]
        versions = [self[key] for key in versions]

        return OrderedDict((v.id, v) for v in versions)
