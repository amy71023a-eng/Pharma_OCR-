from fastapi.testclient import TestClient
from app import app
from rag import retrieve

def test_source_and_grounding():
    r=retrieve('OCR 信心低於85怎麼處理')
    assert not r.abstained and r.sources
    assert all(s.excerpt in r.answer for s in r.sources)
    assert any(s.source=='sop-demo.md' for s in r.sources)

def test_abstain():
    r=retrieve('明天天氣與股市預測')
    assert r.abstained and r.sources==[]

def test_rag_api():
    c=TestClient(app)
    assert c.post('/rag',json={'question':'色塊與版面如何比較'}).json()['sources']
    assert c.post('/rag',json={'question':''}).status_code==422

def test_empty_knowledge(tmp_path):
    assert retrieve('OCR信心處理',tmp_path).abstained
