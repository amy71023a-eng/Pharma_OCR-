# 第二版 Docker 快速啟動

在解壓後的 pharma-review 資料夾執行：

```bash
docker compose up -d --build --wait
```

開啟 http://127.0.0.1:8081 ，上傳 examples/sample.pdf 產生 Word，也可在下方詢問 SOP。無答案時會拒答。所有 OCR 及 Word 工具都已封裝，不用另裝 Python 或 Tesseract。

```bash
docker compose exec -T review python -m pytest -v
docker compose exec -T review python scripts/container_check.py
docker compose logs --tail=100
docker compose cp review:/app/output/. ./downloaded-output/
docker compose down
```

依序為測試、端到端驗收、查看日誌、下載報告及停止服務。停止後 volume 保留資料。完整 GCP/OCI VM 與遠端 CI 步驟見 deploy/README.md；實際完成狀態見 docs/STATUS_V2.md。

MVP 是 Minimum Viable Product，最小可行產品：核心流程已能使用和測試，還不是正式上線或完成合規驗證的產品。

以下保留不使用 Docker 的第一版備援步驟：

# 本機快速操作

本機網站若仍運行，開啟 http://127.0.0.1:8080 。

解壓 ZIP，以 VS Code 開啟 pharma-review 資料夾：

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn app:app --host 127.0.0.1 --port 8080
```

打開網址後：
1. 先用「產生文字備援報告」確認可下載 Word。
2. 已安裝 Tesseract 與 Poppler 時，選 examples/sample.pdf，再按辨識。
3. 開 Word 展示原圖、擷取欄位、仿單全文與人工覆核欄。
4. 跑 `python etl.py examples/records.json --db output/demo.sqlite` 展示 SQL 統計。
5. 跑 `python -m pytest -v` 展示測試；無 OCR 引擎時整合測試會 skip。


直接展示檔案：output/sample-ocr-review.docx 為真正 PDF OCR，output/sample-review.docx 為已知文字備援。不要把文字備援當成 OCR 成果。僅限虛構資料；最終處置依既有品質程序由人工決定。
