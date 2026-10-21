> 第二版實際 Docker 操作與 VM 腳本見 deploy/README.md；本頁保留雲端概念與排查參考。

# Linux 排查與雲端部署規劃

此文件為概念設計，沒有實際部署至 GCP 或 OCI。

## 本機及 Linux

`curl -f http://127.0.0.1:8080/health`：檢查 API 活著及是否能找到外部工具；status ok 並不保證 OCR 語言包可用。
`tesseract --list-langs`：確認語言包；中文用 `OCR_LANG=chi_tra+eng`。
`pdftoppm -v`：確認 PDF 轉圖工具。
`docker compose logs --tail=100 review`：找出工作 UUID 及例外堆疊，log 不主動輸出全文。
`docker compose ps`：查看容器及 health；`df -h` 查空間，`free -m` 查 Linux 記憶體。

錯誤 422：檢查副檔名與實際格式、加密 PDF、引擎安裝、語言包。錯誤 413：檔案超過 10 MB。PDF 超過十頁、圖片超過 2500 萬像素也拒絕。
Port 已佔用：改用 `--port 8081`。Permission denied：確認 output 對目前使用者可寫。PDF OOM：降低 DPI、拆頁，正式環境改背景工作佇列。Tesseract timeout：單頁限制 45 秒，檢查影像與語言。
本機只綁定 127.0.0.1；此 MVP 沒有登入或租戶隔離，不宜公開暴露。容器暫存原圖無自動清理，僅用合成資料，示範後自行管理 output 保存期限。

## GCP 規劃

映像建置 → Artifact Registry → Cloud Run（指定 container port 8080）→ Cloud Logging。入口需 IAM 驗證，限制上傳、CPU、記憶體及併發。Cloud Run 本機檔案不持久；正式版原圖/Word 存 GCS、結果存 Cloud SQL，下載改簽署連結。長 OCR 工作以 Cloud Tasks 或 Pub/Sub 配背景 worker，API 回傳 job id。服務帳號採最小權限、Secret Manager 管理憑證；費用、區域、資料保存政策需另行審核。

官方契約：https://docs.cloud.google.com/run/docs/container-contract

## OCI 規劃

映像推至 OCIR → Container Instances 或 Compute 上 Docker → OCI Logging；原圖存 Object Storage，資料庫另選 managed PostgreSQL 或合適資料服務。設定 VCN、受限 ingress、IAM policies、Vault 與可觀測性；避免把 SQLite 放在可水平擴充且不共享的容器磁碟。

官方介紹：https://docs.oracle.com/en-us/iaas/Content/container-instances/overview-of-container-instances.htm

## 供應鏈

`python -m pip_audit -r requirements.txt -f json -o output/audit.json`：比對公開漏洞，需網路；無發現不代表安全保證。
`cyclonedx-py requirements requirements.txt -o output/sbom.cdx.json`：生成依賴清單。SBOM 不是掃描通過證書。
`requirements.txt` 鎖定整個專案依賴閉包；`requirements.in` 記錄直接需求。升級後必須重新解析鎖檔、測試及掃描。Docker 基底標籤仍可變，正式建置應另鎖 digest，CI action 亦應鎖 commit SHA。
