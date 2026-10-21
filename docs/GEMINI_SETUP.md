# Google Gemini 操作說明

已實作：本機關鍵字檢索 → 最多兩個來源段落 → Gemini JSON 回答 → Pydantic 與來源編號驗證 → 顯示回答及原文。沒有向量資料庫。來源編號驗證無法保證回答語意正確，仍須人工覆核。沒有足夠證據時拒答；金鑰缺失、超時、API 錯誤或不合法引用時回退本機原文。

1. 至 https://aistudio.google.com/apikey 建立 Gemini API 金鑰；確認所選專案的計費與額度。現有 GCP 專案可能已啟用計費，不能假定一定免費。請勿在聊天貼金鑰。
2. 使用 VS Code 開啟 `/Users/amy/Pharma_OCR/.env`，將 `GEMINI_API_KEY=` 的等號後填上自己的金鑰。`GEMINI_MODEL=gemini-3.1-flash-lite` 為預設，可改成帳號支援的文字模型；其他模型可能不支援目前的 thinkingBudget 設定。`.env` 不提交 Git，也不打包進 Docker 映像。
3. 終端機執行以下指令，將新環境設定帶進容器：

```sh
cd /Users/amy/Pharma_OCR
docker compose up -d --build --force-recreate
```

4. 開啟 http://127.0.0.1:8083 ，在 SOP 查詢勾選「使用 Gemini 整理」，先以示範 SOP 問「OCR 信心低於85怎麼處理」。這會傳送問題與搜尋命中的段落至 Google，不上傳原圖；取消勾選即可完全使用本機檢索。注意命中段落可能包含自行匯入的仿單，不要以未授權敏感文件測試。免費層資料可能用於改善 Google 產品，詳閱官方條款。
5. 畫面顯示「Gemini 整理」並有 S1/S2 來源才表示本次成功；「本機原文模式」和回退提示表示未完成生成。`/rag/status` 的 configured 只代表有設定金鑰，不代表驗證成功。

API：`POST /rag`，JSON 為 `{"question":"OCR 信心低於85怎麼處理","use_llm":true}`。預設 use_llm=false。

測試：`docker compose exec -T review pytest -q`。單元測試採模擬回應，無雲端費用。尚未設定金鑰前，不能宣稱真實 Gemini API 已連通；真實品質評估須用人工標註問答、引用正確率、拒答率與錯誤答案率進行，測試通過不等於醫療或法規驗證。

官方文件：https://ai.google.dev/api/generate-content 、https://ai.google.dev/gemini-api/docs/pricing 。GCP 部署另須將金鑰安全設定到 VM 的環境，這次本地修改不代表雲端已更新。
