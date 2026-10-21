# 實際執行紀錄

測試日期：2026 年 10 月 21 日，Mac arm64、Python 3.12.14、Tesseract 5.5.3。檔案以實際執行產生，不把計畫當成果。

## 已確認

- 先建立 TEST_PLAN 及核心測試，再實作 app。
- 19 項 pytest 通過，含 16 項核心/契約測試、3 項真實 OCR/API 整合測試，無 skip。TestClient 有 httpx 未來淘汰警告，沒有影響本次通過。
- 真實英文 PNG 與兩頁 PDF 經 Tesseract + Poppler 處理成功，品名 DEMO MEDICINE、批號 DEMO2026A、效期 2028-12-31；PDF 仿單全文保留。
- Word 兩份示範各四頁，已轉圖逐頁檢視，修復原環境中文缺字及標題殘留邊框問題。報告保留原圖、全文、人工覆核提示及留白簽核欄。
- JSON 首次匯入 1 筆、重複 1 筆；同資料 CSV 重送為新增 0、重複 1；總筆數 1、缺效期 0，見 etl-evidence.json。
- 套件鎖定後另建乾淨 venv，成功安裝並重新跑測試；pip check 見 output/pip-check.txt。
- pip-audit 首輪發現 Pillow、pip 漏洞，升級 Pillow 13.0.0、pip 26.2.2 後重掃沒有已知漏洞；以 output/audit.json 為證。此結果不等於零風險。
- CycloneDX SBOM 已產生，見 output/sbom.cdx.json。
- 本機瀏覽器實際按文字備援按鈕，顯示結果及 Word 下載連結；PNG/PDF 上傳及下載則透過真實 API 整合測試確認。

## OCR 評估界線

合成樣本 1 組的三欄完全一致：field accuracy、precision、recall 均為 1.0。原始全文 CER 約 0.0465，這個數字包含系統插入的 PAGE 分隔符及換行差異，不應解讀成純 OCR 錯字率。平均 token 信心約 95.49，非校準機率。ground truth 是生成合成影像時的已知標籤，已對照樣本可視內容，並非外部人工雙人盲測。正式評估需要獨立人工標註集，固定分隔符/空白正規化規則後再報告 CER。

## 尚未完成的驗證及功能

繁體中文語言包 OCR 尚未執行；目前只驗證英文合成文件。人工驗收清單尚待使用者實際在 Word 勾選及覆核，沒有代填簽名。未建置 Docker、未上傳 GitHub 執行遠端 Actions、未部署 GCP/OCI。RAG、LLM、產品主檔、法規驗證、電子簽章與實務文件品質驗證未實作。

環境限制與替代：原先無 FastAPI 及 Tesseract，已安裝完成；曾遇網路/本機監聽限制，經授權後已可用。PDF 引擎目前使用工作環境附帶 Poppler，使用者乾淨 Mac 需依 README 安裝 poppler。即使 OCR 安裝未就緒，文字備援與附帶 Word 仍可展示。
