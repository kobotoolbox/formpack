import json
import difflib

from collections import OrderedDict

from version import FormVersion
from f8dff.models.formpack.utils import get_version_identifiers


class FormPack:
    def __init__(self, *args, **kwargs):
        self.versions = []
        self.id_string = kwargs.get('id_string')
        self._versions_by_id = {}
        if 'name' in kwargs:
            raise ValueError('FormPack cannot have name. consider '
                             'using id_string, title, or description')
        self._x = kwargs
        self.title = kwargs.get('title')
        self.asset_type = kwargs.get('asset_type')
        for v in kwargs.get('versions', []):
            self.load_version(v)
        if 'submissions_xml' in kwargs:
            self._load_submissions_xml(kwargs.get('submissions_xml'))

    def __repr__(self):
        return '<models.formpack.pack.FormPack %s>' % self._stats()

    def lookup(self, prop, default=None):
        # can't use a one liner because sometimes self.prop is None
        result = getattr(self, prop, default)
        if result is None:
            return default
        return result

    def latest_version(self):
        return self.versions[-1]

    def _stats(self):
        _stats = OrderedDict()
        _stats['id_string'] = self.id_string
        _stats['versions'] = len(self.versions)
        _stats['submissions'] = self._submissions_count()
        _stats['row_count'] = len(self.versions[-1]._v.get('content', {})
                                                      .get('survey', []))
        # returns stats in the format [ key="value" ]
        return '\n\t'.join(map(lambda key: '%s="%s"' % (
                            key, str(_stats[key])), _stats.keys()))

    def _load_submissions_xml(self, submissions):
        for submission_xml in submissions:
            (id_string, version_id) = get_version_identifiers(submission_xml)
            if version_id not in self._versions_by_id:
                raise KeyError('version [%s] is not available' % version_id)
            cur_ver = self._versions_by_id[version_id]
            cur_ver._load_submission_xml(submission_xml)

    def load_version(self, v):
        _v = FormVersion(v, self)
        version_id = _v._version_id
        if version_id in self._versions_by_id:
            if version_id is None:
                raise ValueError('cannot have two versions without '
                                 'a "version" id specified')
            else:
                raise ValueError('cannot have duplicate version id: %s'
                                 % version_id)
        self._versions_by_id[version_id] = _v
        if _v.id_string:
            if self.id_string and self.id_string != _v.id_string:
                raise ValueError('Versions must of the same form must '
                                 'share an id_string: %s != %s' % (
                                    self.id_string,
                                    _v.id_string,
                                 ))

            self.id_string = _v.id_string
        if (self.title is None) and _v.version_title:
            self.title = _v.version_title
        self.versions.append(_v)

    def version_diff(self, vn1, vn2):
        v1 = self.versions[vn1]
        v2 = self.versions[vn2]

        def summr(v):
            return json.dumps(v._v.get('content'),
                              indent=4,
                              sort_keys=True,
                              ).splitlines(1)
        out = []
        for line in difflib.unified_diff(summr(v1),
                                         summr(v2),
                                         fromfile="v%d" % vn1,
                                         tofile="v%d" % vn2,
                                         n=1):
            out.append(line)
        return ''.join(out)

    def _submissions_count(self):
        sc = 0
        for v in self.versions:
            sc += v._submissions_count()
        return sc

    def to_dict(self, **kwargs):
        out = {
            u'versions': [v.to_dict() for v in self.versions],
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

    def submissions_list(self):
        return list(self.submissions_gen())

    def submissions_gen(self):
        for version in self.versions:
            for submission in version._submissions:
                yield submission


    def _to_ss_generator(self, options):
        '''
        ss_generator means "spreadsheet" structure with generators instead of lists
        '''
        if not isinstance(options, dict):
            raise ValueError('options must be provided')
        sheets = OrderedDict()
        latest_version = self.versions[-1]
        column_formatters = latest_version._formatters

        def _generator():
            for submission in self.submissions_gen():
                row = []
                for (colname, formatter) in column_formatters.iteritems():
                    row.append(formatter.format(submission._data.get(colname)))
                yield row
        sheets['submissions'] = [column_formatters.keys(), _generator()]
        return sheets

    def _export_to_lists(self, options):
        '''
        this defeats the purpose of using generators, but it's useful for tests
        '''
        gens = self._to_ss_generator(options)
        out = []
        for key in gens.keys():
            (headers, _gen) = gens[key]
            vals = list(_gen)
            out.append([key, [headers, vals]])
        return out
