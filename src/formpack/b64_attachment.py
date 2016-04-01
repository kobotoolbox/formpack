from utils import randstr
import re

DATA_URI_RE = r'data:(\w+)\/(\w+);base64(.*)'


class B64Attachment(str):
    '''
    * loaded from base64 string
    * unloadable to file
    '''

    @classmethod
    def _is_attachment(kls, data_uri):
        return hasattr(data_uri, "startswith") and data_uri.startswith('data:')

    @classmethod
    def _attachment_split(kls, data_uri):
        '''
        accepts a data_uri,
        returns a tuple (mediatype, extension, contents)
        '''
        return re.match(DATA_URI_RE, data_uri).groups()

    @classmethod
    def write_to_tempfile(kls, data_uri):
        '''
        *placeholder method*

        this method will create a new TempFile (or cStringIO) with the
        contents of the data_uri which can then be POST'ed to kobocat in
        a mock submission.
        '''
        (ftype, fext, fcont) = kls._attachment_split(data_uri)
        fname = 'a%s.%s' % (randstr(10), fext)
        return (fname, '/tmp/path/to/%s' % fname)
