---
name: sync-outline
description: "將 PRD 資料夾推到 Outline（primary path）：建一個 parent doc（PRD 名稱）+ 每個 .md 對應一個 nested child doc。Outline 為內部 SSOT 的對外 snapshot；對外分享 / 跨 org stakeholder 才用 sync-gdoc。Triggers on: sync outline, push outline, 同步 outline, 推到 outline, sync prd outline."
---

# Sync PRD to Outline（Primary）

把 PRD 資料夾中的 markdown 檔案同步到 Outline，每個 .md 對應一份 nested child doc。Outline 是公司內部 SSOT 的對外 snapshot — 同事直接從 Outline 看 PRD 即可，repo 是 source of truth。

## 規則

- 用繁體中文回覆
- 需要 cl-outline MCP plugin 已 mounted（`mcp__plugin_cl-outline_outline__*`）
- Outline doc 是 **read-only snapshot**，source of truth 是 repo 裡的 markdown
- 每份 PRD 對應一個 parent Outline doc，frontmatter 記 `outline_doc_id` 與 `outline_url`
- 每個 .md 對應一個 child doc（parentDocumentId = parent doc id）
- Outline 原生吃 markdown，**不需要 batchUpdate / md_to_gdoc.py 轉換**
- Patch 既有 doc 一律走 `/patch-outline-safely` 加 pre/post-flight 驗證

## 輸入

```
/sync-outline <prd-name>                      # 直接同步
/sync-outline <prd-name> --dry-run            # 列出計畫，不寫入
/sync-outline                                  # 沒指定 PRD 時掃描詢問
/sync-outline <prd-name> --collection {id}    # 新建時指定 Outline collection
```

如果沒指定 PRD，掃 `prds/` 詢問。

### `--dry-run` 模式

不呼叫任何 Outline 寫入 API，只輸出：
- parent doc 將建立 / 已存在
- 每個 child doc：create / update / preserve（local 已刪檔）
- 預估 API call 數量與執行時間

## 檔案與 child doc 對應

動態掃描，只為存在的檔案建立 child：

| 檔案 | Child doc title | 順序 |
|---|---|---|
| `evaluation.md` | Evaluation | 1 |
| `prd.md` | PRD | 2 |
| `review.md` | Agent Reviews | 3 |
| `test-cases.md` | Test Cases | 4 |
| `release-notes.md` | Release Notes | 5 |
| `hc-content.md` | HC Content | 6 |
| `verification-*.md` | Verification ({date}) | 7+ |
| `retrospective-*.md` | Retrospective ({date}) | 8+ |

## Workflow

### Step 1：確認狀態 + 新鮮度檢查

1. 讀 `prds/{name}/prd.md` frontmatter 看 `outline_doc_id` / `outline_synced_at`
2. 掃描 PRD 資料夾現有 .md
3. **新鮮度檢查**：對每個 .md 比對 mtime vs `outline_synced_at`
   - 若任一 .md 比 Outline 新且未先跑 `/sync-prd`，提醒 PM
4. 告知計畫：
   - 若有 outline_doc_id：「將更新現有 Outline doc: {outline_url}，N 個 children 變動」
   - 若沒：「將建立新 Outline doc + N 個 children」
5. 等 PM 確認

### Step 2a：（dry-run only）輸出 plan 並結束

詳列即將執行的所有動作，不實際呼叫 API。

### Step 2b：建立或準備 Outline parent doc

**新建（沒 outline_doc_id）：**

1. 詢問 collection（若沒給 `--collection`，列 `mcp__plugin_cl-outline_outline__list_collections` 結果讓 PM 選；建議「PRD 收納用」collection）
2. `mcp__plugin_cl-outline_outline__create_document`：
   - title: `[PRD] {prd title from frontmatter}`
   - collectionId: {chosen}
   - text: `> Auto-generated from prds/{name}/. Source of truth: <repo URL>.\n\n## Children\n\n- Evaluation\n- PRD\n- ...`（簡短 index）
3. 記下回傳 doc id 作為 parent

**更新（已有 outline_doc_id）：**

1. `mcp__plugin_cl-outline_outline__fetch` 確認 parent 仍存在
2. `mcp__plugin_cl-outline_outline__list_documents` with parentDocumentId = parent，取現有 children list

### Step 3：對每個 .md 同步 child doc

對每個本地 .md：

#### Case A：local 有檔、Outline child 有

用 `/patch-outline-safely` patch（whole-doc replace via `mode: replace`）：

```json
[{
  "replaceText": "{full markdown content of .md, frontmatter stripped}",
  "mode": "replace"
}]
```

patch-outline-safely 會做 pre/post-flight 驗證，避免 silent fail。

#### Case B：local 有、Outline 沒（新檔案）

`mcp__plugin_cl-outline_outline__create_document`：
- title: 對照表的 child doc title
- parentDocumentId: parent doc id
- text: .md 完整內容（strip frontmatter）

#### Case C：local 沒、Outline 有（檔案被刪）

**保留 child doc**，不刪除（避免遺失 comment / 連結）。在 PM summary 提醒「{doc title} 在 repo 已刪除但 Outline 仍保留，可手動 archive」。

### Step 4：更新 frontmatter

寫入 `prd.md` frontmatter：
- `outline_doc_id`、`outline_url`（首次同步）
- `outline_synced_at: {ISO 8601 timestamp}`

### Step 5：回報

```markdown
✅ Outline 同步完成

- Parent: {outline_url}
- Children:
  - Evaluation ✅ updated
  - PRD ✅ updated
  - Review ⏭ created
  - Test Cases ⏭ preserved (local removed)

Last synced: 2026-05-09T11:24:00+08:00
```

## 跟 sync-gdoc 的關係

| 用途 | 用 sync-outline | 用 sync-gdoc |
|---|---|---|
| 內部 SSOT snapshot | ✅ primary | — |
| 跨團隊發現 | ✅ Outline 搜尋強 | — |
| 對外分享給沒帳號 stakeholder | — | ✅（Drive share link） |
| 客戶 / vendor 協作 | — | ✅ |

通常做法：每份 PRD 都跑 sync-outline；只在需要對外分享時加跑 sync-gdoc。

## Common Mistakes

- ❌ **直接呼叫 cl-outline `update_document`**：會 silent fail。一律走 `/patch-outline-safely`
- ❌ **mode 選錯**：用 `replace` 全文覆蓋；不用 `patch`（patch 找不到 findText 會無聲略過）
- ❌ **Frontmatter 沒 strip**：Outline child doc 不需要 markdown frontmatter，會顯示成原文
- ❌ **child doc 順序亂**：Outline 用 sortOrder 排，建議照表中 1-8 順序建，方便 PM 在 sidebar 看

## Example Invocation

```bash
# 直接同步
/sync-outline custom-field-tagging

# 先看計畫
/sync-outline custom-field-tagging --dry-run

# 新建到指定 collection
/sync-outline new-feature --collection abc-123-collection-id
```
