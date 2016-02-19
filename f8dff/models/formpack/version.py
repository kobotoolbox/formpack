from collections import OrderedDict

from utils import formversion_pyxform
from f8dff.models.formpack.submission import FormSubmission
from f8dff.models.formpack.utils import parse_xml_to_xmljson


class FormVersion:
    def __init__(self, version_data, parent):
        if 'name' in version_data:
            raise ValueError('version_data should have a title but not a name')
        self._v = version_data
        self._parent = parent
        self._names = []
        self._root_node_name = version_data.get('root_node_name')
        self.version_title = version_data.get('title')
        self._submissions = []
        self.id_string = version_data.get('id_string')
        self._version_id = version_data.get('version')
        content = self._v.get('content', {})
        for item in content.get('survey', []):
            if 'name' in item:
                self._names.append(item['name'])
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

    def _get_id_string(self):
        if self.id_string is None:
            return self._parent.id_string
        return self.id_string

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
        data_root_node_name = self._get_id_string()
        title = self._get_title()
        if title is None:
            raise ValueError('cannot create xml on a survey '
                             'with no title.')
        survey.update({
                u'name': self._root_node_name or u'data',
                u'id_string': data_root_node_name,
                u'title': title,
                u'version': self._version_id,
            })
        return survey.to_xml().encode('utf-8')

    def _add_blank_submission(self):
        self.load_submission(self.generate_blank_submission())

    def generate_blank_submission(self):
        _d = {}
        for name in self._names:
            _d[name] = '_____'
        return _d
