from swoop import Session

def test_simple():
    s = Session()
    r = s.request('http://fansubs.ru')
    print r.xpath.many('//a/text()')
    assert False

