# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

from collections import OrderedDict

from .utils import formversion_pyxform
from f8dff.models.formpack.submission import FormSubmission
from f8dff.models.formpack.utils import parse_xml_to_xmljson


class FormVersion:
    def __init__(self, version_data, parent):
        if 'name' in version_data:
            raise ValueError('FormVersion should not have a name parameter. '
                             'consider using "title" or "id_string"')
        self._v = version_data
        self._parent = parent
        self._names = []
        self._root_node_name = version_data.get('root_node_name')
        self.version_title = version_data.get('title')
        self._submissions = []
        self.id_string = version_data.get('id_string')
        self._version_id = version_data.get('version')

        schema = OrderedDict()

        content = self._v.get('content', {})

        for item in content.get('survey', []):
            if 'name' in item:
                name = item['name']
                self._names.append(name)
                schema[name] = {
                    "type": item['type']
                }

        self._formatters = OrderedDict()
        for name, structure in schema.items():
            # question_type = get_question_type(name, version)
            # formater_class = formater_registry[question_type]
            self._formatters[name] = Formatter(name, structure['type'])

        for submission in version_data.get('submissions', []):
            self.load_submission(submission)

    def __repr__(self):
        return '<models.formpack.version.FormVersion %s>' % self._stats()

    def _stats(self):
        _stats = OrderedDict()
        _stats['id_string'] = self._get_id_string()
        _stats['version'] = '' if not self._version_id else self._version_id
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
        if _version_id != self._version_id:
            raise ValueError('mismatching version id %s != %s' %
                             (self._version_id, _version_id))
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
                'version': self._version_id,
            })
        return survey.to_xml().encode('utf-8')


class Formatter:
    def __init__(self, data_type, name):
        self.data_type = data_type
        self.name = name

    def format(self, val):
        return "{data_type}:{val}".format(data_type=self.data_type, val=val)