# 進口醫藥產品批次外盒與仿單 OCR 審核輔助系統

這是一個功能展示用 Python MVP，將研發及 QA 文件覆核經驗轉成可執行工具。使用虛構外盒與仿單，可上傳圖片或多頁 PDF，擷取品名、批號、效期及全文，下載附原圖與人工覆核欄的 Word。所有結果待人工覆核；不自動決定放行、不驗證法規合規。

## 第二版 Docker 與知識檢索

建議現在使用 Docker 啟動，不必在 Mac 安裝 Python 套件或 OCR 工具：

```bash
docker compose up -d --build --wait
```

開啟 http://127.0.0.1:8081 。操作頁新增 SOP 檢索，回答引用檔名、章節及原文；查不到就拒答。此版採字詞檢索與擷取式回答，不呼叫 LLM，也不假稱完成生成模型整合。

完整雲端 VM 建立、SSH 隧道、Docker 安裝與 GitHub CI 步驟請先看 [部署指南](deploy/README.md)。驗證狀態見 `docs/STATUS_V2.md`，以下第一版紀錄中的「Docker 未執行」「RAG 未實作」已由第二版更新；GCP/OCI 實際部署及遠端 Actions 仍須目標帳號/儲存庫與授權。

## 最短啟動 Mac 與 VS Code

下載 ZIP 解壓，在 VS Code 開啟 `pharma-review` 資料夾，以 Terminal 執行：

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn app:app --host 127.0.0.1 --port 8080
```

`venv` 隔離套件，避免改到其他專案；`requirements.txt` 鎖定版本；uvicorn 啟動 FastAPI 網站及 API。建議 Python 3.12，若尚未安裝可用 `brew install python@3.12`。在 VS Code 的 Python interpreter 選 `.venv/bin/python`。

瀏覽 http://127.0.0.1:8080 ，先按「產生文字備援報告」確認流程，再下載 Word。此模式沒有 OCR，畫面與報告都會明示。`/docs` 是可互動 API 文件，`/health` 檢查程序及工具路徑。

## 啟用真正 OCR

另開終端執行：

```bash
brew install tesseract poppler
# 需繁體中文文件再安裝，套件較大
brew install tesseract-lang
```

Tesseract 把影像變成文字；Poppler 把 PDF 每頁轉圖。英文範例用預設 `eng`；中文啟動方式為 `OCR_LANG=chi_tra+eng python -m uvicorn app:app --host 127.0.0.1 --port 8080`。範例英文是為了讓乾淨環境只裝基本引擎也能重現；程式註解、操作及報告為繁體中文。

上傳 `examples/sample.pdf`（兩頁外盒及仿單），或 `examples/box.png`。點辨識、查看 JSON 與提示、下載 Word。Word 的擷取結果、逐頁原圖與全文分開展示，勾選欄與覆核簽名留空。人工須拿核准樣本對照版面、字體及色塊；系統不量測色差，也不判定版面合格。

也可用 CLI，適合功能展示時快速演示：

```bash
python app.py --file examples/sample.pdf
python app.py --file examples/box.png --lang eng
python app.py --text examples/sample.txt
```

每次工作存到 `output/<UUID>/`，包含原始上傳檔、轉圖、`result.json` 與 `report.docx`。文字備援沒有上傳原圖；預先附的 `output/sample-review.docx` 是已知文字搭配合成原圖，`output/sample-ocr-review.docx` 才是實際 PDF OCR 結果。

## ETL 操作及意義

```bash
python etl.py examples/records.json --db output/demo.sqlite
python etl.py examples/records.csv --db output/demo.sqlite
```

JSON/CSV Extract → Pydantic 驗證 Transform → SQLite Load。JSON 含同一份資料兩次，乾淨資料庫第一次預期 inserted=1、duplicates=1；再次執行全部算重送。以全文 SHA256 去重，不把同批號差異文件直接丟棄。CLI 印出本次新增、重複、資料庫總筆數及缺效期數，也保存 `output/etl-summary.json`。

```sql
SELECT COUNT(*) AS total, SUM(expiry IS NULL) AS missing_expiry FROM batches;
SELECT product, COUNT(*) AS documents FROM batches GROUP BY product;
SELECT batch, COUNT(*) FROM batches GROUP BY batch HAVING COUNT(*) > 1;
```

這些 SQL 分別檢查完整性、產品分布及同批號多版本線索，不等同業務核准或放行。可用 VS Code SQLite extension 或 Python sqlite3 查詢。

## 測試與評估

```bash
python -m pytest -v --junitxml=output/junit.xml
python evaluate.py examples/ground_truth.json output/ocr-predictions.json
```

pytest 驗證解析、日期、閏年、缺值、重複、OCR 失敗、報告圖片、CSV、API 與真實 OCR 整合；外部工具缺少時整合測試會標示 skip。測試不是藥品系統驗證文件。詳見 `docs/TEST_PLAN.md`、當次執行 `output/tests.txt`、`output/junit.xml` 及 `docs/RESULTS.md`。

評估工具比較獨立標註與預測，計算欄位準確率、precision/recall、全文 CER。附的 ground truth 是生成合成影像時已知的標籤，尚不是多人人工標註的實務資料集。正式評估須人工逐頁轉錄、雙人處理歧異、凍結盲測集。不得以單一乾淨樣本成績推估真實文件。所有資料即使高信心也要人工覆核。

## 容器與供應鏈

```bash
docker compose up --build
python -m pip_audit -r requirements.txt -f json -o output/audit.json
cyclonedx-py requirements requirements.txt -o output/sbom.cdx.json
```

Docker 封裝 Python、OCR 與 PDF 工具，Compose 保存 output volume。掃描會查已知漏洞；SBOM 列出依賴。需要網路。`.github/workflows/ci.yml` 在上傳 GitHub 後觸發測試、範例 OCR、掃描與證據上傳；本交付已有本機 Docker 建置與執行紀錄，尚無遠端 CI 執行紀錄。

`docs/DEPLOYMENT.md` 有 Linux 排查、log、health 及 GCP/OCI 部署設計。雲端設計參考官方 [Cloud Run 容器契約](https://docs.cloud.google.com/run/docs/container-contract) 與 [OCI Container Instances](https://docs.oracle.com/en-us/iaas/Content/container-instances/overview-of-container-instances.htm)，並未實際部署。

## 專案導覽與已知限制

- `app.py`：資料契約、OCR、解析、Word、FastAPI、CLI；繁體中文註解解釋決策。
- `etl.py`、`evaluate.py`：資料匯入與獨立評估。
- `schema.json`：Pydantic 產生的 JSON Schema，不是 LLM 已部署的聲明。
- `examples/`：自行生成的虛構外盒、仿單、PDF、JSON/CSV 及標籤。
- `docs/ARCHITECTURE.md`：架構圖及設計取捨。
- `output/`：實際報告、測試、SQL 摘要、掃描及 SBOM。

規則只認行首標籤及冒號；未標示欄位不猜測。年月效期依示範規則轉月底，仍須 SOP 確認。不支援手寫辨識保證、加密 PDF、跨文件自動配對、核准主檔或版面/色差合格判定。單頁 OCR 有 45 秒 timeout；PDF 最多十頁、上傳最多 10 MB。

MVP 已實作 OCR → Word → 測試 → ETL 與附來源的擷取式 SOP 檢索。生成式 LLM、登入/權限、電子簽章、版本化審核軌跡及雲端部署尚未實作。沒有自動放行及合規認證。僅使用虛構資料在本機展示；清理與保存期限需自行管理。

## 三分鐘功能展示展示順序

1. 開操作頁，上傳兩頁 sample.pdf，說明原始證據、OCR 與結構化欄位。
2. 下載 Word，展示原圖、全文與人工覆核欄，解釋不代替 QA 決策。
3. 執行 ETL 兩次，展示去重及 SQL；打開測試結果及架構圖，依專案應用方向使用說明。
