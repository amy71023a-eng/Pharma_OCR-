import json
import httpx
import pytest
import gemini_rag as g

@pytest.fixture
def folder(tmp_path):
    (tmp_path/'demo.md').write_text('# 示範\n## OCR\nOCR 信心低於85應人工覆核。')
    return tmp_path

def test_missing_key(monkeypatch,folder):
    monkeypatch.delenv('GEMINI_API_KEY',raising=False)
    r=g.answer_question('OCR',True,folder)
    assert r.method=='extractive_fallback' and '沒有呼叫' in r.notice

def test_no_hit_or_opt_out(monkeypatch,folder):
    monkeypatch.setattr(g,'generate',lambda *a:pytest.fail('must not call cloud'))
    assert g.answer_question('unrelated',True,folder).abstained
    assert g.answer_question('OCR',False,folder).method.startswith('lexical')

def test_transport_and_citations(monkeypatch,folder):
    monkeypatch.setenv('GEMINI_API_KEY','fake-test-key')
    monkeypatch.setenv('GEMINI_MODEL','gemini-2.5-flash')
    original=httpx.Client
    def handler(req):
        assert req.url.host=='generativelanguage.googleapis.com'
        assert 'fake-test-key' not in str(req.url)
        assert req.headers['x-goog-api-key']=='fake-test-key'
        body=json.loads(req.content)
        assert body['generationConfig']['responseMimeType']=='application/json'
        return httpx.Response(200,json={'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':json.dumps({'answer':'應人工覆核。','source_ids':['S1'],'abstained':False})}]}}]})
    monkeypatch.setattr(g.httpx,'Client',lambda **kw:original(transport=httpx.MockTransport(handler),**kw))
    r=g.answer_question('OCR',True,folder)
    assert r.method=='gemini_grounded_answer' and r.sources[0].source_id=='S1'

@pytest.mark.parametrize('kind',['timeout','429','401','bad_json','unknown_source','truncated','blocked'])
def test_failures_fallback(monkeypatch,folder,kind):
    monkeypatch.setenv('GEMINI_API_KEY','fake-test-key')
    original=httpx.Client
    def handler(req):
        if kind=='timeout':raise httpx.ReadTimeout('secret must not leak')
        if kind in ['429','401']:return httpx.Response(int(kind),json={'error':'secret must not leak'})
        if kind=='blocked':return httpx.Response(200,json={'promptFeedback':{'blockReason':'SAFETY'}})
        text='oops' if kind=='bad_json' else json.dumps({'answer':'bad','source_ids':['S99'],'abstained':False})
        return httpx.Response(200,json={'candidates':[{'finishReason':'MAX_TOKENS' if kind=='truncated' else 'STOP','content':{'parts':[{'text':text}]}}]})
    monkeypatch.setattr(g.httpx,'Client',lambda **kw:original(transport=httpx.MockTransport(handler),**kw))
    r=g.answer_question('OCR',True,folder)
    assert r.method=='extractive_fallback' and 'secret' not in r.model_dump_json()
