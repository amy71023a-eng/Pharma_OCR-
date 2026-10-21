"""以同頁 OCR 文字組合品牌、規格及劑型；不含藥品名稱字典或預設答案。"""
import re

STRENGTH=re.compile(r'(?<![\w/])(\d+(?:\.\d+)?\s*(?:mcg|mg|g)(?:\s*/\s*\d+(?:\.\d+)?\s*(?:mcg|mg|g))?)(?!\w)',re.I)

def product_parts(text):
    lines=[line.strip() for line in text.splitlines() if line.strip()]
    parts={'brand':[],'strength':[],'form':[]}
    for i,line in enumerate(lines):
        if re.search(r'\b(?:mg|mcg|g)\b',line,re.I):
            for previous in reversed(lines[max(0,i-2):i]):
                m=re.fullmatch(r'[\W\d_]*([A-Za-z][A-Za-z-]{2,})[^\w]*',previous)
                if m and m[1].lower() not in {'lot','batch','exp','tablets','capsules','product'}:
                    parts['brand'].append(m[1]);break
            for m in STRENGTH.finditer(line):
                value=re.sub(r'\s*/\s*','/',m[1]);value=re.sub(r'(\d)\s*(mcg|mg|g)',r'\1 \2',value,flags=re.I)
                parts['strength'].append(value)
        for form in re.findall(r'\b(tablets|capsules)\b',line,re.I):parts['form'].append(form.lower())
    return {key:list(dict.fromkeys(values)) for key,values in parts.items()}

def product_from_attempts(attempts):
    """不同頁不混配；任一組件不唯一就不合成。附來源文字供人工追溯。"""
    bypage={};evidence=[]
    for attempt in attempts:
        page=attempt.get('page',1);parts=product_parts(attempt['text'])
        aggregate=bypage.setdefault(page,{'brand':[],'strength':[],'form':[]})
        for field,values in parts.items():
            for value in values:
                if value not in aggregate[field]:aggregate[field].append(value)
                evidence.append({'field':field,'value':value,'page':page,'source':attempt['source'],'text':attempt['text']})
    candidates=[]
    for parts in bypage.values():
        if all(len(parts[field])==1 for field in ['brand','strength','form']):
            value=' '.join(parts[field][0] for field in ['brand','strength','form'])
            if value not in candidates:candidates.append(value)
    return candidates,evidence
