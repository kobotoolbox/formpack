# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

from .pack import FormPack

import os
import json
import errno
import requests

from urlparse import urlparse


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def _get_kobo_environ_vars():
    for env_var in [
            'KOBO_API_TOKEN',
            'KOBO_API_URL',
        ]:
        if not env_var in os.environ:
            raise ValueError('Configuration value not present: {}'.format(env_var))
    _data_dir = os.environ.get('FORMPACK_DATA_DIRECTORY', None)
    if not _data_dir:
        _data_dir = os.path.join(os.path.expanduser('~'),
                                 '.formpack')
        mkdir_p(_data_dir)
    return (
        os.environ['KOBO_API_TOKEN'],
        os.environ['KOBO_API_URL'],
        _data_dir,
        )


class RemoteFormPack:
    def __init__(self, uid):
        self.uid = uid
        (self.api_token,
            self.api_url,
            self._data_dir) = _get_kobo_environ_vars()

        self.data_dir = os.path.join(self._data_dir, self.uid)
        mkdir_p(self.data_dir)
        self._versions_dir = os.path.join(self.data_dir, 'versions')
        self._data_path = os.path.join(self.data_dir, 'data.json')
        mkdir_p(self._versions_dir)

        _url = '{}{}/?format=json'.format(self.api_url, self.uid)
        r1 = requests.get(_url,
                          headers=self._headers(),
                          ).json()
        self._deployment_identifier = r1['deployment__identifier']
        version_id = r1['version_id']
        _version_file_path = self._version_file_path(version_id)

        if not os.path.exists(_version_file_path):
            with open(_version_file_path, 'w') as ff:
                ff.write(json.dumps(resp_data['content'], indent=4))

        _deployment = urlparse(self._deployment_identifier)
        self._kc_api_url = '{}://{}/api/v1'.format(_deployment.scheme,
                                                   _deployment.netloc)
        r2 = requests.get('{}/forms?id_string={}'.format(self._kc_api_url, self.uid),
                          headers=self._headers()).json()
        self.kc_formid = r2[0]['formid']

    def pull(self):
        _data_url = '{}/data/{}'.format(self._kc_api_url, self.kc_formid)
        resp = requests.get('{}{}'.format(_data_url, '?format=json'),
                            headers=self._headers())
        with open(self._data_path, 'w') as ff:
            ff.write(resp.content)
        _version_ids = set([i['__version__'] for i in resp.json()])
        for _version_id in _version_ids:
            self._ensure_version(_version_id)

    def _ensure_version(self, version_id):
        _f = self._version_file_path(version_id)
        if not os.path.exists(_f):
            raise Exception('version content not found. please write'
                            ' content to file and rerun script\n{}'.format(_f))

    def _version_file_path(self, version_id):
        return os.path.join(self._versions_dir, '{}.json'.format(version_id))

    def _headers(self, upd={}):
        return dict({'Content-Type': 'application/json',
                    'Authorization': 'Token {}'.format(self.api_token),
                    }, **upd)

    def pack(self):
        with open(self._data_path, 'r') as ff:
            self.submissions = json.loads(ff.read())
        _version_ids = set([s['__version__'] for s in self.submissions])
        self.versions = []
        for version_id in _version_ids:
            with open(self._version_file_path(version_id), 'r') as ff:
                self.versions.append({'content': json.loads(ff.read())})
        return FormPack(versions=self.versions, id_string=self.uid)
