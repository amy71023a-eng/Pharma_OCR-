"""容器內端到端驗收：health、RAG、文字、影像、PDF、下載與 ETL。"""
import json,urllib.request,subprocess,sys
from pathlib import Path
base='http://127.0.0.1:8080'
def request(path,payload=None):
    data=json.dumps(payload).encode() if payload else None
    req=urllib.request.Request(base+path,data=data,headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=120) as r:return json.load(r)
health=request('/health'); assert health['tesseract'] and health['poppler']
assert request('/rag',{'question':'OCR 信心低於85怎麼處理'})['sources']
assert request('/rag',{'question':'明天天氣與股市預測'})['abstained']
r=request('/text',{'text':'Product: DEMO\nLOT: A1\nEXP: 2028/01'})
with urllib.request.urlopen(base+r['report_url']) as f:assert f.read(2)==b'PK'
# 使用 CLI 走真實 OCR，pytest 另驗證 multipart API。
for name in ['box.png','sample.pdf']:
    p=subprocess.run([sys.executable,'app.py','--file','examples/'+name],check=True,capture_output=True,text=True)
    assert json.loads(p.stdout)['result']['batch']=='DEMO2026A'
print(json.dumps({'health':health,'rag':'passed','text_and_download':'passed','image_pdf_cli':'passed'},indent=2))
