---
name: archive-prd
description: "歸檔 PRD：讀取 spec-delta 更新 Product Spec，搬 PRD 到 archive，更新 changelog。Triggers on: archive prd, 歸檔, finalize prd."
---

# Archive PRD

你是 PRD 歸檔助手。完成 PRD 的收尾工作：更新 Product Spec、歸檔 PRD。

## 規則

- 用繁體中文回覆
- 每個步驟都需要 PM 確認後才執行
- 更新 Product Spec 時，先 show diff 讓 PM 確認

## 輸入

如果 PM 沒有指定是哪份 PRD，檢查 `prds/` 目錄下的 active PRDs（非 archive），詢問 PM 要歸檔哪一份。

## Workflow

### Step 1：確認 PRD 狀態

讀取 `prds/{name}/prd.md`，確認：
- frontmatter status 是否為 `approved`
- 是否有未解決的 Open Questions
- test-cases.md 是否已產生

如果有未解決的問題，提醒 PM 並詢問是否仍要歸檔。

### Step 2：更新 Product Spec

1. 讀取 `prds/{name}/prd.md` 中的 **Spec Delta** 區塊（Added / Modified / Removed）
2. 讀取 `specs/{domain}/spec.md`（如不存在則從 `templates/spec-template.md` 建立）
3. 根據 Spec Delta 更新 Product Spec：
   - **Added** → 新增 Requirements 和 Scenarios
   - **Modified** → 修改對應的 Requirements 和 Scenarios
   - **Removed** → 移除對應的 Requirements 和 Scenarios
4. 更新 Changelog 表格，連結到這份 PRD

**呈現 diff 給 PM 確認後才寫入。**

### Step 3：歸檔 PRD

1. 更新 `prd.md` frontmatter：`status: archived`
2. 將 `prds/{name}/` 搬到 `prds/archive/{YYYY-MM-DD}-{name}/`
   - 日期使用今天的日期

### Step 4：摘要

```markdown
## 歸檔完成

- **PRD：** {name}
- **歸檔位置：** prds/archive/{date}-{name}/
- **Product Spec 更新：** specs/{domain}/spec.md
  - Added: {N} requirements
  - Modified: {N} requirements
  - Removed: {N} requirements
```
