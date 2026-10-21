"""僅在乾淨 venv 安裝 requirements.in 後執行，以鎖定含 extras 的全部傳遞依賴。"""
import subprocess,sys
from pathlib import Path
# 若環境還裝了其他專案套件，也會被記錄；故請務必使用專用乾淨 venv。
Path('requirements.txt').write_text(subprocess.check_output([sys.executable,'-m','pip','freeze','--all'],text=True))
