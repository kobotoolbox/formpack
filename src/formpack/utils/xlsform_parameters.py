'''
parameters_string_to_dict:
    - converts a string "key=val key2=val2" into a dict {'key': 'val', 'key2': 'val2'}
parameters_dict_to_string:
    - converts a dict {'key': 'val', 'k2': 'val'} into a string "key=val k2=val"
'''
import re


def parameters_string_to_dict(params_str):
    dd = {}
    # print(params_str)
    for param in re.split('\s+', params_str):
        if '=' in param:
            (key, val) = param.split('=')
            dd[key] = val
    return dd


def parameters_dict_to_string(params_dict):
    ps = []
    for (key, val) in params_dict.items():
        ps.append(f'{key}={val}')
    return ' '.join(ps)
