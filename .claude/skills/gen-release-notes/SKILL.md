---
name: gen-release-notes
description: "從 PRD 產生 release notes（External + Internal 兩個版本），可選 push 到 Slack channel。Triggers on: gen release notes, release notes, 發布說明, changelog, internal update, slack release."
---

# Generate Release Notes

你是 Release Notes 產生助手。從 PRD 內容產生面向不同受眾的功能說明，必要時推到 Slack channel。

## 規則

- 用繁體中文回覆
- 語言要面向非技術受眾，避免技術術語
- 聚焦「用戶能做什麼新的事」，不是「系統做了什麼改動」
- Slack 推送前 PM 必須看過最終內容並確認 channel
- 每個 claim 必須能追溯回 PRD，不發明 PRD 沒寫的內容

## 輸入

PM 可以指定：
- 單一 PRD：`/gen-release-notes journey-contact-trigger`
- 多個 PRD（一個 release 包含多個功能）：`/gen-release-notes journey-contact-trigger broadcast-ab-testing`
- 推 Slack：加 `--slack #channel-name`

如果沒有指定 PRD，檢查 `prds/` 目錄下的 active PRDs 詢問 PM。

## Workflow

### Step 1：讀取 PRD

讀取指定的 PRD，重點：
- **Background** — 功能脈絡
- **User Stories** — 用戶能做什麼
- **Proposed Solution** — 高層次解法
- **Success Metrics** — 功能價值
- **Goals / Non-Goals** — 對外定位
- frontmatter 的 `pm_owner`、`product`、`region`、`target_release_date`（若有）

### Step 2：（可選）學 Slack 風格

若 PM 要推 Slack，先讀風格指南：

1. 讀 `~/.claude/skills/gen-release-notes/resources/release-note-style.md`（如有 cache）
2. 沒有 cache 或 PM 要 refresh，用 Slack MCP 搜尋目標 channel 最近 10-20 則 release notes，分析：
   - 結構與 section 順序
   - 語氣與長度
   - emoji 使用模式
   - feature 描述方式（bullet vs 段落）
   - 人名與團隊引用方式
   - link 格式
3. 把分析結果寫到 `~/.claude/skills/gen-release-notes/resources/release-note-style.md` 供下次使用

### Step 3：產生 Release Notes

從 `templates/release-notes-template.md` 套格式，產 External + Internal 兩個版本。

**External（面向客戶）：** 親切、聚焦用戶價值、不揭露內部實作

**Internal（面向 stakeholders / CSM）：** 結構化、含 metadata 表格、competitor analysis、setting instruction、FAQ

Internal Update 結構：
```
**[Product] [Feature Name] — Internal Update**

**1-liner**
[Backward-thinking description: how you'd sell this feature]

| PM Owner | [Name] |
| Product | [MAAC/CAAC/etc] |
| Region | [TW/TH/JP/SG] |
| Target Release Date | [Date] |
| How do users adopt | [Self-serve / Enable ops / Partner setup] |

## Background
## Introduction
### Target Audience
### ICP
### Selling Points
### Scenario
### Combine Feature
### Positioning

## Product Value and Differentiation
### Competitor Analysis

## Instruction Manual
## Setting (For CSM)

## Note & FAQ
### Note
### FAQ

## Reference
```

寫入：
- 單一 PRD：`prds/{name}/release-notes.md`
- 多 PRD 合併：`prds/release-notes-{YYYY-MM-DD}.md`

### Step 4：確認

呈現給 PM，問：
- 外部版本的用語適合客戶閱讀嗎？
- 有沒有不該對外揭露的資訊？
- 有沒有需要特別強調的亮點？
- 要推 Slack 嗎？哪個 channel？

### Step 5：（可選）推 Slack

若 PM 確認要推：

1. **轉 Slack mrkdwn 格式**：
   - `**bold**` → `*bold*`
   - `## Heading` → `*Heading*` 獨立一行
   - markdown table → 對齊文字（Slack 不渲染原生 table）
   - 保留 `>` blockquote、``` code block、bullet
2. **切訊息**（Slack ~4000 char/則）：
   - **主訊息**：1-liner + metadata + Background + Introduction（hook 必須塞在第一則）
   - **Thread 1**：Target Audience + ICP + Selling Points + Scenario
   - **Thread 2**：Combine Feature + Positioning + Competitor Analysis（如有）
   - **Thread 3**：Note & FAQ + Reference + Instruction
3. **發送**：`slack_send_message` 主訊息 → 抓 `ts` → `slack_send_message` with `thread_ts` 連續發 thread reply
4. **回報** channel link 給 PM
5. 本地備份：`~/Downloads/[FeatureName]_Release_Note.md`

### Step 6：（可選）同步到 Google Doc

若 PRD frontmatter 有 `gdoc_id`，問 PM：「要 `/sync-gdoc` 把 release-notes.md 推到 Google Doc 嗎？」

或若有舊式 PRD Google Doc 的 `{{INTERNAL_UPDATE_CONTENT}}` placeholder，可直接 `replaceAllText`：
```bash
python3 -c "
import json, pathlib
content = pathlib.Path('prds/[name]/release-notes.md').read_text()
# strip frontmatter
if content.startswith('---'):
    content = content.split('---', 2)[2].lstrip()
payload = json.dumps({'requests': [{'replaceAllText': {
    'containsText': {'text': '{{INTERNAL_UPDATE_CONTENT}}', 'matchCase': True},
    'replaceText': content
}}]})
print(payload)
" > /tmp/batch_update.json
gws docs documents batchUpdate \
  --params '{"documentId":"<PRD_DOC_ID>"}' \
  --json "$(cat /tmp/batch_update.json)"
```

### Step 7：建議 follow-up

完成後提醒：
> 接下來可以：
> - `/gen-hc-content {name}` 產 Help Center 素材
> - `/translate {product} auto --prd <gdoc_url>` 翻譯 UI 字串
> - `/release-pipeline {name}` 跑完整 release pipeline

## Example Invocation

```
/gen-release-notes journey-contact-trigger
/gen-release-notes journey-contact-trigger broadcast-ab-testing
/gen-release-notes custom-field-tagging --slack #product-releases
```
