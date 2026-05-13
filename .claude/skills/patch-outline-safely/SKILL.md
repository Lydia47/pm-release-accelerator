---
name: patch-outline-safely
description: "**Use whenever modifying an existing Outline doc via editMode=patch** — phrases like patch outline / 安全更新 outline / 改 outline 段落 / update outline section / outline patch verify / 替換 outline 某一段 / 改 outline 內容. Wraps cl-outline update_document with pre-flight (verify findText exists, suggest similar via difflib if not) + post-flight (verify revision incremented AND content changed) checks. Mandatory wrapper for any Outline patch — direct update_document calls silently no-op when findText doesn't match. Other skills (tidy-outline-headings, etc.) call this as their patch primitive."
---

# Outline Patch Safe

`mcp__plugin_cl-outline_outline__update_document` 在 `editMode="patch"` 時，若 `findText` 沒命中文件內容會 **silent fail** — API 不報錯、revision 不變、但 patch 沒有發生。本 skill 為它加上 pre/post-flight 驗證，把 silent fail 轉成明確 error。

## 規則

- 用繁體中文回覆
- **強制**：mode 為 `patch` 或 `replace` 時必須先做 pre-flight（驗證 `findText` 存在於文件中）
- **fail-fast**：第一個 patch 失敗就 stop，回報已完成、未完成清單，不繼續執行剩下的 patch
- **revision +1 不等於成功**：可能是別人同時編輯，post-flight 一定要驗 content match
- 多行 `findText`：先 fetch content 再逐行 grep，不要假設 newline 編碼
- 每個 patch 之間 sleep 200ms（避免 rate limit）
- 禁用 `editMode="patch"` 不做 pre-flight（這就是這個 skill 存在的理由）

## 輸入

| Flag | 必填 | 說明 |
|------|------|------|
| `--doc-id` | ✅ | Outline document ID（UUID 或 short id） |
| `--patches` | ✅ | JSON list `[{findText, replaceText, mode: "patch\|append\|replace"}]`，可傳 inline JSON 或 `./path/to/patches.json` |
| `--dry-run` | — | 只跑 Phase 1 pre-flight 驗證，不執行 patch |

### Patch 物件結構

```json
{
  "findText": "OOS",
  "replaceText": "P0",
  "mode": "patch"
}
```

- `mode="patch"`：在 content 中找 `findText` 替換為 `replaceText`（pre-flight 必查）
- `mode="append"`：把 `replaceText` 追加到 content 末尾（不需 findText，pre-flight 跳過）
- `mode="replace"`：用 `replaceText` 整篇覆蓋 content（pre-flight 仍查 findText 存在以避免誤覆蓋）

## Workflow

### Phase 1 — Pre-flight 驗證

1. `mcp__plugin_cl-outline_outline__fetch(id=doc-id)` 取得 markdown content + revision number，記為 `rev_before`
2. 對每個 patch（mode 為 `patch` 或 `replace`）：grep 確認 `findText` 存在於 content
   - 多行 findText：拆成 lines，逐行 `in content` 確認（避免 `\r\n` vs `\n` 差異）
3. 任何一個 findText 不存在 → **結構化 error**：
   ```
   ❌ Pre-flight failed for patch #N
   findText (50 chars): "..."
   Suggested similar lines (top 3):
     1. "..."  (similarity 0.82)
     2. "..."  (similarity 0.71)
     3. "..."  (similarity 0.65)
   建議：重新提供 findText，或改 mode=append。
   ```
   使用 Python `difflib.get_close_matches` 找相近行
4. 全部通過 → 進 Phase 2（若 `--dry-run` 則此處 stop 並回報「Pre-flight ✅ all N patches OK, dry-run skipped execution」）

### Phase 2 — 執行 patch（非 dry-run）

5. 依序對每個 patch 呼叫：
   ```
   mcp__plugin_cl-outline_outline__update_document(
     id=doc-id,
     text=replaceText,            # mode=replace 時是整篇新內容
     editMode="patch"|"append"|"replace",
     findText=findText,           # mode=append 不傳
     replaceText=replaceText,     # mode=patch 才需要
   )
   ```
6. 每個 patch 之間 `sleep 200ms`
7. **fail-fast**：API 報錯立即 stop，回報「已完成 K 個、剩餘 M 個未執行」

### Phase 3 — Post-flight 驗證

8. 再次 `mcp__plugin_cl-outline_outline__fetch(id=doc-id)` → 取 `rev_after` 與最新 content
9. 比對 `rev_after > rev_before`；若否 → **❌ no-op 警示**（即使 API 沒報錯，內容也沒動）
10. 對每個 patch 驗 content：
    - `mode="patch"`：`replaceText` 出現於 content **且** `findText` 不再出現（除非 findText 是 replaceText 的 substring）
    - `mode="append"`：`replaceText` 在 content 末尾出現
    - `mode="replace"`：content 完全等於 `replaceText`（trim 後比對）
11. 回傳 per-patch 結果表：

   | # | findText (≤50) | mode | status | rev_before | rev_after |
   |---|----------------|------|--------|------------|-----------|
   | 1 | `OOS` | patch | ✅ | 12 | 13 |
   | 2 | `Q4 plan` | patch | ❌ no-op | 13 | 13 |

12. 結尾附最終文件 URL（從 fetch response 取，或組 `https://<workspace>.getoutline.com/doc/<urlId>`）

## Common Mistakes

- ❌ 直接呼叫 `update_document` 不做 pre-flight — silent fail 會吃掉你的 patch
- ❌ 看到 API 沒報錯就以為成功 — Outline patch 模式下 findText 不命中時 API **回 200**
- ❌ 看到 revision 變了就以為自己的 patch 上去了 — 可能是別人同時編輯
- ❌ 多 patch 失敗一個就靜默繼續 — 後續 patch 可能依賴前一個的 anchor，要 fail-fast
- ❌ 假設 `findText` 的 newline 跟 fetch 回來的一致 — Outline 內部用 `\n`，你貼來的可能是 `\r\n`
- ❌ `mode="replace"` 不做 pre-flight 就送 — 整篇被覆蓋無法復原

## Example Invocation

```bash
# 單一 patch
/patch-outline-safely --doc-id abc123 --patches '[{"findText":"OOS","replaceText":"P0","mode":"patch"}]'

# 多 patch + 從檔案讀
/patch-outline-safely --doc-id abc123 --patches ./patches.json

# Dry-run 只驗 findText 不執行
/patch-outline-safely --doc-id abc123 --patches ./patches.json --dry-run

# Append 一段到末尾
/patch-outline-safely --doc-id abc123 --patches '[{"replaceText":"\n## Update 2026-05-08\n...","mode":"append"}]'
```

## Reference MCP Tools

- `mcp__plugin_cl-outline_outline__fetch` — 取 document content + revision
- `mcp__plugin_cl-outline_outline__update_document` — 寫入（patch/append/replace 三種 editMode）
- `mcp__plugin_cl-outline_outline__list_documents` — （選）查 doc-id
