---
name: announce-slack
description: "已上線功能 → #announce-product 格式 Slack draft（含 product context、feature points、links）。Triggers on: announce slack, slack draft, 公告 draft, announce product, 上線通知 slack, internal update slack."
---

# Announce Slack Draft

你是 #announce-product 短公告產生助手。從**已上線**功能資訊產出 8-10 行的 Slack draft（不直接送出），讓 PM 在 Slack 編輯器最後過目再發。

## 與 `/gen-release-notes` 的邊界（重要）

兩個 skill 場景不同，**不要混用**：

| | `/gen-release-notes` | `/announce-slack`（本 skill） |
|---|---|---|
| 時機 | Release **前**（內部 review） | 功能**上線當天** |
| 長度 | 完整 internal update（多段、含 metadata 表、competitor analysis、FAQ） | 8-10 行短公告 |
| 目的 | 內部 stakeholder 完整理解 | 全公司 awareness |
| 輸出 | 寫回 PRD 資料夾 (`release-notes.md`)、可選同步到 PRD Google Doc | Slack **draft**（不寫回 PRD） |
| Slack 形式 | 主訊息 + 多則 thread reply | 單一 draft（≤10 行） |

**核心差異**：本 skill **不寫回 PRD**、**不送 thread**、**不直接 send**。只產 draft。

## 規則

- 用繁體中文回覆 PM；draft 內容語言由 `--lang` 決定（預設 `en`）
- 全文 8-10 行為佳，超過要建議拆 thread（但仍只產 draft，不直接送）
- **URL 必須包在 `< >`**（Slack mrkdwn 規範，避免顯示亂碼）
- 開頭 `:rocket:` 已在模板，不要再加額外 emoji 開頭
- 不寫回 PRD（與 `/gen-release-notes` 的核心差異）
- 用 `mcp__claude_ai_Slack__slack_send_message_draft` 產 draft，**絕不**用 `slack_send_message` 直接送出
- 每個 claim 必須能追溯回 PRD / PM 輸入，不發明 PRD 沒寫的內容

## 輸入

| 參數 | 必填 | 預設 | 說明 |
|---|---|---|---|
| `--feature` | ✅ | — | 功能名稱（顯示在 :rocket: 後） |
| `--prd` | ❌ | — | PRD URL（Outline doc 或 Google Doc）→ 自動 fetch context |
| `--shipped-date` | ❌ | 今天 | 上線日期（YYYY-MM-DD） |
| `--channel` | ❌ | `#announce-product` | 目標 channel |
| `--lang` | ❌ | `en` | `en` 或 `zh-TW` |

## Workflow

### Step 1：收集 context

**若有 `--prd`**：依 URL 類型 fetch：

- **Outline**（`app.getoutline.com/doc/...`）：用 `mcp__plugin_cl-outline_outline__fetch`
- **Google Doc**（`docs.google.com/document/...`）：用 gws CLI
  ```bash
  gws docs documents get --params '{"documentId":"<DOC_ID>","includeTabsContent":true}'
  ```

從 PRD 萃取 4 欄位：
1. **What it does** — 1-2 句 product framing（從 Background / Introduction）
2. **For whom** — 目標客群（從 Target Audience / ICP）
3. **Why it matters** — 3 個 key value points（從 Selling Points / User Stories）
4. **Links** — PRD、HC、Slack Q&A thread

**若沒 `--prd`**：互動式詢問 PM 提供上述 4 欄位（HC link / Q&A thread 可留空）。

### Step 2：套用模板

根據 `--lang` 選模板。**URL 必須包在 `< >` 裡**（Slack mrkdwn）。

#### English 模板

```
:rocket: *{Feature name}* shipped on {date}

*What it does*
{1-2 sentence product framing}

*For whom*
{Target audience / customer segment}

*Why it matters*
- {Key value point 1}
- {Key value point 2}
- {Key value point 3}

*Links*
- PRD: <{PRD url}|spec>
- HC: <{HC url}|help center>
- Slack Q&A thread: <{thread url}|here>

cc @{stakeholders}
```

#### zh-TW 模板

```
:rocket: *{功能名稱}* 已於 {日期} 上線

*功能簡介*
{1-2 句產品定位}

*受眾*
{目標客群 / 適用對象}

*為什麼重要*
- {關鍵價值點 1}
- {關鍵價值點 2}
- {關鍵價值點 3}

*相關連結*
- PRD：<{PRD url}|規格文件>
- HC：<{HC url}|說明中心>
- Slack Q&A thread：<{thread url}|此處>

cc @{相關 stakeholders}
```

### Step 3：產 Slack draft

呼叫 `mcp__claude_ai_Slack__slack_send_message_draft`：

- `channel`: 由 `--channel` 決定（預設 `#announce-product`）
- `text`: 套好模板的訊息

**絕不**用 `slack_send_message`（會直接送出）。

### Step 4：回報

呈現給 PM：

```
✅ Slack draft 已建立

📝 Preview：
[draft 內容]

🔗 編輯連結：[Slack draft URL]
🎯 Channel：#announce-product
👀 建議 reviewer：[PM owner / product lead]

請 PM 在 Slack 編輯器最後檢查再送出。
```

**不寫回 PRD**。

## Common Mistakes

| ❌ | ✅ |
|---|---|
| 用 `slack_send_message` 直接送出 | 用 `slack_send_message_draft` 產 draft |
| URL 寫成純文字 `https://...` | URL 包在 `<...|label>` 裡 |
| 寫得跟 release-notes 一樣長 | 控制在 8-10 行；超過建議改用 `/gen-release-notes` |
| 在 :rocket: 前再加 emoji | 模板 :rocket: 開頭就好 |
| 寫回 `prds/{name}/release-notes.md` | 本 skill 不寫回 PRD |
| 主訊息 + 多則 thread reply | 本 skill 只產一則 draft |

## Example Invocation

```
# 從 Outline PRD 自動 fetch context
/announce-slack --feature "WhatsApp Agent Recognition" --prd https://app.getoutline.com/doc/abc

# 中文版、指定上線日期
/announce-slack --feature "Lead Capture v2" --shipped-date 2026-05-08 --lang zh-TW

# 推到非預設 channel
/announce-slack --feature "Ads to Chat P1.5" --channel "#proj-ads-to-chat"

# 沒有 PRD，互動式輸入
/announce-slack --feature "Custom Field Tagging"
```
