"""評估工具不生成 ground truth；標註與預測需各自提供，禁止用預測反填標註。"""
import argparse,json
from pathlib import Path

def distance(a,b):
    row=list(range(len(b)+1))
    for i,x in enumerate(a,1):
        nxt=[i]
        for j,y in enumerate(b,1): nxt.append(min(nxt[-1]+1,row[j]+1,row[j-1]+(x!=y)))
        row=nxt
    return row[-1]

def evaluate(truth,pred):
    correct=predicted=expected=total=edits=chars=0
    for key,t in truth.items():
        p=pred.get(key,{})
        for f in ['product','batch','expiry']:
            tv,pv=t.get(f),p.get(f); total+=1
            correct+=int(tv==pv and tv is not None)
            predicted+=int(pv is not None); expected+=int(tv is not None)
        edits+=distance(t.get('full_text',''),p.get('full_text','')); chars+=len(t.get('full_text',''))
    return {'samples':len(truth),'field_accuracy':correct/total if total else 0,'precision':correct/predicted if predicted else 0,'recall':correct/expected if expected else 0,'CER':edits/chars if chars else None,'note':'僅限此資料集，並非真實文件效能保證'}
if __name__=='__main__':
    a=argparse.ArgumentParser(); a.add_argument('truth'); a.add_argument('predictions'); s=a.parse_args()
    print(json.dumps(evaluate(json.loads(Path(s.truth).read_text()),json.loads(Path(s.predictions).read_text())),ensure_ascii=False,indent=2))
