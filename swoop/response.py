import zlib, gzip
from weakref import ref
from cStringIO import StringIO

from .xpath import XPathWrapper
from .form import get_request_for_form

class Response(object):
    def __init__(self, session, response, response_data):
        self.session_ref = ref(session)
        self.response = response
        self.encoding = response.msg.getparam('charset') or session.encoding

        encoding = response.getheader('content-encoding', '')
        self.raw_content = response_data
        if encoding == 'deflate':
            self.raw_content = zlib.decompress(self.raw_content)
        elif encoding == 'gzip':
            self.raw_content = gzip.GzipFile('', 'rb', 9, StringIO(self.raw_content)).read()

        self.xpath = XPathWrapper(self.raw_content, self.encoding)
        self.url = response.url

    @property
    def content(self):
        try:
            return self._content
        except AttributeError:
            pass

        self._content = self.raw_content.decode(self.encoding)
        return self._content

    def save_content(self, filename):
        with open(filename, mode='w') as f:
            f.write(self.raw_content)

        return filename

    def form(self, action=None, id=None, idx=None, name=None, submit=True, values=None):
        return get_request_for_form(self, action=action, id=id, idx=idx, name=name, submit=submit,
            values=values)