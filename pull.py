from formpack.remote_pack import RemoteFormPack, FORMPACK_DATA_DIR

import os
import json
import argparse
import importlib


parser = argparse.ArgumentParser(description='Initialize RemoteFormPack.')

parser.add_argument('--refresh-data',
                    dest='refresh_data',
                    help='flush data cache',
                    action='store_true')

parser.add_argument('--print-stats',
                    dest='print_stats',
                    help='print stats from the dataset',
                    action='store_true')

parser.add_argument('--print-survey',
                    dest='print_survey',
                    help='print survey questions',
                    action='store_true')

parser.add_argument('--print-submissions',
                    dest='print_submissions',
                    help='print submissions from the dataset',
                    action='store_true')

parser.add_argument('--run-module',
                    dest='run_module',
                    help='import and run a module',
                    action='store')

parser.add_argument('--account',
                    dest='account',
                    help='server:account corresponding to local config',
                    action='store')

parser.add_argument('uid',
                    nargs=1,
                    help='formid',
                    action='store')


def load_pack(uid, account):
    accounts_file = os.environ.get('KOBO_ACCOUNTS', False)
    if not accounts_file:
        accounts_file = os.path.join(FORMPACK_DATA_DIR, 'accounts.json')
    if not os.path.exists(accounts_file):
        raise ValueError('need an accounts json file in {}'.format(
                         accounts_file))
    with open(accounts_file, 'r') as ff:
        accounts = json.loads(ff.read())
    try:
        _account = accounts[account]
    except KeyError:
        raise ValueError('accounts.json needs a configuration for {}'.format(
                         account))
    return RemoteFormPack(uid=uid,
                          token=_account['token'],
                          api_url=_account['api_url'],
                          )


def run(args):
    rpack = load_pack(uid=args.uid[0],
                      account=args.account)

    if args.refresh_data:
        print('clearing submissions')
        rpack.clear_submissions()

    rpack.pull()
    formpk = rpack.create_pack()

    if args.print_stats:
        print(json.dumps(formpk._stats, indent=2))

    if args.print_survey:
        print(json.dumps(formpk.get_survey(), indent=2))

    if args.print_submissions:
        print(json.dumps(list(rpack.submissions), indent=2))

    if args.run_module:
        _mod = importlib.import_module(args.run_module)
        if not hasattr(_mod, 'run') and hasattr(_mod.run, '__call__'):
            _mod.run(formpk, submissions=rpack.submissions)
        else:
            raise ValueError('run-module parameter must be an importable '
                             'module with a method "run"')

if __name__ == '__main__':
    run(parser.parse_args())
