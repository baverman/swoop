from swoop import Session

def test_simple():
    s = Session()
    r = s.request('http://fansubs.ru')
    r = s.request(r.form(idx=0, values={'query':'haruhi'}))
    r.save_content('/tmp/wow.html')
    assert False

