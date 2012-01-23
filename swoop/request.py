from collections import OrderedDict

from httplib import HTTP_PORT, HTTPS_PORT
from urlparse import urlsplit, urljoin, parse_qsl, urlunsplit
from urllib import urlencode

class Request(object):
    def __init__(self, url, baseurl=None):
        if baseurl:
            url = urljoin(baseurl.get_url(), url)

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

        self.method = 'GET'
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
        conn.request(self.method, self.path_qs, headers=headers)
        response = conn.getresponse()

        if response.getheader('connection', '').lower() == 'close':
            conn.close()

        response.url = self.url
        response.host = self.host
        return response
