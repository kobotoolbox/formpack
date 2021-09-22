import re

def get_valid_filename(name):
    """
    Copied over from django/utils/text.py#L225-L238 to emulate filename
    handling in KPI
    """
    s = str(name).strip().replace(' ', '_')
    s = re.sub(r'(?u)[^-\w.]', '', s)
    return s
