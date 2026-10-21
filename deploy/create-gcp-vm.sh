#!/usr/bin/env bash
# 執行會建立計費 VM；先填環境變數並確認專案/區域與費用，不自動執行。
set -euo pipefail
: "${GCP_PROJECT:?請設定 GCP_PROJECT}"
GCP_ZONE=${GCP_ZONE:-asia-east1-b}
VM_NAME=${VM_NAME:-pharma-review-demo}
gcloud compute instances create "$VM_NAME" --project="$GCP_PROJECT" --zone="$GCP_ZONE" --machine-type=e2-standard-2 --image-family=ubuntu-2404-lts-amd64 --image-project=ubuntu-os-cloud --boot-disk-size=30GB --boot-disk-type=pd-balanced --no-service-account --no-scopes
# 不開放 8081 到網際網路；使用 SSH tunnel 試用。
printf '下一步：gcloud compute ssh %s --project=%s --zone=%s -- -L 8081:127.0.0.1:8081\n' "$VM_NAME" "$GCP_PROJECT" "$GCP_ZONE"
