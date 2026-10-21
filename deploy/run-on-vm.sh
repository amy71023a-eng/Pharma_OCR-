#!/usr/bin/env bash
# 在已裝 Docker 的 VM 專案根目錄執行；同樣適用 GCP 或 OCI Ubuntu。
set -euo pipefail
sudo docker compose up -d --build --wait
sudo docker compose exec -T review python scripts/container_check.py
sudo docker compose logs --tail=50
