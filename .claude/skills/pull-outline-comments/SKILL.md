---
name: pull-outline-comments
description: "**Use IMMEDIATELY when user wants to pull stakeholder comments from an Outline doc** — phrases like 拉 outline 評論 / pull outline comments / outline comments / outline feedback / Outline 上面留言 / 同事在 outline 留了什麼 / 收 outline 回饋 / 整理 outline 評論 / 看大家 outline 留什麼 / outline 上的意見. Structures comments by author + theme so PM can decide what to fold back into the PRD. PRIMARY path for internal stakeholder feedback. For external / cross-org stakeholders commenting on GDoc, use pull-gdoc-comments. If doc URL/ID unclear, ask in-skill."
---

# Pull Outline Comments → PRD

從 PRD 對應的 Outline parent doc 與 children 拉取所有 comments，整理成結構化摘要，協助 PM 決定要 reflect 到 PRD 的哪些段落。Outline comment 拉完不直接寫死，最終是否落地到 PRD 由 PM 逐項決定。

## 規則

- 用繁體中文回覆
- 需要 cl-outline MCP plugin 已 mounted
- Comment 本身不搬進 repo — 只把結論反映到 markdown
- 對每個 comment 必須讓 PM 判斷三選一：修 PRD / 加 Open Question / 略過
- 寫入 PRD 後可選擇是否 mark Outline comment 為 resolved

## 輸入

```
/pull-outline-comments <prd-name>             # 拉指定 PRD 的 Outline 評論
/pull-outline-comments                         # 沒指定時掃 prds/ 找有 outline_doc_id 的
/pull-outline-comments <prd-name> --include-resolved   # 也拉已 resolved 的（預設只拉 unresolved）
```

如果沒指定，掃 `prds/` 找 frontmatter 有 `outline_doc_id` 的 active PRD 詢問 PM。

## Workflow

### Step 1：讀取 Comments

1. 讀 `prds/{name}/prd.md` frontmatter 取 `outline_doc_id`
2. 用 `mcp__plugin_cl-outline_outline__list_documents` 列 parent + children doc id
3. 對每個 doc：
   ```
   mcp__plugin_cl-outline_outline__list_comments(documentId)
   ```
4. 整理出每則 comment：
   - **author**（display name）
   - **doc**（哪個 child / parent）
   - **quoted text**（被評論的段落，若 inline comment）
   - **comment body**
   - **replies**（如有 thread）
   - **created_at / updated_at**
   - **resolved**（true / false）

### Step 2：分類與摘要

把所有 comments 分成三組（呈現給 PM）：

| Category | 描述 |
|---|---|
| **需要修改 PRD** | comment 指出 PRD 內容錯誤、要新增 / 修改 / 移除 requirement |
| **新增 Open Question** | comment 引出新問題、需後續釐清 |
| **僅供參考** | comment 是討論 / 補充 context、不需改 PRD |

呈現 table：

```markdown
## Outline Comments — {prd-name}

| # | Doc | Author | Quoted | Comment | Suggested Action |
|---|---|---|---|---|---|
| 1 | PRD | @PM-x | "Goals 第二點" | 「這個 metric 太抽象」 | 修 PRD |
| 2 | Test Cases | @QA-y | (general) | 「edge case 沒涵蓋 X」 | 新增 Open Question |
| 3 | Evaluation | @ENG-z | "ICE Ease=4" | 「我覺得 3 比較合理」 | 僅供參考 |
```

### Step 3：PM 決定

針對每個 comment item，PM 標：
- `[ ] 修 PRD` — 進 Step 4 寫入
- `[ ] 加 Open Question` — 進 Step 4 寫入 Open Questions
- `[ ] 略過` — 不動

**等 PM 全部標完才進 Step 4**。

### Step 4：執行變更

對每個被標 `修 PRD` 或 `加 Open Question` 的 comment：

1. 讀 `prds/{name}/prd.md`
2. 找對應段落或 Open Questions section
3. 套用 PM 描述的修改
4. 顯示 final diff 給 PM 最後 confirm 後才寫檔
5. 更新 frontmatter `updated`

### Step 5：（可選）Mark Outline Comments Resolved

問 PM：「要在 Outline 上把已處理的 comment 標 resolved 嗎？」

若 yes：對每個被處理的 comment，用：

```
mcp__plugin_cl-outline_outline__update_comment(commentId, resolved: true)
```

或 reply + resolved：

```
mcp__plugin_cl-outline_outline__create_comment(documentId, parentCommentId, text: "已反映到 PRD: {section}")
mcp__plugin_cl-outline_outline__update_comment(parentCommentId, resolved: true)
```

### Step 6：摘要 + 後續提醒

```markdown
## Pull Outline Comments Summary

- 拉到 N 則 comment（unresolved: M / resolved: K）
- 反映到 PRD: X 則
- 加為 Open Question: Y 則
- 略過: Z 則
- Outline 上 mark resolved: J 則

提醒：PRD 已修改，記得跑 `/sync-outline` 同步回 Outline，避免 PRD ↔ Outline 偏離。
```

## 跟 pull-gdoc-comments 的關係

| 來源 | 用 pull-outline-comments | 用 pull-gdoc-comments |
|---|---|---|
| 內部 stakeholder 在 Outline 留 comment | ✅ primary | — |
| 外部 / cross-org 在 Google Doc 留 comment | — | ✅（gws drive comments） |

兩個並行，不互斥；同一份 PRD 可以兩邊都有評論回流。

## Common Mistakes

- ❌ **跳過 PM 決定直接修 PRD**：每個 comment 都要 PM 標 action
- ❌ **mark resolved 沒留 reply**：之後 audit 看不出為什麼 resolved；建議先 reply 再 resolved
- ❌ **覆蓋 Outline doc**：本 skill 是讀 + 反映，不該寫 Outline doc body（要寫的話用 sync-outline）

## Example Invocation

```bash
# 拉指定 PRD
/pull-outline-comments custom-field-tagging

# 拉並包含已 resolved 的（看完整 history）
/pull-outline-comments custom-field-tagging --include-resolved

# 沒指定，互動詢問
/pull-outline-comments
```
