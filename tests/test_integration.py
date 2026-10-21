"""真實引擎整合測試；工具不存在時明確 skip，不冒充通過。"""
import shutil
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app import app,ROOT
pytestmark=pytest.mark.skipif(not shutil.which('tesseract') or not shutil.which('pdftoppm'),reason='需要 Tesseract 與 Poppler')
@pytest.mark.parametrize('name',['box.png','sample.pdf'])
def test_real_ocr_api(name):
    c=TestClient(app)
    with (ROOT/'examples'/name).open('rb') as f:
        response=c.post('/ocr',files={'file':(name,f,'application/pdf' if name.endswith('pdf') else 'image/png')})
    assert response.status_code==200,response.text
    result=response.json()['result']
    assert result['product']=='DEMO MEDICINE'
    assert result['batch']=='DEMO2026A' and result['expiry']=='2028-12-31'
    assert result['mode']=='ocr' and result['review_required']
    assert c.get(response.json()['report_url']).content.startswith(b'PK')

def test_corrupt_upload():
    c=TestClient(app)
    assert c.post('/ocr',files={'file':('bad.png',b'broken','image/png')}).status_code==422
    assert c.post('/ocr',files={'file':('bad.exe',b'broken','application/octet-stream')}).status_code==415
