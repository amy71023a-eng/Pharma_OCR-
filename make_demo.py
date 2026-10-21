"""自行生成無敏感資料的外盒與仿單影像、PDF 以及明確標示的文字備援報告。"""
import json,csv
from PIL import Image,ImageDraw,ImageFont
from app import ROOT,OUT,parse,report,Result
E=ROOT/'examples'; E.mkdir(exist_ok=True)
text='Product: DEMO MEDICINE\nLOT: DEMO2026A\nEXP: 2028/12\nDEMONSTRATION ONLY\nNot for medical use.'
leaflet='DEMONSTRATION LEAFLET\nThis is fictional demonstration material.\nNo therapeutic indication or dosage is provided.\nStore and handle according to a verified SOP.\nReview all text against the approved reference.'
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',32) if __import__('sys').platform=='darwin' else ImageFont.truetype('DejaVuSans.ttf',32)
paths=[]
for name,content in [('box',text),('leaflet',leaflet)]:
    im=Image.new('RGB',(1200,700),'white'); d=ImageDraw.Draw(im)
    d.rectangle((30,30,1170,80),fill='#286a91'); d.multiline_text((60,120),content,font=font,fill='black',spacing=20)
    p=E/f'{name}.png'; im.save(p); paths.append(p)
Image.open(paths[0]).save(E/'sample.pdf',save_all=True,append_images=[Image.open(paths[1])],resolution=150)
full=text+'\n\n'+leaflet
(E/'sample.txt').write_text(full,encoding='utf-8')
r=parse(full); report(r,paths,OUT/'sample-review.docx')
(OUT/'sample-result.json').write_text(r.model_dump_json(indent=2),encoding='utf-8')
(E/'records.json').write_text(json.dumps([r.model_dump(),r.model_dump()],ensure_ascii=False,indent=2),encoding='utf-8')
with (E/'records.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['product','batch','expiry','full_text']);w.writeheader();w.writerow({k:r.model_dump()[k] for k in w.fieldnames})
# 以產生影像時使用的已知標籤作為合成資料 ground truth，非真實人工盲測。
(E/'ground_truth.json').write_text(json.dumps({'sample':{'product':'DEMO MEDICINE','batch':'DEMO2026A','expiry':'2028-12-31','full_text':full}},indent=2))
(ROOT/'schema.json').write_text(json.dumps(Result.model_json_schema(),ensure_ascii=False,indent=2),encoding='utf-8')
