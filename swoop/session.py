from collections import defaultdict
from Cookie import SimpleCookie
from cookielib import Cookie

from weakref import ref

from .pool import ConnectionPool
from .request import Request
from .response import Response

MAX_REDIRECTS = 10

class Session(object):
    def __init__(self, debuglevel=None):
        self._pool = ConnectionPool(debuglevel=debuglevel)
        self.cookies = defaultdict(dict)
        self.encoding = None
        self.user_agent = None

    def _set_cookies(self, headers, request):
        cookies = [c for domain, cookies in self.cookies.iteritems()
            if request.host.endswith(domain) or domain == '_all' for c in cookies.itervalues()]

        if cookies:
            headers['Cookie'] = '; '.join(c.output([], '').lstrip() for c in cookies)

    def set_cookie(self, name, value=None, domain='_all'):
        if isinstance(name, Cookie):
            name, value = name.name, name.value
            domain = name.domain or domain

        c = SimpleCookie()
        c[name] = value

        for cookie in c.itervalues():
            self.cookies[domain.rstrip(',').lstrip('.')][cookie.key] = cookie

    def _get_cookies(self, response):
        c = SimpleCookie()
        for h, v in response.getheaders():
            if h == 'set-cookie':
                c.load(v)

        for cookie in c.itervalues():
            domain = cookie['domain'].rstrip(',').lstrip('.') or response.host
            self.cookies[domain][cookie.key] = cookie

    def _get_default_headers(self):
        return {
            'User-Agent': self.user_agent or \
                'Opera/9.80 (X11; Linux i686; U; en) Presto/2.10.229 Version/11.60',
            'Accept': 'text/html, application/xml;q=0.9, application/xhtml+xml, image/png,'
                      ' image/webp, image/jpeg, image/gif, image/x-xbitmap, */*;q=0.1',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'Keep-Alive'
        }

    def request(self, request):
        if isinstance(request, basestring):
            request = Request(request)

        count = MAX_REDIRECTS
        while count:
            headers = self._get_default_headers()

            if request.referer:
                headers['Referer'] = request.referer.url if\
                    isinstance(request.referer, (Response, Request)) else request.referer

            self._set_cookies(headers, request)
            response = request.request(self._pool, headers)
            response_data = response.read()
            self._get_cookies(response)

            if 300 <= response.status < 400:
                request = Request(response.getheader('location'))
                request.referer = response.url
                count -= 1
            else:
                break

        return Response(self, response, response_data)

    def __call__(self, url, baseurl):
        return Request(url, baseurl, ref(self))

    def clear(self):
        self._pool.clear()
        self.cookies.clear()
