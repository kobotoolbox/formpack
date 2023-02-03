'''
FormPack object with
    default_image_max_pixels=None does not touch 'max-pixels'
    default_image_max_pixels=integer sets "parameters" column of questions of type == 'image'

    To override default behavior and unset "max-pixels", set the value to -1 in the xlsform
    See: https://xlsform.org/en/#image
'''
from formpack import FormPack
from formpack.utils.xlsform_parameters import parameters_string_to_dict, parameters_dict_to_string


# used in this test file
def fp_content_with_row(rdata, **kwargs):
    return FormPack([{'content': {'survey': [{
        'name': 'q1', 'label': 'q1 label',
        **rdata,
    }]}, 'version': 'v1'}], 'title', 'idstr', **kwargs)


# used in this test file
def fp_content_with_row_to_xml(rdata, default_image_max_pixels):
    return fp_content_with_row(rdata, default_image_max_pixels=default_image_max_pixels)[0].to_xml()

#
# Test micro utils:
#  - parameters_string_to_dict
#  - parameters_dict_to_string
#
def test_string_to_dict():
    aa = parameters_string_to_dict('abc=123 def=456')
    assert aa['abc'] == '123'
    assert aa['def'] == '456'


def test_dict_to_string():
    assert parameters_dict_to_string({'abc': '987', 'def': '654'}) == 'abc=987 def=654'

#
# Test variations of FormPack(..., default_image_max_pixels=...).to_xml()
#
def test_has_max_pixels_set_00():
    '''
    if default not set
    and row sets nothing
    then no orx:max-pixels is in xform
    '''
    assert 'orx:max-pixels' not in \
        fp_content_with_row_to_xml({
            'type': 'image',
        }, None)


def test_has_max_pixels_set_01():
    '''
    if default is not set
    and row sets 222
    then 222 is in xform
    '''
    assert 'orx:max-pixels="222"' in \
        fp_content_with_row_to_xml({
            'type': 'image',
            'parameters': 'max-pixels=222',
        }, None)


def test_has_max_pixels_set_10():
    '''
    if default is 111
    and row sets nothing
    then 111 is in xform
    '''
    assert 'orx:max-pixels="111"' in \
        fp_content_with_row_to_xml({'type': 'image'}, '111')


def test_has_max_pixels_set_11():
    '''
    if default is 111
    and row sets value to 222
    then 222 is in xform
    '''
    assert 'orx:max-pixels="222"' in \
        fp_content_with_row_to_xml({
            'type': 'image',
            'parameters': 'max-pixels=222'
        }, '111')


def test_has_max_pixels_set_with_numeric_default():
    '''
    if default is 111 (int)
    and row sets nothing
    then "111" is in xform
    '''
    assert 'orx:max-pixels="111"' in \
        fp_content_with_row_to_xml({'type': 'image'}, 111)


def test_can_unset_default_with_negative1():
    '''
    if default is set to 111
    and row sets -1
    then no orx:max-pixels is in xform
    '''
    assert 'orx:max-pixels' not in \
        fp_content_with_row_to_xml({
            'type': 'image',
            'parameters': 'max-pixels=-1',
        }, 111)
