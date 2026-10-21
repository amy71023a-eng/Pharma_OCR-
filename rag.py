"""輕量 grounded QA：字詞檢索加原文節錄，不呼叫 LLM、不編造答案。"""
from pathlib import Path
import re
from pydantic import BaseModel,Field

class Query(BaseModel):
    question:str=Field(min_length=2,max_length=500)
class Citation(BaseModel):
    source:str
    section:str
    excerpt:str
    score:float
class Answer(BaseModel):
    answer:str
    abstained:bool
    sources:list[Citation]
    method:str='lexical_retrieval_with_extractive_answer'

def tokens(text):
    """英文單詞加中文二字組，避免繁體中文沒有空格造成檢索失效。"""
    latin=set(re.findall(r'[a-z0-9]+',text.lower()))
    for segment in re.findall(r'[\u4e00-\u9fff]+',text):
        latin.update(segment[i:i+2] for i in range(len(segment)-1))
    return latin

def retrieve(question,folder=None):
    folder=folder or Path(__file__).parent/'knowledge'
    q=tokens(question);hits=[]
    for path in sorted(folder.glob('*.md')):
        for part in path.read_text(encoding='utf-8').split('## ')[1:]:
            heading,_,body=part.partition('\n'); body=body.strip()
            overlap=q & tokens(heading+' '+body)
            # 至少兩個不同字詞匹配，且有足夠問題字詞涵蓋率，否則拒答。
            score=len(overlap)/len(q) if q else 0
            if len(overlap)>=2 and score>=.25:
                hits.append(Citation(source=path.name,section=heading.strip(),excerpt=body,score=round(score,3)))
    hits=sorted(hits,key=lambda h:(-h.score,h.source,h.section))[:2]
    if not hits:return Answer(answer='提供的示範知識文件沒有足夠證據，無法回答，請由人工確認。',abstained=True,sources=[])
    return Answer(answer='依文件原文節錄，供人工查閱：\n'+'\n'.join(h.excerpt for h in hits),abstained=False,sources=hits)
