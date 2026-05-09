---
name: run-launch-retro
description: "Post-launch retrospective —— launch 後 N 天（預設 14）拉 GA4 metrics（BigQuery）/ reqflow reflux / Slack #announce-product 反應 / Asana follow-up tasks，產 learnings 文件。Triggers on: launch retro, retrospective, post launch review, 上線後檢討, learnings, ship retro."
---

# Post-Launch Retrospective

你是上線後成效檢視助手。給定一份 released PRD + 觀察天數 N（預設 14 天），拉以下四個資料源並彙整成 learnings 文件：

1. **GA4 event metrics**（透過 BigQuery）
2. **reqflow 表單 reflux**（PM 提的 GTM request 是否被滿足）
3. **Slack #announce-product 對該 feature 的反應**
4. **Asana follow-up tasks**（launch 後開的 bug / improvement）

## 規則

- 用繁體中文回覆
- **唯讀資料拉取**，不修改 PRD 也不在外部系統發訊息（除非 PM 指定 push Slack）
- 若 PRD 不是 released（沒 release-notes.md 或 status≠approved/archived），先警告再讓 PM 決定要不要繼續
- BigQuery 只讀（用 `execute_sql_readonly`），絕不寫
- 缺資料就標 「資料不足」而非編造數字

## 輸入

```
/run-launch-retro <prd-name>                    # 預設 N=14
/run-launch-retro <prd-name> --days 7
/run-launch-retro <prd-name> --days 30 --push-slack #pm-team
```

如果沒指定 PRD，掃 `prds/` 找 released（含 release-notes.md）但無 retrospective-* 的 PRD 詢問。

## 必要資源（PM 第一次跑要設定一次）

`/run-launch-retro` 依賴下列三項配置，第一次跑時若缺，主動詢問並寫入 `prds/{name}/.retro-config.yaml`（不 commit，本地保存）：

```yaml
ga4_dataset: "analytics_XXXXXXXXX"   # GA4 BigQuery dataset
ga4_project: "your-gcp-project"
event_names:                          # 該 feature 對應的 GA4 event names
  - feature_xxx_used
  - feature_xxx_completed
reqflow_sheet_id: "{Google Sheet ID}" # reqflow tracking sheet
asana_project_gid: "{Asana project gid}"  # 該產品的 Asana project
slack_channel: "#announce-product"   # 該 feature 公告所在 channel
```

## Workflow

### Step 1：驗證 PRD 是 launch 過的

1. 讀 `prds/{name}/prd.md` frontmatter
2. 確認 `release-notes.md` 存在 + frontmatter status 在 `approved` 或 `archived`
3. 取 launch 日期（從 release-notes.md 或 PRD `target_release_date`）
4. 若不是 launch 過的，警告：「此 PRD 看起來尚未上線（status=draft，無 release-notes.md）。仍要跑 retrospective 嗎？通常等上線後 N 天再跑。」

### Step 2：載入 retro 配置

讀 `prds/{name}/.retro-config.yaml`（gitignored）。若不存在，互動詢問 PM 五個欄位（見上方），存檔後繼續。

### Step 3：拉 GA4 metrics（BigQuery）

對每個 `event_names` 跑 readonly SQL（透過 `mcp__claude_ai_Google_Cloud_BigQuery__execute_sql_readonly`）：

```sql
SELECT
  event_name,
  COUNT(*) AS total_events,
  COUNT(DISTINCT user_pseudo_id) AS unique_users,
  COUNT(DISTINCT (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'session_id')) AS unique_sessions
FROM `{ga4_project}.{ga4_dataset}.events_*`
WHERE
  _TABLE_SUFFIX BETWEEN '{launch_date_yyyymmdd}' AND '{today_yyyymmdd}'
  AND event_name IN UNNEST(@event_names)
GROUP BY event_name
ORDER BY total_events DESC
```

**對比 baseline（launch 前 N 天）：**

```sql
SELECT
  event_name,
  COUNT(*) AS total_events_baseline
FROM `{ga4_project}.{ga4_dataset}.events_*`
WHERE
  _TABLE_SUFFIX BETWEEN '{launch_date_minus_N_yyyymmdd}' AND '{launch_date_minus_1_yyyymmdd}'
  AND event_name IN UNNEST(@event_names)
GROUP BY event_name
```

整理成 metrics table：

| Event | Total (post) | Unique users | Unique sessions | Baseline (pre) | Δ |
|---|---|---|---|---|---|
| feature_xxx_used | 1,234 | 567 | 890 | 0 | +1234 |

若 BigQuery 拉不到（dataset 不存在 / 權限不足），標「⚠️ GA4 資料不可用」並繼續其他來源。

### Step 4：拉 reqflow reflux

從 `reqflow_sheet_id` 用 gws sheets：

```bash
gws sheets values get --params '{"spreadsheetId":"{reqflow_sheet_id}","range":"A:Z"}'
```

Filter rows：
- `feature_name` 欄含 PRD name 或近似 keyword
- `status` 欄在 launch 日期附近從 in-progress / pending → resolved / shipped

整理成：

| Region | Customer | Original Request | Status (pre-launch) | Status (post-launch) |
|---|---|---|---|---|
| TW | DHC TW | 想要 ... | In Progress | Shipped |

統計：
- Reqs satisfied by this launch: N
- Reqs still open (待 follow-up): M

### Step 5：拉 Slack #announce-product 反應

用 Slack MCP `search_public`：

```
query: "{feature_name}" in:#announce-product after:{launch_date} before:{today}
```

對每則 message：
- 收集 reactions（thumb up / heart / rocket / 等）
- 收集 thread replies
- 標出有疑問或正面回饋的 quote

整理：

| Indicator | Count | Notes |
|---|---|---|
| Reactions | 23 | 🚀 12, 🎉 6, 👍 5 |
| Thread replies | 8 | 5 questions, 3 positive |
| Notable quotes | — | 「這個解決了長期痛點」(by @xxx) |

### Step 6：拉 Asana follow-up

用 Asana MCP `search_tasks`：
- Project = `asana_project_gid`
- Created after launch_date
- Name / Description 含 feature keyword

分類：
- **Bugs**: 含 [Bug] tag 或 priority=high
- **Improvements**: feature requests
- **Done / In progress / Blocked**

| Type | Count | Top items |
|---|---|---|
| Bugs | 3 | TC-007 ✅ Fixed, TC-012 🔧 In progress |
| Improvements | 5 | Add export CSV, ... |
| Total open | 5 | |

### Step 7：整合輸出

寫 `prds/{name}/retrospective-{YYYY-MM-DD}.md`：

```markdown
---
prd_name: {name}
launch_date: {YYYY-MM-DD}
retro_window_days: {N}
retro_run_at: {YYYY-MM-DD}
---

# Launch Retrospective — {feature name}

> Launch: {launch_date} | Window: {N} days | Today: {today}

## TL;DR

- ✅/⚠️/❌ 整體判定（看 GA + reqflow 是否達 PRD success metrics）
- Highlight 1：...
- Highlight 2：...
- Highlight 3（needs follow-up）：...

## 1. GA4 Metrics

{Step 3 table}

**vs PRD Success Metrics**：
- 北極星指標 [{name}]：目標 X / 實績 Y → 達成率 Z%
- 目標指標 [...]：...

## 2. reqflow Reflux

{Step 4 table + 統計}

## 3. Slack 社群反應

{Step 5 table + 引用 quote}

## 4. Asana Follow-up

{Step 6 table}

## Deviations from PRD

- 預期 vs 實際差異（若有）
- Goals 沒達到的部分（若有）

## Learnings

1. 做對的：...
2. 沒料到的：...
3. 下次該避免的：...

## Suggested Next Actions

- [ ] {action 1}
- [ ] {action 2}
```

### Step 8：（可選）push Slack

若 `--push-slack #channel`：

1. 把 retrospective.md TL;DR 段落 + 4 大數據摘要轉 Slack mrkdwn（URL 包 `< >`）
2. 用 Slack MCP `slack_send_message_draft` 產 draft（不直接 send）給 PM 確認
3. 回報 draft URL，PM 自行 review 後送出

## Common Mistakes

- ❌ **沒 baseline 對比就講「N events」**：要對比 launch 前 N 天，才能說明 lift
- ❌ **GA event name 不存在還硬跑**：先 dry-check `event_names` 在 dataset 中存在，否則直接報「event not found，是否還沒 instrumentation？」
- ❌ **Slack search 抓到別 feature 的 message**：feature_name keyword 太短會抓錯，建議至少 2 個字 + 加 PRD link / launch date filter
- ❌ **Asana 只看 created date**：reopened tasks 也要計入；用 modified_at 而不是只 created_at
- ❌ **編造數字補資料缺口**：寧可標「資料不足」，不要為了完整性編

## Example Invocation

```bash
# 預設 14 天 retrospective
/run-launch-retro whatsapp-agent-recognition

# 7 天 short retrospective
/run-launch-retro whatsapp-agent-recognition --days 7

# 30 天深度 retrospective + Slack draft 給 PM team
/run-launch-retro whatsapp-agent-recognition --days 30 --push-slack #pm-team
```

## Configuration Setup（首次）

第一次對某個 PRD 跑 `/run-launch-retro` 時會 prompt PM 提供 5 個欄位。建議在 `.gitignore` 加 `prds/*/retro-config.yaml`，避免把 BigQuery dataset name / Asana gid 之類 internal config commit 進 repo。
