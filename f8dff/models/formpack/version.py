# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

from collections import OrderedDict

from .utils import formversion_pyxform

# QUESTION FOR ALEX:
# should we turn that into relative imports ? Such as:
# from .models.formpack.submission import FormSubmission
# from .models.formpack.utils import parse_xml_to_xmljson
# Since d8dff will probably be renammed, this make it easy to merge it
from f8dff.models.formpack.submission import FormSubmission
from f8dff.models.formpack.utils import parse_xml_to_xmljson


# TODO: move submission, pack.py and version.py into a forms module with
#       __init__ their content
# TODO: put formatters in their own module

class FormVersion:
    def __init__(self, version_data, parent):
        if 'name' in version_data:
            raise ValueError('FormVersion should not have a name parameter. '
                             'consider using "title" or "id_string"')
        # TODO: # rename _v to something meaningful
        self._v = version_data
        self._parent = parent
        self._names = []
        self._root_node_name = version_data.get('root_node_name')
        self.version_title = version_data.get('title')
        self._submissions = []
        self.id_string = version_data.get('id_string')
        self.version_id = version_data.get('version')
        # This will be converted down the line to a list. We use an OrderedDict
        # to maintain order and remove duplicates, but will need indexing later.
        self.translations = OrderedDict()

        self.schema = OrderedDict()

        content = self._v.get('content', {})

        # TODO: put that part in a separate method
        survey = content.get('survey', [])

        # Analize the survey schema and extract the informations we need
        # to build the export
        for data_definition in survey:

            # Get the the data name and type
            if 'name' in data_definition:
                name = data_definition['name']
                self._names.append(name)

                field = self.schema[name] = {
                    "type": data_definition['type']
                }

                # Get the labels and associated languages for this data
                labels = field['labels'] = {'default': name}
                if "label" in data_definition:
                    labels['default'] = data_definition['label']
                else:
                    for key, val in data_definition.items():
                        if key.startswith('label::'):
                            _, lang = key.split('::')
                            labels[lang] = val
                            self.translations[lang] = None

        # Convert it back to a list to get numerical indexing
        self.translations = list(self.translations)

        self._formatters = OrderedDict()

        for name, structure in self.schema.items():
            # question_type = get_question_type(name, version)
            # formater_class = formater_registry[question_type]
            self._formatters[name] = Formatter(name, structure['type'])

        for submission in version_data.get('submissions', []):
            self.load_submission(submission)

    def __repr__(self):
        return '<FormVersion %s>' % self._stats()

    def _stats(self):
        _stats = OrderedDict()
        _stats['id_string'] = self._get_id_string()
        _stats['version'] = '' if not self.version_id else self.version_id
        _stats['row_count'] = len(self._v.get('content', {})
                                         .get('survey', []))
        _stats['submission_count'] = len(self._submissions)
        # returns stats in the format [ key="value" ]
        return '\n\t'.join(map(lambda key: '%s="%s"' % (
                            key, str(_stats[key])), _stats.keys()))

    def to_dict(self):
        _ss = []
        for _s in self._submissions:
            _ss.append(_s.to_dict())
        out = {}
        out.update(self._v)
        out[u'submissions'] = _ss
        return out

    def load_submission(self, v):
        self._submissions.append(FormSubmission(v, self))

    def _load_submission_xml(self, xml):
        _xmljson = parse_xml_to_xmljson(xml)
        _rootatts = _xmljson.get('attributes', {})
        _id_string = _rootatts.get('id_string')
        _version_id = _rootatts.get('version')
        if _id_string != self._get_id_string():
            raise ValueError('submission id_string does not match: %s != %s' %
                             (self._get_id_string(), _id_string))
        if _version_id != self.version_id:
            raise ValueError('mismatching version id %s != %s' %
                             (self.version_id, _version_id))
        self._submissions.append(FormSubmission.from_xml(_xmljson, self))

    def _submissions_count(self):
        return len(self._submissions)

    def lookup(self, prop, default=None):
        result = getattr(self, prop, None)
        if result is None:
            result = self._parent.lookup(prop, default=default)
        return result

    def _get_root_node_name(self):
        return self.lookup('root_node_name', default='data')

    def _get_id_string(self):
        return self.lookup('id_string')

    def _get_title(self):
        '''
        if formversion has no name, uses form's name
        '''
        if self.version_title is None:
            return self._parent.title
        return self.version_title

    def submit(self, *args, **kwargs):
        self.load_submission(kwargs)

    def get_colum_names_for_lang(self, lang="default"):
        for field, infos in self.schema.items():
            yield field, infos['labels'].get(lang)

    def to_xml(self):
        survey = formversion_pyxform(self._v)

        title = self._get_title()

        if title is None:
            raise ValueError('cannot create xml on a survey '
                             'with no title.')
        survey.update({
                'name': self.lookup('root_node_name', 'data'),
                'id_string': self.lookup('id_string'),
                'title': title,
                'version': self.version_id,
            })
        return survey.to_xml().encode('utf-8')


class Formatter:
    def __init__(self, name, data_type):
        self.data_type = data_type
        self.name = name

    def format(self, val):
        return "{val}".format(val=val)

    def __repr__(self):
        return "<Formatter type='%s' name='%s'>" % (self.data_type, self.name)

