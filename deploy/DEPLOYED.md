# 已完成的 GCP 部署與持續整合

部署日期：2026 年 10 月 21 日。

## 實際環境

- GCP 專案：`project-37ed6ff2-08b8-447a-8f6`
- VM：`pharma-ocr-20261021`，區域：`asia-east1-b`
- Ubuntu 24.04，x86_64，2 vCPU、8 GiB RAM、約 30 GB 磁碟
- Docker 容器健康檢查成功；VM 應用綁定 `127.0.0.1:8081`
- VM 容器內 pytest：23 passed，沒有略過；另有 httpx 未來淘汰提示
- ETL：新增 1、重複 1、總計 1、缺效期 0

完整執行紀錄已保存在交付 ZIP 的 output/gcp-deployment.txt 及 output/gcp-verification.txt，不將本機測試冒充雲端驗收。

## 從 Mac 連線

先登入有該 VM SSH 權限的 GCP 帳號，再執行下列命令，保持終端開啟：

```bash
gcloud compute ssh pharma-ocr-20261021 --project=project-37ed6ff2-08b8-447a-8f6 --zone=asia-east1-b -- -N -L 8082:127.0.0.1:8081
```

開啟 http://127.0.0.1:8082 。雖然網址顯示本機，請求會經 SSH 隧道送到 GCP 的 Docker。這與本機 Docker 的 8081 是兩套服務。沒有直接對外提供 `外部IP:8081` 公開網站。

## 維護與取回報告

```bash
gcloud compute ssh pharma-ocr-20261021 --project=project-37ed6ff2-08b8-447a-8f6 --zone=asia-east1-b
cd pharma-review
sudo docker compose ps
sudo docker compose logs --tail=100
sudo docker compose cp review:/app/output/. ./downloaded-output/
```

Word 也能在操作頁直接下載。一般停止使用 `sudo docker compose down`，不要加 `-v`，以免刪除資料卷。VM 停機與磁碟保留仍可能有費用，請自行依展示需求管理資源。

## 已成功的遠端持續整合

- 儲存庫：https://github.com/amy71023a-eng/Pharma_OCR-
- 首輪成功：https://github.com/amy71023a-eng/Pharma_OCR-/actions/runs/39557254909
- 執行提交：`0722708`
- 流程：建置 Docker → 單元與真實 OCR 整合測試 → 執行中服務驗收 → ETL → 依賴掃描 → SBOM → 驗證檔案上傳
- 驗證檔案名稱：`container-evidence`，可在該次 Actions 頁面下載。

CI 出現 action 執行環境版本淘汰警告，但整體成功，非建置失敗。OCI 按本次需求僅保留部署步驟，沒有建立 OCI 資源。知識查詢是附來源的擷取式回答，並非生成式 LLM。
