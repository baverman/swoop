from swoop import Session

def test_simple():
    s = Session(debuglevel=1)
    r = s('http://fansubs.ru')
    r = r.form(idx=0, values={'query':'haruhi'}).fetch()
    r.save_content('/tmp/wow.html')
    assert False

