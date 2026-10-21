"""JSON/CSV → Pydantic 驗證 → SQLite → SQL 統計。"""
import argparse,csv,json
from pathlib import Path
from app import Result,save_etl

def load(path):
    if path.suffix=='.csv':
        with path.open(encoding='utf-8',newline='') as f: rows=list(csv.DictReader(f))
    else:
        rows=json.loads(path.read_text(encoding='utf-8'))
        if isinstance(rows,dict): rows=[rows]
    # 先全批驗證，再進交易，避免部分髒資料寫入。
    return [Result.model_validate({k:(v if v!='' else None) for k,v in r.items()}) for r in rows]
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('source',type=Path); p.add_argument('--db',type=Path,default=Path('output/batches.sqlite')); a=p.parse_args()
    stats=save_etl(load(a.source),a.db)
    print(json.dumps(stats,ensure_ascii=False,indent=2))
    Path('output/etl-summary.json').write_text(json.dumps(stats,indent=2))
