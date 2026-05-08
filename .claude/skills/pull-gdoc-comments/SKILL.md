---
name: pull-gdoc-comments
description: "從 Google Doc 讀取 comment（包含 stakeholder gdoc feedback），整理成結構化摘要，協助 PM 決定如何反映到 PRD。Triggers on: pull comments, gdoc comments, 拉評論, 讀取評論, review comments, stakeholder feedback gdoc, stakeholder gdoc feedback."
---

# Pull Google Doc Comments

從 Google Doc 讀取 stakeholder 留下的 comment，整理成結構化摘要，協助 PM 處理回饋。

## 規則

- 用繁體中文回覆
- 需要 `gws` CLI 已安裝且認證
- Comment 本身不搬進 repo — 只把結論反映到 markdown
- PM 是最終決策者，所有建議都需要 PM 核准才會修改 PRD
- 處理完的 comment 可以在 Google Doc 上標記 resolved

## 輸入

PM 可以指定 PRD：`/pull-gdoc-comments journey-datetime-scheduled-trigger`

如果沒有指定，檢查 `prds/` 目錄下有 `gdoc_id` 的 PRD，詢問 PM 要拉哪份。

## Workflow

### Step 1：讀取 Comments

1. 從 `prds/{name}/prd.md` frontmatter 讀取 `gdoc_id`
2. 用 `gws drive comments list` 讀取所有未 resolved 的 comment
3. 對每則 comment 擷取：
   - 作者（displayName）
   - 引用文字（quotedFileContent.value）— 用來判斷 comment 在哪個段落
   - Comment 內容
   - 是否有 reply thread
   - 建立時間

### Step 2：分類整理

將 comment 依影響類型分類，呈現給 PM：

```markdown
## Google Doc Comments 摘要

> 來源：[PRD Google Doc](gdoc_url)
> 未處理 comment：N 則

### 需要修改 PRD

| # | 角色 | 引用段落 | Comment | 建議處理方式 |
|---|------|---------|---------|-------------|
| 1 | ...  | ...     | ...     | 修改 Proposed Solution / 新增 AC / ... |

### 新增 Open Question

| # | 角色 | Comment | 建議的 Open Question |
|---|------|---------|---------------------|
| 1 | ...  | ...     | ...                 |

### 僅供參考（不需改 PRD）

| # | 角色 | Comment | 原因 |
|---|------|---------|------|
| 1 | ...  | ...     | 屬於實作細節 / 已在 scope 外 / ... |
```

### Step 3：PM 決策

逐項詢問 PM：
- 哪些要修改 PRD？怎麼改？
- 哪些要加到 Open Questions？
- 哪些略過？

### Step 4：執行修改

根據 PM 決策：
1. 修改 `prd.md`（或其他對應的 .md 檔案）
2. 修改完成後，提醒 PM：
   - 「要用 `/sync-gdoc` 同步到 Google Doc 嗎？」
   - 「要在 Google Doc 上把已處理的 comment 標記 resolved 嗎？」

### Step 5：標記 Resolved（可選）

如果 PM 同意，用 `gws drive replies create` 回覆 comment 說明處理結果，
再用 `gws drive comments update` 將 comment 標記為 resolved。

回覆格式：
```
✅ 已處理：{處理方式簡述}
```
