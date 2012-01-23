import zlib, gzip
from cStringIO import StringIO

from .xpath import XPathWrapper

class Response(object):
    def __init__(self, session, response):
        self.response = response
        self.encoding = response.msg.getparam('charset') or session.encoding

        encoding = response.getheader('content-encoding', '')
        self.raw_content = response.read()
        if encoding == 'deflate':
            self.raw_content = zlib.decompress(self.raw_content)
        elif encoding == 'gzip':
            self.raw_content = gzip.GzipFile('', 'rb', 9, StringIO(self.raw_content)).read()

        self.xpath = XPathWrapper(self.raw_content)

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
