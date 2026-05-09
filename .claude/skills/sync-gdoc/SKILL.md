---
name: sync-gdoc
description: "將 PRD 資料夾推送（snapshot）到 Google Doc，每個 .md 檔對應一個分頁。Markdown 是 source of truth；如果 markdown 是從 meeting / Slack 結論進來的，先跑 sync-prd 再 sync-gdoc。Triggers on: sync gdoc, google doc, 同步文件, 產生 gdoc, push gdoc, push to google doc."
---

# Sync PRD to Google Doc

將 PRD 資料夾中的 markdown 檔案同步到 Google Doc，每個檔案一個分頁，帶格式。

## 規則

- 用繁體中文回覆
- 需要 `gws` CLI 已安裝且認證
- Google Doc 是 **read-only snapshot**，source of truth 是 repo 裡的 markdown
- 每份 PRD 對應一份固定的 Google Doc，Doc ID 記在 `prd.md` frontmatter 的 `gdoc_id` 和 `gdoc_url`

## 輸入

PM 可以指定 PRD：`/sync-gdoc journey-datetime-scheduled-trigger`

如果沒有指定，檢查 `prds/` 目錄下的 active PRDs，詢問 PM 要同步哪份。

## 檔案與分頁對應

動態掃描 PRD 資料夾，只為存在的檔案建立分頁：

| 檔案 | Tab 名稱 | 說明 |
|------|---------|------|
| `evaluation.md` | Evaluation | 評估報告 |
| `prd.md` | PRD | PRD 本文 |
| `review.md` | Agent Reviews | Review 結果 |
| `test-cases.md` | Test Cases | 測試案例 |
| `release-notes.md` | Release Notes | 發布說明 |
| `hc-content.md` | HC Content | Help Center 內容素材 |

## Workflow

### Step 1：確認狀態 + 新鮮度檢查

1. 讀取 `prds/{name}/prd.md` 的 frontmatter，檢查是否已有 `gdoc_id`、`gdoc_synced_at`
2. 掃描 PRD 資料夾中存在的 .md 檔案
3. **新鮮度檢查**：對每個 .md 檔比對 mtime vs `gdoc_synced_at`
   - 若任一 .md 比 GDoc 新且**沒有**先跑 `/sync-prd`，提醒 PM：
     > 「偵測到 prd.md / sync-prd 寫入後 GDoc 還沒更新。是否先確認 `/sync-prd` 已收齊所有 meeting / Slack 結論？或可直接 push 既有 markdown 到 GDoc。」
   - PM 確認後才繼續
4. 告知 PM：
   - 如果有 `gdoc_id`：「將更新現有 Google Doc: {gdoc_url}，共 N 個分頁」
   - 如果沒有 `gdoc_id`：「將建立新的 Google Doc，共 N 個分頁」
5. 等 PM 確認後再執行

### Step 2：建立或準備 Google Doc

**新建（沒有 gdoc_id）：**

1. 用 `gws docs documents create` 建立空白文件，標題格式：`[PRD] {prd title}`
2. 重命名第一個 tab，並用 `addDocumentTab` 建立其餘分頁
3. 記錄 Doc ID 和各 tab ID

**更新（已有 gdoc_id）：**

1. 用 `gws docs documents get` 讀取現有 Doc，取得已有的 tab 清單
2. 比對需要的分頁：
   - 已存在的 tab → 清空內容後重寫
   - 新增的檔案 → 用 `addDocumentTab` 建立新分頁
   - 不再存在的檔案 → 保留 tab（不刪除，避免丟失 comment）

### Step 3：寫入內容

使用 `scripts/md_to_gdoc.py` 的邏輯（或直接呼叫該腳本）：

1. 對每個 tab，strip frontmatter 後解析 markdown
2. 轉為 Google Docs batchUpdate requests（帶格式：heading、bold、code、bullet list 等）
3. 分 chunk（每 100 個 request）送出

### Step 4：更新 frontmatter

寫入 `prd.md` 的 frontmatter：
- `gdoc_id`、`gdoc_url`（若是新建）
- `gdoc_synced_at: {ISO 8601 timestamp}`（每次都更新，給 Step 1 新鮮度檢查用）

### Step 5：回報結果

告知 PM：
- Google Doc 連結
- 同步了哪些分頁
- 最後同步時間
