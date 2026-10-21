"""可選 Gemini RAG；僅上傳本次命中的文字，不上傳照片或完整知識庫。"""
import json
import logging
import os
import re
import httpx
from rag import retrieve, Answer
from llm_contract import SYSTEM_PROMPT, validate_citations

log=logging.getLogger(__name__)

def configuration():
    return {'provider':'Google Gemini','configured':bool(os.getenv('GEMINI_API_KEY','').strip()),
            'model':os.getenv('GEMINI_MODEL','gemini-3.1-flash-lite'),'live_connection_verified':False}

def generate(question,sources):
    model=configuration()['model']
    if not re.fullmatch(r'gemini-[a-z0-9.-]+',model):raise ValueError('invalid model')
    schema={'type':'OBJECT','properties':{'answer':{'type':'STRING'},'source_ids':{'type':'ARRAY','items':{'type':'STRING','enum':[s.source_id for s in sources]}},'abstained':{'type':'BOOLEAN'}},'required':['answer','source_ids','abstained']}
    payload={'systemInstruction':{'parts':[{'text':SYSTEM_PROMPT}]},'contents':[{'role':'user','parts':[{'text':json.dumps({'question':question,'references':[s.model_dump() for s in sources]},ensure_ascii=False)}]}],
             'generationConfig':{'responseMimeType':'application/json','responseSchema':schema,'temperature':0,'maxOutputTokens':2048}}
    # 金鑰只放 header；不記錄請求內容、金鑰或原始錯誤回應。無自動重試。
    with httpx.Client(timeout=30,follow_redirects=False) as client:
        response=client.post(f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent',headers={'x-goog-api-key':os.environ['GEMINI_API_KEY']},json=payload)
        response.raise_for_status()
    candidate=response.json()['candidates'][0]
    if candidate.get('finishReason')!='STOP':raise ValueError('incomplete response')
    text=''.join(part.get('text','') for part in candidate['content']['parts'] if not part.get('thought'))
    return validate_citations(json.loads(text),{s.source_id for s in sources})

def answer_question(question,use_llm=False,folder=None):
    result=retrieve(question,folder)
    if not use_llm or result.abstained:return result
    if not configuration()['configured']:
        return result.model_copy(update={'method':'extractive_fallback','notice':'尚未設定 GEMINI_API_KEY，改顯示本機原文；沒有呼叫雲端。'})
    sources=[s.model_copy(update={'source_id':f'S{i}'}) for i,s in enumerate(result.sources,1)]
    try:
        generated=generate(question,sources)
        return Answer(answer=generated.answer,abstained=generated.abstained,sources=[s for s in sources if s.source_id in generated.source_ids],method='gemini_grounded_answer',model=configuration()['model'],notice='來源編號已驗證；回答與原文是否一致仍需人工確認。')
    except httpx.HTTPStatusError as exc:
        code=exc.response.status_code
        reasons={400:'API 請求參數不相容',401:'金鑰驗證失敗',403:'金鑰或專案權限不足',404:'設定模型已停用或不開放此帳號',429:'API 額度不足或請求過於頻繁',503:'Google 模型服務忙碌，請稍後再試'}
        reason=reasons.get(code,'Google API 服務錯誤')
        log.warning('Gemini request failed HTTP %s',code)
        return result.model_copy(update={'method':'extractive_fallback','notice':f'Gemini 未完成：{reason}（HTTP {code}）；目前顯示本機原文。'})
    except (httpx.HTTPError,ValueError,KeyError,IndexError,TypeError):
        log.warning('Gemini generation unavailable or validation failed; returning local excerpts')
        return result.model_copy(update={'method':'extractive_fallback','notice':'Gemini 暫時無法產生可驗證回答（可能為金鑰、額度、連線或格式問題），改顯示本機原文。'})
