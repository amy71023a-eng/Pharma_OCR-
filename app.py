"""批次文件審核輔助 MVP：所有輸出都必須人工覆核，禁止自動放行。"""
import argparse
import calendar
import hashlib
import json
import logging
import re
import shutil
import sqlite3
import tempfile
import uuid
from datetime import date
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field, field_validator
from PIL import Image
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output'; OUT.mkdir(exist_ok=True)
logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')
log=logging.getLogger('review')

class Result(BaseModel):
    """固定型別讓 API、ETL 與報告共用相同契約；缺值保留 null。"""
    product: str|None=None
    batch: str|None=None
    expiry: str|None=None
    full_text: str
    confidence: float|None=Field(default=None,ge=0,le=100)
    mode: Literal['text_demo','ocr']='text_demo'
    review_required: Literal[True]=True
    warnings: list[str]=Field(default_factory=list)

    @field_validator('expiry')
    @classmethod
    def valid_expiry(cls,value):
        if value is not None:
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',value): raise ValueError('效期必須為 ISO 日期')
            date.fromisoformat(value)
        return value

class TextInput(BaseModel):
    text: str=Field(min_length=1,max_length=100000)

def normalize_date(raw):
    """僅接受 ISO 年月日或年月；年月依明示規則取月底，不修補 OCR 字元。"""
    m=re.fullmatch(r'(\d{4})[-/](\d{2})(?:[-/](\d{2}))?',raw.strip())
    if not m: return None
    try:
        y,mo=int(m[1]),int(m[2]); d=int(m[3]) if m[3] else calendar.monthrange(y,mo)[1]
        return date(y,mo,d).isoformat()
    except ValueError: return None

def parse(text,confidence=None,mode='text_demo'):
    def field(labels):
        m=re.search(r'(?im)^\s*(?:'+labels+r')\s*[:：]\s*([^\n\r]+)',text)
        return m[1].strip() if m else None
    product=field('Product|品名'); batch=field('LOT|Batch|批號'); raw=field('EXP|Expiry|效期')
    expiry=normalize_date(raw) if raw else None
    warnings=[]
    for name,value in [('品名',product),('批號',batch),('效期',expiry)]:
        if value is None: warnings.append(name+'缺值或格式無法確認，請對照原圖')
    if raw and re.fullmatch(r'\d{4}[-/]\d{2}',raw): warnings.append('年月效期依示範規則換算月底，須由 SOP 確認')
    if confidence is not None and confidence<85: warnings.append('OCR 平均信心低於 85，優先人工覆核')
    if mode=='text_demo': warnings.append('文字備援模式，未執行 OCR')
    return Result(product=product,batch=batch,expiry=expiry,full_text=text,confidence=confidence,mode=mode,warnings=warnings)

def pages_for(source,folder):
    """保留原檔；PDF 轉成逐頁影像，最多十頁以限制資源。"""
    if source.suffix.lower()=='.pdf':
        from pdf2image import convert_from_path, pdfinfo_from_path
        if pdfinfo_from_path(source)['Pages']>10: raise ValueError('PDF 最多十頁')
        imgs=convert_from_path(source,dpi=150,first_page=1,last_page=10)
    else:
        with Image.open(source) as im:
            if im.width*im.height>25000000: raise ValueError('圖片超過 2500 萬像素')
            imgs=[im.convert('RGB')]
    paths=[]
    for i,im in enumerate(imgs):
        p=folder/f'page-{i+1}.png'; im.save(p); paths.append(p)
    return paths

def ocr_pages(paths,lang='eng'):
    import pytesseract
    texts=[]; scores=[]
    for p in paths:
        with Image.open(p) as im:
            data=pytesseract.image_to_data(im,lang=lang,output_type=pytesseract.Output.DICT,timeout=45)
            # 同一次 OCR 的 token 依行重組，避免全文與信心來自不同執行。
            lines={}
            for i,t in enumerate(data['text']):
                if not t.strip(): continue
                key=(data['block_num'][i],data['par_num'][i],data['line_num'][i])
                lines.setdefault(key,[]).append(t)
                if float(data['conf'][i])>=0: scores.append(float(data['conf'][i]))
            texts.append('\n'.join(' '.join(v) for v in lines.values()))
    return parse('\n\n--- PAGE ---\n\n'.join(texts),sum(scores)/len(scores) if scores else 0,'ocr')

def report(r,images,target):
    """原圖與辨識文字分頁展示；人工檢查與簽核欄永遠留白。"""
    d=Document(); sec=d.sections[0]
    sec.top_margin=sec.bottom_margin=Inches(.7)
    style=d.styles['Normal']; style.font.name='Arial'; style.font.size=Pt(11)
    style.element.rPr.rFonts.set(qn('w:eastAsia'),'Heiti TC')
    for n in ['Title','Heading 1','Heading 2']:
        d.styles[n].font.color.rgb=RGBColor(0,0,0)
        d.styles[n].element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),'Heiti TC')
        for border in list(d.styles[n].element.findall('.//'+qn('w:pBdr'))): border.getparent().remove(border)
    d.add_heading('進口醫藥產品批次文件審核輔助報告',0)
    d.add_paragraph('虛構示範文件。本報告僅整理 OCR 或輸入結果，所有欄位均待人工覆核，不構成產品放行決定或法規合規驗證。')
    d.add_heading('擷取結果',1)
    for label,v in [('品名',r.product),('批號',r.batch),('效期',r.expiry),('模式',r.mode),('平均信心',r.confidence)]:
        d.add_paragraph(f'{label}：{v if v is not None else "未辨識"}')
    for w in r.warnings: d.add_paragraph('提示：'+w)
    d.add_heading('人工覆核',1)
    d.add_paragraph('□ 品名及規格  □ 批號  □ 效期與 SOP  □ 仿單完整性\n□ 字體與版面  □ 色塊與印刷  □ 包裝與核准樣本一致性\n色塊與版面僅提示人工對照；系統未執行色差或版面合格判定。\n差異與處置：________________________________\n覆核者：________________  日期：________________\n品質單位依既有程序另行決定處置：________________')
    for i,p in enumerate(images):
        d.add_page_break(); d.add_heading(f'原圖 第 {i+1} 頁',1); d.add_picture(str(p),width=Inches(6))
    d.add_page_break(); d.add_heading('完整辨識文字',1)
    d.add_paragraph(r.full_text or '無辨識文字，不得補造內容。')
    for paragraph in d.paragraphs:
        for border in list(paragraph._p.findall('.//'+qn('w:pBdr'))): border.getparent().remove(border)
    d.save(target)

def save_etl(records,db):
    """以原始文字 SHA256 去重，SQL 參數綁定避免拼接資料。"""
    inserted=0
    with sqlite3.connect(db) as c:
        c.execute('CREATE TABLE IF NOT EXISTS batches (id TEXT PRIMARY KEY, product TEXT, batch TEXT, expiry TEXT, payload TEXT NOT NULL)')
        for r in records:
            key=hashlib.sha256(r.full_text.encode()).hexdigest()
            cur=c.execute('INSERT OR IGNORE INTO batches VALUES (?,?,?,?,?)',(key,r.product,r.batch,r.expiry,r.model_dump_json()))
            inserted+=cur.rowcount
        total,missing=c.execute('SELECT COUNT(*), COALESCE(SUM(expiry IS NULL),0) FROM batches').fetchone()
    return dict(inserted=inserted,duplicates=len(records)-inserted,total=total,missing_expiry=missing)

from rag import Query, Answer, retrieve

app=FastAPI(title='批次文件審核輔助 MVP',version='1.0.0')
@app.post('/rag',response_model=Answer)
def rag_api(body:Query):
    return retrieve(body.question)

@app.get('/health')
def health(): return {'status':'ok','tesseract':bool(shutil.which('tesseract')),'poppler':bool(shutil.which('pdftoppm'))}
@app.get('/',response_class=HTMLResponse)
def home():
    return '''<html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{padding:0 20px}textarea{width:100%;box-sizing:border-box}pre{overflow-wrap:anywhere}button{padding:8px;margin:6px 0}</style><title>批次文件審核輔助</title><body style="max-width:800px;margin:40px auto;font:18px sans-serif"><h1>批次文件審核輔助 MVP</h1><p>僅限虛構資料。所有結果待人工覆核，不自動放行。</p><h2>圖片或 PDF OCR</h2><input id="f" type="file" accept=".png,.jpg,.jpeg,.pdf"><button onclick="upload()">辨識並產生 Word</button><h2>文字備援示範</h2><textarea id="t" rows="8" cols="65">Product: DEMO MEDICINE\nLOT: DEMO2026A\nEXP: 2028/12\nDEMONSTRATION ONLY. Not for medical use.</textarea><br><button onclick="run()">產生文字備援報告</button><h2>SOP 檢索與原文回答</h2><p>回答附來源；無足夠證據就拒答。本示範採擷取式回答，未使用生成模型。</p><input id="q" value="OCR 信心低於85怎麼處理" style="width:90%"><button onclick="ask()">查詢 SOP</button><pre id="ra" style="white-space:pre-wrap"></pre><pre id="o" style="white-space:pre-wrap"></pre><div id="link"></div><script>async function ask(){let r=await fetch('/rag',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q.value})});ra.textContent=JSON.stringify(await r.json(),null,2)}async function show(r){let j=await r.json();o.textContent=JSON.stringify(j,null,2);link.innerHTML='';if(j.report_url){let a=document.createElement('a');a.href=j.report_url;a.textContent='下載 Word 報告';link.appendChild(a)}}async function run(){show(await fetch('/text',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:t.value})}))}async function upload(){let d=new FormData();d.append('file',f.files[0]);show(await fetch('/ocr',{method:'POST',body:d}))}</script></body></html>'''

def complete(r,paths,folder):
    report(r,paths,folder/'report.docx'); (folder/'result.json').write_text(r.model_dump_json(indent=2),encoding='utf-8')
    log.info('report_created job=%s mode=%s',folder.name,r.mode)
    return {'result':r.model_dump(),'report_url':f'/reports/{folder.name}'}
@app.post('/text')
def text_api(body:TextInput):
    folder=OUT/uuid.uuid4().hex; folder.mkdir()
    return complete(parse(body.text),[],folder)
@app.post('/ocr')
async def ocr_api(file:UploadFile=File(...)):
    suffix=Path(file.filename or '').suffix.lower()
    if suffix not in {'.png','.jpg','.jpeg','.pdf'}: raise HTTPException(415,'僅支援 PNG JPG PDF')
    content=await file.read(10*1024*1024+1)
    if len(content)>10*1024*1024: raise HTTPException(413,'檔案上限 10 MB')
    folder=OUT/uuid.uuid4().hex; folder.mkdir(); source=folder/('original'+suffix); source.write_bytes(content)
    try:
        paths=pages_for(source,folder)
        import os
        r=ocr_pages(paths,os.getenv('OCR_LANG','eng'))
        return complete(r,paths,folder)
    except Exception as e:
        log.exception('ocr_failed job=%s',folder.name)
        raise HTTPException(422,'OCR 失敗；請檢查檔案、Tesseract 語言包及 Poppler，或使用文字備援。') from e
@app.get('/reports/{job}')
def download(job:str):
    if not re.fullmatch('[0-9a-f]{32}',job): raise HTTPException(404)
    p=OUT/job/'report.docx'
    if not p.exists(): raise HTTPException(404)
    return FileResponse(p,filename='review-report.docx')

if __name__=='__main__':
    a=argparse.ArgumentParser(); a.add_argument('--text',type=Path); a.add_argument('--file',type=Path); a.add_argument('--lang',default='eng'); args=a.parse_args()
    folder=OUT/uuid.uuid4().hex; folder.mkdir()
    if args.file:
        source=folder/('original'+args.file.suffix.lower()); shutil.copy2(args.file,source)
        paths=pages_for(source,folder); r=ocr_pages(paths,args.lang)
    elif args.text: paths=[]; r=parse(args.text.read_text(encoding='utf-8'))
    else: a.error('請指定 --text 或 --file')
    print(json.dumps(complete(r,paths,folder),ensure_ascii=False,indent=2))
