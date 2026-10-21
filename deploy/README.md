# Docker 本機與雲端執行

## 本機 Mac

Docker Desktop 要處於啟動狀態。以 VS Code 開啟解壓後的專案資料夾：

```bash
docker compose up -d --build --wait
```

開啟 http://127.0.0.1:8081 。容器提供 Python、OCR、繁體中文語言包、Poppler、Word 及 RAG，主機不必安裝 Python 套件。預設 8081 避免舊的 8080 本機程式衝突。

```bash
docker compose exec -T review python -m pytest -v
docker compose exec -T review python scripts/container_check.py
docker compose exec -T review python etl.py examples/records.json --db output/demo.sqlite
docker compose logs --tail=100
docker compose ps
```

測試、OCR、RAG 及 ETL 都在 Linux 容器內執行。`docker compose cp review:/app/output/. ./downloaded-output/` 取回產生的 Word 與 JSON。`docker compose down` 停止示範，命名 volume 保留資料；`down -v` 會刪掉資料，不要把它當一般停止命令。

## GCP VM 起始規格

建議 e2-standard-2（2 vCPU、8 GiB 記憶體）、30 GB pd-balanced、Ubuntu 24.04 LTS x86_64、asia-east1-b。無需 GPU。本建議適合低量功能示範，尚未做壓力測試；Docker 建置、影像及套件會占用磁碟，資料增長需監控。

目前 SQLite 與 Word 使用本機持久 volume，單台 VM 最容易重現。Cloud Run 不需要 VM，但應先把資料移到物件儲存及外部資料庫，不能直接把現有 SQLite 當成持久儲存。

建立 VM 是計費操作；腳本不會自動執行。確認計費、配額、Compute Engine API 及權限後：

```bash
export GCP_PROJECT=你的專案ID
bash deploy/create-gcp-vm.sh
```

也可在 Console 建立上述規格，不必交付任何金鑰。不要勾選對全網開放 HTTP/HTTPS，應用只綁定 VM 的 loopback。

將 ZIP 上傳到 VM：

```bash
gcloud compute scp ../pharma-review-docker-v2.zip pharma-review-demo:~/ --project="$GCP_PROJECT" --zone=asia-east1-b
gcloud compute ssh pharma-review-demo --project="$GCP_PROJECT" --zone=asia-east1-b
```

進入 VM 後解壓，安裝 Docker，啟動：

```bash
sudo apt-get update
sudo apt-get install -y unzip
unzip pharma-review-docker-v2.zip
cd pharma-review
bash deploy/install-docker-ubuntu.sh
bash deploy/run-on-vm.sh
```

Mac 另開終端建立隧道：

```bash
gcloud compute ssh pharma-review-demo --project="$GCP_PROJECT" --zone=asia-east1-b -- -L 8081:127.0.0.1:8081
```

Mac 開 http://127.0.0.1:8081 。若本機容器已佔用 8081，將 `-L` 的第一個埠改成 8082，瀏覽 8082。SSH 仍需既有 IAM、網路及防火牆允許；組織若採 IAP，依管理政策使用 IAP tunnel，不新增全網應用連接埠。

示範結束可在 Console 停機；磁碟與其他保留資源仍可能計費，刪除前先備份 Word。此專案不自動刪除雲端資源。

## OCI 路徑

相同 ZIP、Dockerfile、run-on-vm.sh 可在 OCI Ubuntu 24.04 VM 執行。建議 x86 shape 提供 2 vCPU、8 GB RAM、至少 30 GB 磁碟；若 Console 的最小 boot volume 較大，保留其最小值，勿假設免費額度。OCPU 與 vCPU 的關係依架構/shape 確認。先建立 VM、以 SSH 上傳 ZIP，再執行相同安裝及啟動腳本；以 `ssh -L 8082:127.0.0.1:8081 <既有SSH連線設定>` 試用。容器沒有雲端相依，GCP 與 OCI 不需要改程式。

OCI 帳號、compartment、網路及目標 VM 尚未提供，因此沒有宣稱已部署。若要 Container Instances，還需 OCIR 映像、VCN、IAM 及外部持久儲存設計，不能把 Docker Compose 命名 volume 直接搬成多副本服務。

## GitHub 遠端 CI

將本資料夾內容放在 GitHub repository 根目錄（必須能看見 `.github/workflows/ci.yml`）。推送後 Actions 自動建置 Linux Docker、跑 pytest、OCR/RAG/ETL 驗收、依賴掃描及 SBOM，並上傳證據。也支援 Actions → docker-ocr-rag-ci → Run workflow。

尚未提供目的 repository 與可用登入，因此遠端執行需連接 GitHub 後才能完成。本機 Docker 執行成功不冒充 Actions 成功。

## 來源

- Docker 官方安裝：https://docs.docker.com/engine/install/ubuntu/
- GCP E2 規格：https://docs.cloud.google.com/compute/docs/general-purpose-machines
- GitHub workflow：https://docs.github.com/en/actions/concepts/workflows-and-actions/workflows
- OCI：https://docs.oracle.com/en-us/iaas/Content/container-instances/overview-of-container-instances.htm
