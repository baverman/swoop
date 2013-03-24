from collections import OrderedDict

from httplib import HTTP_PORT, HTTPS_PORT
from urlparse import urlsplit, urljoin, parse_qsl, urlunsplit
from urllib import urlencode
from mimetools import choose_boundary
from mimetypes import guess_type

class Request(object):
    def __init__(self, url, baseurl=None, session_ref=None):
        if baseurl:
            if isinstance(baseurl, Request):
                baseurl = baseurl.url

            url = urljoin(baseurl.get_url(), url)

        self.session_ref = session_ref

        url = urlsplit(url)
        self._scheme = url.scheme
        self._netloc = url.netloc
        self.host = url.hostname
        self.is_secure = self._scheme == 'https'
        self._port = url.port if url.port else (HTTPS_PORT if self.is_secure else HTTP_PORT)
        self._path = url.path or '/'

        assert self._scheme in ('http', 'https')
        assert self.host

        self.query = OrderedDict(parse_qsl(url.query, True))
        self.params = OrderedDict()
        self.files = OrderedDict()
        self.multipart = False

        self.follow_redirects = True
        self.referer = None

    @property
    def path_qs(self):
        return urlunsplit(('', '', self._path, urlencode(self.query), ''))

    @property
    def url(self):
        return urlunsplit((self._scheme, self._netloc, self._path, urlencode(self.query), ''))

    def request(self, pool, headers):
        conn = pool.get_connection(self.host, self._port, self.is_secure)

        method = 'GET'
        body = None

        if self.multipart:
            method = 'POST'
            files = ((name, fname, value) for name, (fname, value) in self.files.iteritems())
            params = (r for r in self.params.iteritems() if r[1] is not None)
            content_type, body = encode_multipart_formdata(params, files)
            headers['Content-Type'] = content_type
        elif self.params:
            method = 'POST'
            body = urlencode(self.params)
            headers['Content-Type'] = 'application/x-www-form-urlencoded'

        conn.request(method, self.path_qs, body, headers)
        response = conn.getresponse()

        if response.getheader('connection', '').lower() == 'close':
            conn.close()

        response.url = self.url
        response.host = self.host
        return response

    def fetch(self):
        assert self.session_ref
        session = self.session_ref()
        assert session
        return session(self)

def post_multipart(host, selector, fields, files):
    """
    Post fields and files to an http host as multipart/form-data.
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files
    Return the server's response page.
    """
    content_type, body = encode_multipart_formdata(fields, files)
    headers = {'Content-Type': content_type,
               'Content-Length': str(len(body))}

# Active state recipe
# http://code.activestate.com/recipes/146306-http-client-to-post-using-multipartform-data/
def encode_multipart_formdata(fields, files):
    """
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files
    Return (content_type, body) ready for httplib.HTTP instance
    """
    BOUNDARY = choose_boundary()
    CRLF = '\r\n'
    L = []
    for (key, value) in fields:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('')
        L.append(value)
    for (key, filename, value) in files:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
        L.append('Content-Type: %s' % get_content_type(filename))
        L.append('')
        L.append(value)
    L.append('--' + BOUNDARY + '--')
    L.append('')
    body = CRLF.join(L)
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return content_type, body

def get_content_type(filename):
    return guess_type(filename)[0] or 'application/octet-stream'