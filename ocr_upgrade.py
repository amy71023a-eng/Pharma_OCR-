"""原圖 OCR 加小字標籤區域重辨識，所有候選保留來源；衝突不自動裁決。"""
from PIL import Image, ImageOps, ImageFilter
import re

def read_attempt(image,lang,config,spatial=False):
    import pytesseract
    d=pytesseract.image_to_data(image,lang=lang,config=config,output_type=pytesseract.Output.DICT,timeout=30)
    tokens=[]; lines={}
    for i,t in enumerate(d['text']):
        if not t.strip(): continue
        token=dict(text=t,x=d['left'][i],y=d['top'][i],w=d['width'][i],h=d['height'][i],confidence=float(d['conf'][i]))
        tokens.append(token)
        key=(d['block_num'][i],d['par_num'][i],d['line_num'][i]);lines.setdefault(key,[]).append(t)
    if spatial:
        # 稀疏模式可能把標籤和數值拆成不同區塊，按垂直位置重建閱讀行。
        rows=[]
        for t in sorted(tokens,key=lambda t:(t['y']+t['h']/2,t['x'])):
            cy=t['y']+t['h']/2
            row=next((r for r in rows if abs(r[0]-cy)<=.8*max(r[1],t['h'])),None)
            if row is None:row=[cy,t['h'],[]];rows.append(row)
            row[2].append(t)
        text='\n'.join(' '.join(t['text'] for t in sorted(row[2],key=lambda t:t['x'])) for row in rows)
    else:text='\n'.join(' '.join(v) for v in lines.values())
    scores=[t['confidence'] for t in tokens if t['confidence']>=0]
    return text,sum(scores)/len(scores) if scores else 0,tokens

def attempts_for(image,lang,need_enhance=True):
    """最多六次辨識；不使用特定照片座標或預期字串填補。"""
    base,confidence,base_tokens=read_attempt(image,lang,'--psm 3')
    yield {'source':'original','text':base,'confidence':confidence,'box':[0,0,image.width,image.height]}
    if not need_enhance:return
    # 以辨識到的規格單位定位包裝品名區，不使用照片固定座標。
    anchors=[t for t in base_tokens if re.search(r'(?i)mg|mcg',t['text']) and t['confidence']>=30]
    if anchors:
        height=max(t['h'] for t in anchors)
        top=min(t['y'] for t in anchors);bottom=max(t['y']+t['h'] for t in anchors)
        for name,margin,desired_scale in [('product_region',2,3),('product_region_compact',1.8,2)]:
            box=[0,max(0,int(top-margin*height)),image.width,min(image.height,int(bottom+1.8*height))]
            region=ImageOps.grayscale(image.crop(box));scale=min(desired_scale,1800/region.width)
            region=region.resize((max(1,round(region.width*scale)),max(1,round(region.height*scale))),Image.Resampling.LANCZOS)
            text,c,_=read_attempt(region,'eng','--psm 6')
            yield {'source':name,'text':text,'confidence':c,'box':box}
    from app import parse
    r=parse(base,confidence,'ocr')
    if r.batch and r.expiry:return
    # 縮放設上限，避免大圖額外放大造成記憶體暴增。
    factor=min(3,1800/image.width)
    scout=image.resize((max(1,round(image.width*factor)),max(1,round(image.height*factor))),Image.Resampling.LANCZOS)
    text,c,tokens=read_attempt(scout,'eng','--psm 11',True)
    yield {'source':'sparse_search','text':text,'confidence':c,'box':[0,0,image.width,image.height]}
    labels=[t for t in tokens if re.fullmatch(r'(?i)(EXP|LOT|BATCH|SN|S/N)[:：]?',t['text']) and t['confidence']>=40]
    if len(labels)<2:return
    # 由偵測到的標籤推算區域，排除大幅背景及右側條碼干擾。
    x=min(t['x'] for t in labels)/factor;y=min(t['y'] for t in labels)/factor
    h=max(t['h'] for t in labels)/factor;bottom=max(t['y']+t['h'] for t in labels)/factor
    box=[max(0,int(x-20)),max(0,int(y-2*h)),min(image.width,int(x+.45*image.width)),min(image.height,int(bottom+h))]
    if box[2]<=box[0] or box[3]<=box[1]:return
    crop=ImageOps.grayscale(image.crop(box))
    scale=min(4,1800/crop.width)
    for name,im,psm in [('label_gray',crop,6),('label_sharp',crop.filter(ImageFilter.UnsharpMask(radius=1,percent=180,threshold=3)),11)]:
        im=im.resize((max(1,round(im.width*scale)),max(1,round(im.height*scale))),Image.Resampling.LANCZOS)
        text,c,_=read_attempt(im,'eng',f'--psm {psm} -c load_system_dawg=0 -c load_freq_dawg=0',psm==11)
        yield {'source':name,'text':text,'confidence':c,'box':box}
