---
name: archive-prd
description: "歸檔 PRD：讀取 spec-delta 更新 Product Spec，搬 PRD 到 archive，更新 changelog。Use when ready to ship/close a finished PRD. Triggers on: archive prd, 歸檔, ship prd, close prd, prd done."
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
2. **檢查 `specs/{domain}/spec.md` 是否存在：**

   #### Case A：spec 已存在 → 繼續

   照原流程套 Spec Delta。

   #### Case B：spec 不存在 → STOP，明確問 PM

   不要無聲從 template 建空殼 — domain 第一次出現通常代表這是新 module，需要先把現有行為 reverse-engineer 成 spec，再套這次 PRD 的 delta。

   呈現給 PM：

   > ⚠️ `specs/{domain}/spec.md` 不存在。三個選項：
   >
   > 1. **（推薦）先跑 `/gen-product-spec {domain}` 反向產出 spec baseline**，再回來繼續歸檔
   > 2. 從 `templates/spec-template.md` 建立空 spec（你之後手動填）
   > 3. Abort 歸檔（這份 PRD 維持 active 狀態）

   等 PM 選擇後再繼續。**不要替 PM 選**。

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
