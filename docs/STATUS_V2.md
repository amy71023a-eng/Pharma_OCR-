# 第二版完成狀態與驗證證據

2026 年 10 月 21 日，本機 Docker Desktop，Linux arm64 容器。

| 項目 | 狀態 | 證據與界線 |
| --- | --- | --- |
| Docker image | 已建置 | output/docker-build.txt、docker-start.txt |
| Compose 服務 | 已啟動 healthy | output/docker-status.txt，僅綁 127.0.0.1:8081 |
| 容器內 pytest | 23 passed，無 skip | output/docker-tests.txt，含真實 PNG/PDF OCR 與 RAG 測試 |
| 執行中服務驗收 | 通過 | output/docker-smoke.txt：health、來源回答、拒答、Word、影像/PDF CLI |
| 容器 ETL | 通過 | output/docker-etl.txt，SQLite 存 named volume |
| SOP grounded QA | 已實作 | rag.py、knowledge/sop-demo.md；字詞檢索、原文節錄、來源章節、無證據拒答 |
| 生成式 LLM RAG | 未實作 | 不呼叫生成模型，不能宣稱完成 LLM RAG；輕量擷取式問答可直接 demo |
| CI workflow | 已建立 | .github/workflows/ci.yml，Linux Docker 執行與掃描流程 |
| 遠端 GitHub Actions | 尚未執行 | 尚無目的 repository 與可用 GitHub 授權，無 run URL |
| GCP VM 部署腳本 | 已建立，語法檢查通過 | deploy/create-gcp-vm.sh、install-docker-ubuntu.sh、run-on-vm.sh |
| GCP 實際部署 | 尚未完成 | VM/計費讀取操作未獲授權，未建立任何雲端資源 |
| OCI 實際部署 | 尚未完成 | 無帳號目標、compartment 或 VM；同一套 Ubuntu Docker 腳本可用 |

第一版的 docs/RESULTS.md 是歷史驗證紀錄，當前狀態以本頁為準。基礎套件版本與第一版修補後鎖檔一致；本版未新增 Python 依賴。SBOM 與掃描仍對應 requirements.txt；未額外掃描 apt 系統套件。原始 Docker base tag 可變，建置紀錄包含當次 digest。

尚未做 Linux amd64、OCI 主機、負載/併發壓力測試，不將本機 arm64 成績推稱跨平台全數驗證。GCP x86 VM 會在其主機重新建置，應再跑 container_check 及 pytest。

## 下一步所需資訊

提供 GitHub 目的 repository URL（建議私人），即可安排推送與遠端 CI。若要 GCP，確認專案、VM 或建立方式；建議 2 vCPU、8 GiB、30 GB pd-balanced、Ubuntu 24.04。若要 OCI，提供目標 VM/區域及既有連線方式，不要貼私鑰或密碼。
