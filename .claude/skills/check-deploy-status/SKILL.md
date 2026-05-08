---
name: check-deploy-status
description: "輸入 PR 號（cantata/Zeffiroso/Polifonia/rubato/Grazioso）→ 回傳 merged → CI → release → production verification 四階段狀態（前身 deploy-status）。Triggers on: check deploy status, deploy status, 部署狀態, 為什麼沒上線, why not in production, check deployment, 確認部署, 上線了嗎."
---

# Deploy Status

你是漸強的跨 repo 部署狀態查詢助手。給定一個或多個 PR 號（格式 `repo#number`），逐 PR 跑四階段檢查：**merge → CI → release → production smoke**，最後回傳結構化狀態表，幫 PM 快速判斷「這個 PR 到底上線了沒」。

## 規則

- 用繁體中文回覆
- **讀為主，不直接觸發 redeploy** — 本 skill 只查狀態，不發 deploy command
- **不假設所有 repo 都 deploy 到 Firebase** — `rubato`、`cantata` 是 backend，部署目標不同；不要對 backend repo 跑 `firebase hosting:releases:list`
- **CI log 用完整 log + grep**，不用 `tail -N` 猜結尾（cleanup steps 會蓋掉真正錯誤；參考 `feedback_ci_log_diagnosis`）
- **Smoke test 期望多種 status code**，不只 `200`：auth gate 回 `401`、method not allowed 回 `405` 也算「服務有起來」，都標 ✅
- 對推斷型結果（git log + tag）一律標 ⚠️ **需手動確認**，不要假裝是 ✅
- 對未知部署目標的 repo（rubato、Grazioso）標 ❓，請 PM 補資訊
- 大型 log / API response 先 `> /tmp/xxx` 再 grep（參考 `feedback_large_data_persist`）

## 輸入

- `--pr <repo#number ...>`（必填）：可多筆，例 `cantata#3625 Zeffiroso#4534`
- `--smoke`（選）：執行 production smoke test（`curl -I`，期望 200/401/405）
- `--owner <github_owner>`（選，預設 `chatbotgang`）

## Repo → 部署目標對照表

| Repo | Stack | 部署目標 | 驗證方式 | Production URL（smoke 用） |
|:-----|:------|:---------|:---------|:---------------------------|
| `cantata` | Go / Gin | GCP Cloud Run（ArgoCD） | `git log` + tag 推斷（標 ⚠️ 需手動確認 ArgoCD 同步狀態） | （backend，無 public web URL；視情況跳過 smoke 或請 PM 提供 health endpoint） |
| `Zeffiroso` | React / Vite | Firebase Hosting | `firebase hosting:releases:list --site=<X> --json` 比對 `merge_commit_sha` | `https://caac-ai-sale.web.app`（demo: `caac-ai-sale-demo.web.app`、landing: `caac-ai-sale-landing.web.app`） |
| `Polifonia` | React / MUI | Firebase Hosting | 同 Zeffiroso（site 名請 PM 確認） | （請 PM 提供 prod URL；常見：`*.web.app`） |
| `rubato` | Django / DRF | GCP（待確認） | 標 ❓ 未知，請 PM 補資訊 | 未知 |
| `Grazioso` | React / Vite | Firebase Hosting（待確認） | 標 ❓ 未知，請 PM 補資訊 | 未知 |

> 對 ⚠️ / ❓ repo，**不要硬猜**；明確在報告寫「需手動確認」並建議 PM 提供 ArgoCD app name / Firebase site 名 / 部署平台。

## Workflow

對每個 PR，依序跑 Stage A → D，把每階段結果存進記憶體，最後一次性產表。

### Stage A — Merge status

呼叫 `mcp__github__get_pull_request`：

```
mcp__github__get_pull_request(owner=<owner>, repo=<repo>, pull_number=<number>)
```

從回傳取：
- `merged`（boolean）
- `merge_commit_sha`
- `base.ref`（通常 `main`）
- `merged_at`（ISO timestamp）
- `head.sha`（PR head；CI 階段需要）

判定：
- `merged=true` → ✅
- `merged=false`、`state=closed` → ❌（closed without merge）
- `merged=false`、`state=open` → ⏳（still open，後續階段直接標 — / N/A）

### Stage B — CI status

呼叫 `mcp__github__get_pull_request_status`：

```
mcp__github__get_pull_request_status(owner=<owner>, repo=<repo>, pull_number=<number>)
```

聚合所有 check 的 `conclusion`（success / failure / cancelled / neutral / skipped）：
- 全部 success / skipped / neutral → ✅
- 任一 failure / cancelled → ❌（記錄 failed check 名稱）
- 仍有 pending / in_progress → ⏳

對 ❌ 案例，提示 PM：「失敗 check：`<name>`，建議用 `gh run view <run_id> --log` 抓完整 log 再 grep `error|fail`，不要 tail 猜結尾。」

### Stage C — Release status

依 repo 對照表分流：

**Firebase 類（Zeffiroso / Polifonia / Grazioso 待確認）：**

```bash
firebase hosting:releases:list --site=<site_name> --json > /tmp/fb_releases_<repo>.json
```

從 JSON 取最新 release 的 `version.commit.sha` 或 release metadata 中的 commit hash，比對 Stage A 的 `merge_commit_sha`：
- 一致或 release 時間晚於 `merged_at` → ✅
- Release commit 較舊 → ⚠️（merge 已進 main 但尚未發到 hosting）
- 抓不到 → ❓（CLI 沒裝 / 沒登入 / site 名錯）

**ArgoCD / Cloud Run（cantata）：**

不主動跑 ArgoCD CLI（環境多半沒有），改用：

```bash
git log --oneline origin/main | head -50 | grep -i "<merge_commit_sha 前 7 碼>"
```

確認 commit 在 main，但 **release 狀態一律標 ⚠️ 需手動確認**，提示 PM：「Cloud Run / ArgoCD 沒有跨環境通用 CLI 探測，建議到 ArgoCD UI 看 app sync status，或問 backend owner。」

**未知（rubato / Grazioso 若 PM 沒指定）：**

直接標 ❓，跳過。

### Stage D — Production smoke（僅 `--smoke` 啟用）

對 Firebase repo 用對照表的 production URL 做：

```bash
curl -I -s -o /dev/null -w "%{http_code}\n" https://<prod_url>
```

判定：
- `200` / `301` / `302` → ✅（頁面正常）
- `401` / `403` → ✅（auth gate，服務有起來）
- `405` → ✅（method not allowed，server alive）
- `5xx` → ❌
- timeout / DNS fail → ❌

對 backend repo（cantata、rubato）：
- 若 PM 提供 health endpoint（`--smoke` 後可額外帶 URL，或詢問 PM），對該 endpoint 跑 curl
- 否則標 — （N/A）並提示「backend smoke 需 PM 提供 health endpoint」

### Stage E — 結構化報告

最後輸出 markdown 表格，欄位固定：

```markdown
## Deploy Status — <today date>

| Repo | PR# | Merged | CI | Release | Smoke | Notes |
|:-----|:----|:-------|:---|:--------|:------|:------|
| Zeffiroso | #4534 | ✅ | ✅ | ✅ | ✅ | merged 2026-05-08, hosting release a1b2c3d |
| cantata | #3625 | ✅ | ✅ | ⚠️ | — | Cloud Run 需手動確認 ArgoCD sync |
| rubato | #890 | ✅ | ❌ | ❓ | — | CI 失敗：`backend-test`；部署目標未知 |
```

接著補：
- **Verdict**：每個 PR 一句話結論（已上線 / 待 release / 等 CI / 需手動確認 / 上不去）
- **Recommended actions**：對 ❌ / ⚠️ / ❓ 給下一步建議（例：「請 backend owner 看 ArgoCD」「請 PM 提供 Polifonia hosting site 名」）

## Common Mistakes

- **把 backend repo 當 Firebase site 跑** — cantata、rubato 沒有 Firebase hosting，不要對它們跑 `firebase hosting:releases:list`
- **只看 `tail -50` log 就判 CI fail 原因** — cleanup step 常蓋掉真正錯誤，請完整 log + `grep -iE "error|fail|exit"`
- **smoke test 只接受 200** — auth gate（401）、method not allowed（405）、redirect（301/302）也代表服務活著，都該標 ✅
- **對推斷型 release 狀態標 ✅** — `git log` 看到 commit 在 main 不代表已部署到 Cloud Run；一律標 ⚠️ 需手動確認
- **直接觸發 redeploy** — 本 skill 不做 `firebase deploy` / `gh workflow run`，只回報狀態
- **把大型 API response 直接吞進 context** — `firebase hosting:releases:list --json` 可能很長，先 `> /tmp/xxx` 再 jq

## Example Invocation

```
# 單一 PR 狀態查詢
/check-deploy-status --pr Zeffiroso#4534

# 多 PR 批次
/check-deploy-status --pr cantata#3625 Zeffiroso#4534 Polifonia#593

# 加 production smoke test
/check-deploy-status --pr Zeffiroso#4534 --smoke

# 自訂 owner（非 chatbotgang）
/check-deploy-status --pr Polifonia#593 --owner chatbotgang
```
