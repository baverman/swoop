from cStringIO import StringIO
from lxml import etree
from .exceptions import ContentException

class XPathWrapper(object):
    def __init__(self, content):
        self.content = content

    @property
    def tree(self):
        try:
            return self._tree
        except AttributeError:
            pass

        self._tree = etree.parse(StringIO(self.content), etree.HTMLParser())
        return self._tree

    def __call__(self, xpath):
        result = self.tree.xpath(xpath)

        if not result:
            raise ContentException('XPath not found [%s]' % xpath)

        if len(result) > 1:
            raise ContentException('There is more than one element [%s]' % xpath)

        try:
            return result[0]
        except IndexError:
            raise ContentException('XPath not found [%s]' % xpath)

    def many(self, xpath):
        result = self.tree.xpath(xpath)
        if not result:
            raise ContentException('XPath not found [%s]' % xpath)

        return result

    def any(self, xpath):
        return self.tree.xpath(xpath)

    def clear(self):
        try:
            del self._tree
        except AttributeError:
            pass

    @staticmethod
    def textof(elem):
        return ''.join(elem.itertext())

    @staticmethod
    def tostring(elem, asunicode=False):
        result = etree.tostring(elem, encoding='utf8')
        if asunicode:
            result = result.decode('utf-8')

        return result
