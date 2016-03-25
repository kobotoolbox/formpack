import json
import requests

from f8dff.fixtures import build_fixture
from f8dff.models.formpack.pack import FormPack

import os
import glob

projects = {}
for dirname in glob.glob('f8dff/fixtures/simplest'):
    if os.path.isdir(dirname):
        fixture_name = os.path.basename(dirname)
        proj = FormPack(**build_fixture(fixture_name)
                        ).validate()
        projects[fixture_name] = proj
        ddd = proj.to_dict()
        print proj.latest_version().to_xml()


destination = 'http://localhost:8000'


AUTH = ('kobo', 'pass', )
HEADERS = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
}


def _asset_exists(query_string):
    url = ''.join([
        destination,
        '/assets/?q=',
        '(%s)' % query_string,
        '+AND+',
        '(asset_type:%s)' % 'survey',
    ])
    matches = requests.get(url, headers=HEADERS, auth=AUTH).json()
    if matches.get('count') == 0:
        return False
    return [r.get('uid') for r in matches.get('results')]


def _put_asset(uid, data):
    url = ''.join([
        destination,
        '/assets/%s/' % uid,
    ])
    patched = requests.put(url, data=json.dumps(data),
                           headers=HEADERS, auth=AUTH)
    try:
        result = patched.json()
    except Exception:
        with open('debug.html', 'w') as ff:
            ff.write(patched.text)
        result = {'local_error': 'see debug.html for details'}
    return result


def _delete_asset(uid):
    url = ''.join([
        destination,
        '/assets/%s/' % uid,
    ])
    reqd = requests.delete(url, headers=HEADERS, auth=AUTH)
    if reqd.text == '':
        result = {}
    else:
        try:
            result = reqd.json()
        except Exception:
            with open('debug.html', 'w') as ff:
                ff.write(reqd.text)
            result = {'local_error': 'see debug.html for details'}
    return result


def _post_asset(data):
    url = ''.join([
        destination,
        '/assets/'
    ])
    posted = requests.post(url, data=json.dumps(data),
                           headers=HEADERS, auth=AUTH)
    try:
        result = posted.json()
    except Exception:
        with open('debug.html', 'w') as ff:
            ff.write(posted.text)
        result = {'local_error': 'see debug.html for details'}
    return result

if __name__ == "__main__":
    for asset_proj in projects.values():
        existing_uids = _asset_exists(asset_proj.name)
        _content = asset_proj.latest_version().to_dict().get('content')
        asset_params = {
            u'name': asset_proj.name,
            u'asset_type': asset_proj.asset_type,
            u'content': json.dumps(_content),
        }
        exists_already = True if existing_uids else False
        if exists_already:
            result = _put_asset(existing_uids[0], asset_params)
        else:
            result = _post_asset(asset_params)
        print '%s | %s/#/forms/%s' % (
                    'saved  ' if exists_already else 'created',
                    destination,
                    result.get('uid'),
                    )
