# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

from .pack import FormPack

import json
import errno
import requests
from urlparse import urlparse
from argparse import Namespace as Ns
from os import (path, makedirs, unlink)

FORMPACK_DATA_DIR = path.join(path.expanduser('~'),
                              '.formpack')


def mkdir_p(_path):
    try:
        makedirs(_path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and path.isdir(_path):
            pass
        else:
            raise


class RemoteFormPack:
    def __init__(self, uid,
                 token,
                 api_url,
                 data_dir=None):
        self.uid = uid
        self.api_token = token
        self.api_url = api_url
        self._data_dir = data_dir or FORMPACK_DATA_DIR

        self.data_dir = path.join(self._data_dir, self.uid)
        mkdir_p(self.data_dir)
        self.paths = {
            'versions/': self.path('versions'),
            'data': self.path('data.json'),
            'context': self.path('context.json'),
            'asset': self.path('asset.json'),
        }
        self._versions_dir = self.path('versions')
        self._data_path = self.path('data.json')
        self._context_path = self.path('context.json')
        mkdir_p(self.path('versions'))
        self._asset_url = '{}{}'.format(self.api_url, self.uid)
        self.asset = Ns(**self._query_asset())
        self.context = Ns(**self._query_kcform())

    def path(self, *args):
        return path.join(self.data_dir, *args)

    def _query_asset(self):
        if not path.exists(self.path('asset.json')):
            ad = requests.get('{}/?format=json'.format(self._asset_url),
                              headers=self._headers(),
                              ).json()
            if 'detail' in ad and ad['detail'] == 'Invalid token.':
                raise ValueError('Invalid token. Is it the correct server?')
            elif 'detail' in ad:
                raise ValueError("Error querying API: {}".format(
                                 ad['detail']))
            # content is ultimately pulled form the "version" file
            del ad['content']
            with open(self.path('asset.json'), 'w') as ff:
                ff.write(json.dumps(ad, indent=2))
            return ad
        else:
            with open(self.path('asset.json'), 'r') as ff:
                return json.loads(ff.read())

    def _query_kcform(self):
        asset = self.asset
        if not path.exists(self.path('context.json')):
            _deployment_identifier = asset.deployment__identifier
            _deployment = urlparse(_deployment_identifier)
            ctx = {
                'kc_api_url': '{}://{}/api/v1'.format(_deployment.scheme,
                                                      _deployment.netloc),
            }
            _url = '{}/forms?id_string={}'.format(ctx['kc_api_url'],
                                                  self.uid)
            r2 = requests.get(_url, headers=self._headers()).json()
            ctx['kc_formid'] = r2[0]['formid']
            with open(self.path('context.json'), 'w') as ff:
                ff.write(json.dumps(ctx, indent=2))
            return ctx
        else:
            with open(self.path('context.json'), 'r') as ff:
                return json.loads(ff.read())

    def pull(self):
        if not path.exists(self.path('data.json')):
            _data_url = '{}/data/{}?{}'.format(self.context.kc_api_url,
                                               self.context.kc_formid,
                                               'format=json',
                                               )
            _data = requests.get(_data_url, headers=self._headers()).json()
            with open(self.path('data.json'), 'w') as ff:
                ff.write(json.dumps(_data, indent=2))
            _version_ids = set([i['__version__'] for i in _data])
            for version_id in _version_ids:
                self.load_version(version_id)

    def load_version(self, version_id):
        _version_path = path.join(self.path('versions'),
                                  '{}.json'.format(version_id)
                                  )
        if not path.exists(_version_path):
            _version_url = '{}/{}/{}/?format=json'.format(
                self._asset_url,
                'versions',
                version_id)
            vd = requests.get(_version_url, headers=self._headers()).json()
            if vd.get('detail') == 'Not found.':
                raise Exception('Version not found')
            with open(_version_path, 'w') as ff:
                ff.write(json.dumps(vd, indent=2))
            return vd
        else:
            with open(_version_path, 'r') as ff:
                return json.loads(ff.read())

    def _headers(self, upd={}):
        return dict({'Content-Type': 'application/json',
                    'Authorization': 'Token {}'.format(self.api_token),
                     }, **upd)

    def create_pack(self):
        if not path.exists(self._data_path):
            raise Exception('cannot generate formpack without running '
                            'remote_pack.pull()')
        _version_ids = set([s['__version__'] for s in self.submissions])
        self.versions = []
        for version_id in _version_ids:
            _v = self.load_version(version_id)
            _v['version'] = version_id
            _v['date_deployed'] = _v.pop('date_deployed', None)
            self.versions.append(_v)
        return FormPack(versions=self.versions, id_string=self.uid,
                        title=self.asset.name, ellipsize_title=False,
                        )

    def stats(self):
        pck = self.create_pack()
        _stats = pck._stats()
        return _stats

    def _submissions(self):
        with open(self.path('data.json'), 'r') as ff:
            return json.loads(ff.read())

    def clear_submissions(self):
        _data_path = self.path('data.json')
        if path.exists(_data_path):
            unlink(_data_path)

    @property
    def submissions(self):
        for submission in self._submissions():
            yield submission
