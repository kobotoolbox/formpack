# coding: utf-8
from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

import json
from copy import deepcopy

from .version import FormVersion
from .utils import str_types
from .reporting import Export, AutoReport
from .utils.future import OrderedDict
from .constants import UNSPECIFIED_TRANSLATION
from formpack.schema.fields import CopyField

from .content import Content, kfrozendict


class FormPack(object):

    def __init__(self,
                 versions=None,
                 title=None,
                 default_version_id_key='__version__',
                 strict_schema=False,
                 asset_type=None,
                 validate=True,
                 submissions_xml=None):
        """


        :param versions: list. Versions of the asset. It must be sorted in ascending order. From oldest to newest.
        :param title: string. The human readable name of the form.
        :param id_string: The human readable id of the form.
        :param default_version_id_key: string. The name of the field in submissions which stores the version ID
        """
        if title is not None:
            raise ValueError("title must be set in form's settings.title")
        # accept a single version, but normalize it to an iterable
        if isinstance(versions, (dict, kfrozendict)):
            versions = [versions]

        self.versions = OrderedDict()

        # the name of the field in submissions which stores the version ID
        self.default_version_id_key = default_version_id_key

        self.validate = validate

        self.id_string = None
        self.title = None
        self.identifier = None
        self.strict_schema = strict_schema

        self.asset_type = asset_type

        self.load_all_versions(versions)

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

    def load_all_versions(self, versions):
        # a hack to ensure single-version forms still validate
        if len(versions) == 1 and 'version' not in versions[0]['settings']:
            versions[0]['settings']['version'] = ''

        for schema in versions:
            self.load_version(deepcopy(schema))
        self.set_properties()

    def set_properties(self):
        settings_ids = []
        titles = []
        version_ids = []
        for version in self.versions.values():
            if version.id in version_ids:
                raise ValueError('cannot have duplicate version id: %s'
                                 % version.id)
            version_ids.append(version.id)
            if version.settings_identifier not in settings_ids:
                settings_ids.append(version.settings_identifier)
            if version.title and version.title not in titles:
                titles.append(version.title)

        if len(version_ids) > 1 and None in version_ids:
            raise ValueError('cannot have two versions without '
                             'a "version" id specified')
        self.title = titles[-1] if len(titles) > 0 else 'Submissions'
        self.id_string = settings_ids[-1]

    @property
    def available_translations(self):
        return [tt['name'] for tt in self[-1].content['translations']]

    def load_version(self, content):
        """ Load one version and attach it to this Formpack

            All the metadata parsing is delegated to the FormVersion class

            Each version can be distinguish by its version_id, which is
            unique accross an entire FormPack. It can be None, but only for
            a FormPack with just one version.
        """
        if 'content' in content:
            # the "versions" parameter no longer wraps the survey object in
            # an extra object with a property "content"
            raise ArgumentError('Discontinued parameter structure: "content"')
        _content_structure = Content(content, validate=self.validate)
        validated_content = _content_structure.export(schema='2',
                                                      flat=False,
                                                      remove_nulls=False)
        form_version = FormVersion(self, validated_content)
        self.versions[form_version.id] = form_version

    @staticmethod
    def _combine_field_choices(old_field, new_field):
        """
        Update `new_field.choice` so that it contains everything from
        `old_field.choice`. In the event of a conflict, `new_field.choice`
        wins. If either field does not have a `choice` attribute, do
        nothing

        :param old_field: FormField
        :param new_field: FormField
        :return: FormField. Updated new_field
        """
        try:
            old_choice = old_field.choice
            new_choice = new_field.choice
            new_field.merge_choice(old_choice)
        except AttributeError:
            pass

        return new_field

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

        # if data_types is not None:
        #     if isinstance(data_types, str_types):
        #         data_types = [data_types]

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
                        if field_name in positions:
                            position = positions[field_name]
                            latest_field_object = tmp2d[position[0]][position[1]]
                            # Because versions_desc are ordered from latest to oldest,
                            # we use current field object as the old one and the one already
                            # in position as the latest one.
                            new_object = self._combine_field_choices(
                                field_object, latest_field_object)
                            tmp2d[position[0]][position[1]] = new_object
                        else:
                            try:
                                current_index_list = tmp2d[index]
                                current_index_list.append(field_object)
                            except IndexError:
                                tmp2d.append([field_object])
                                # set index with upper bound of the tmp2d list
                                # in case index is greater than it.
                                # it can happen when current version has more items than newest one.
                                index = len(tmp2d) - 1

                            positions[field_name] = (index, len(tmp2d[index]) - 1)

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

    def to_version_list(self):
        return [
            vv.to_dict()
            for vv in self.versions.values()
        ]


    def to_dict(self, **kwargs):
        out = {
            'versions': [v.to_dict() for v in self.versions.values()],
        }
        if self.title is not None:
            out['title'] = self.title
        if self.id_string is not None:
            out['id_string'] = self.id_string
        if self.asset_type is not None:
            out['asset_type'] = self.asset_type
        return out

    def export(self, lang=UNSPECIFIED_TRANSLATION, group_sep='/', hierarchy_in_labels=False,
               versions=-1, multiple_select="both",
               force_index=False, copy_fields=(), title=None,
               tag_cols_for_header=None):
        """
        Create an export for given versions of the form
        """
        versions = self._get_versions(versions)
        title = title or self.title
        return Export(self, versions, lang=lang, group_sep=group_sep,
                      hierarchy_in_labels=hierarchy_in_labels,
                      version_id_keys=self.version_id_keys(versions),
                      title=title, multiple_select=multiple_select,
                      force_index=force_index, copy_fields=copy_fields,
                      tag_cols_for_header=tag_cols_for_header)

    def autoreport(self, versions=-1):
        """
        Create an automatic report for given versions of the form
        """
        return AutoReport(self, self._get_versions(versions))

    def _get_versions(self, versions):

        if versions is None:
            versions = -1

        if isinstance(versions, str_types + (int,)):
            versions = [versions]
        versions = [self[key] for key in versions]

        return OrderedDict((v.id, v) for v in versions)
