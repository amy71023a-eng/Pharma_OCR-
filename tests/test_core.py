from pathlib import Path
import sqlite3
import pytest
from fastapi.testclient import TestClient
from docx import Document
from PIL import Image
from app import parse, normalize_date, save_etl, report, ocr_pages, app

def test_fields():
    r=parse('Product: DEMO\nLOT: AB123\nEXP: 2028/02\nLeaflet text')
    assert (r.product,r.batch,r.expiry)==('DEMO','AB123','2028-02-29')
    assert 'Leaflet text' in r.full_text

@pytest.mark.parametrize('raw,expected',[('2028-02-29','2028-02-29'),('2027/02','2027-02-28'),('2026-02-30',None),('2O28/01',None),('31/12/2028',None)])
def test_dates(raw,expected): assert normalize_date(raw)==expected

def test_missing():
    r=parse('unreadable')
    assert r.product is None and r.batch is None and r.expiry is None
    assert len(r.warnings)>=3 and r.review_required

def test_no_guess(): assert parse('LOT: A0O1\nEXP: 2O28/01').batch=='A0O1'

def test_duplicate(tmp_path):
    r=parse('Product: DEMO\nLOT: A1\nEXP: 2028/01')
    assert save_etl([r,r],tmp_path/'db')=={'inserted':1,'duplicates':1,'total':1,'missing_expiry':0}

def test_report(tmp_path):
    p=tmp_path/'original.png'; Image.new('RGB',(200,100),'white').save(p)
    target=tmp_path/'report.docx'; report(parse('demo'),[p],target)
    d=Document(target)
    assert len(d.inline_shapes)==1
    assert '覆核' in '\n'.join(x.text for x in d.paragraphs)

def test_ocr_failure(monkeypatch,tmp_path):
    import pytesseract
    monkeypatch.setattr(pytesseract,'image_to_data',lambda *a,**k: (_ for _ in ()).throw(RuntimeError('engine failed')))
    p=tmp_path/'x.png'; Image.new('RGB',(50,50)).save(p)
    with pytest.raises(RuntimeError): ocr_pages([p],'eng')

def test_api():
    c=TestClient(app)
    assert c.get('/health').status_code==200
    assert c.post('/text',json={'text':''}).status_code==422
    r=c.post('/text',json={'text':'Product: DEMO\nLOT: TEST\nEXP: 2028/01'})
    assert r.status_code==200
    assert c.get(r.json()['report_url']).content[:2]==b'PK'
    assert c.get('/reports/invalid').status_code==404

def test_low_confidence():
    assert any('85' in w for w in parse('Product: A\nLOT: B\nEXP: 2028/01',20,'ocr').warnings)

def test_etl_rejects_invalid_date(tmp_path):
    import json
    from etl import load
    p=tmp_path/'bad.json'; p.write_text(json.dumps([{'full_text':'x','expiry':'2026-02-30'}]))
    with pytest.raises(ValueError): load(p)

def test_csv(tmp_path):
    from etl import load
    p=tmp_path/'rows.csv';p.write_text('product,batch,expiry,full_text\nA,B,2028-01-31,source\n')
    assert load(p)[0].batch=='B'

def test_evaluation():
    from evaluate import evaluate
    g={'x':{'product':'A','batch':'B','expiry':'2028-01-31','full_text':'abc'}}
    m=evaluate(g,{'x':{'product':'A','batch':'WRONG','full_text':'ab'}})
    assert m['precision']==.5 and m['recall']==pytest.approx(1/3) and m['CER']==pytest.approx(1/3)
