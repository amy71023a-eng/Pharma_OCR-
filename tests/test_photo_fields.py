"""不含真實照片或序號；以虛構標籤測試解析及保守的候選合併。"""
from pathlib import Path
from PIL import Image
from app import normalize_date,parse,ocr_pages

def test_month_year_and_optional_colon():
    r=parse('EXP 02/2027\nLot AB1234\nSN 123456789012')
    assert r.expiry=='2027-02-28' and r.expiry_raw=='02/2027'
    assert r.batch=='AB1234' and r.serial_number=='123456789012'

def test_label_does_not_match_word_prefix():
    assert parse('Lottery 12345\nSNAKE 99999').batch is None
    assert parse('Lottery 12345\nSNAKE 99999').serial_number is None

def test_no_substitution():
    assert parse('Lot G0O111\nEXP O2/2027').batch=='G0O111'
    assert parse('EXP O2/2027').expiry is None

def test_sn_spaces_preserved_as_digits():
    assert parse('SN: 123456 789012').serial_number=='123456789012'

def test_month_year_invalid():
    assert normalize_date('13/2027') is None
    assert normalize_date('02/2028')=='2028-02-29'

def test_conflicting_attempts_not_guessed(monkeypatch,tmp_path):
    import ocr_upgrade
    p=tmp_path/'test.png';Image.new('RGB',(100,100)).save(p)
    def fake(*args):
        for source,code in [('original','AB1234'),('label_sharp','A81234')]:
            yield {'source':source,'text':f'LOT {code}\nEXP 02/2027\nSN 123456789012','confidence':90,'box':[0,0,100,100]}
    monkeypatch.setattr(ocr_upgrade,'attempts_for',fake)
    r=ocr_pages([p]);assert r.batch is None
    assert r.field_candidates['batch']==['AB1234','A81234']
    assert r.serial_number=='123456789012' and r.review_required
    assert len(r.ocr_attempts)==2
