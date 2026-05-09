---
name: sync-spec-to-prd
description: "Reverse sync —— 把 spec.md 的改動回填到同 domain 的 active PRD。從 git diff 抓最近 spec 變動，對每個 active PRD 提示是否補進 Spec Delta；用於 hot-fix spec 後保持 PRD 與 spec 一致。Triggers on: spec to prd, spec sync back, 把 spec 改回 prd, reverse sync spec, hot-fix spec, spec drift."
---

# Sync Spec → PRD（Reverse Sync）

你是 spec ↔ PRD 雙向同步助手。Dual SSOT 設計下，正向流程是 PRD → archive → spec.md 更新；但偶爾會直接改 `specs/{domain}/spec.md`（hot-fix、合規修正、文件 cleanup），這時 active PRD 跟 spec 會偏離。本 skill 把 spec 改動反向回填到同 domain 的 active PRD 的「Post-PRD Spec Changes」段落，保持兩者可追蹤一致。

## 規則

- 用繁體中文回覆
- **每個 PRD 修改前都要 PM 確認 yes/skip**
- spec diff 從 git 取，不憑記憶
- 寫入 PRD 時 append 到 Spec Delta 之後的 Post-PRD Spec Changes 段落（新增段落如不存在），**不修改原 PRD body**
- 寫完更新 frontmatter `spec_synced_at: {ISO 8601}`

## 輸入

```
/sync-spec-to-prd <domain>                       # 對 specs/{domain}/spec.md 跑
/sync-spec-to-prd <domain> --since HEAD~3        # 自指定 commit 起算
/sync-spec-to-prd <domain> --since 2026-04-01    # 自指定日期起算
/sync-spec-to-prd --spec specs/journey/spec.md   # 用 path 也行
```

預設 `--since` 為 last commit on file（即「最近一次 spec 改動」）。

## Workflow

### Step 1：解析 input

1. 從 `<domain>` 或 `--spec` 推 spec 檔案路徑
2. 確認 `specs/{domain}/spec.md` 存在
3. 確定 `--since` 起點（commit hash / 日期 / 預設 last commit on this file）

### Step 2：從 git 抓 spec diff

```bash
git log --since="{date}" -- specs/{domain}/spec.md
git diff {since-hash}..HEAD -- specs/{domain}/spec.md
```

或對 last commit：

```bash
git log -1 --format="%H %ai %s" -- specs/{domain}/spec.md  # 取最近 commit
git show {commit} -- specs/{domain}/spec.md
```

整理 diff 成結構化變更清單：

| # | Change Type | Section | Before | After | Source Commit |
|---|---|---|---|---|---|
| 1 | Added | REQ-JRN-042 | (new) | "Journey contact trigger 支援 ..." | abc123 |
| 2 | Modified | Capability "trigger" | "...只支援 broadcast" | "...支援 broadcast + journey" | def456 |
| 3 | Removed | REQ-JRN-013 | "Trigger 必須..." | (removed) | ghi789 |

若無變動或 diff 為空，回報「指定區間內 spec 無變動」並結束。

### Step 3：列出同 domain 的 active PRD

掃 `prds/*/prd.md`（排除 archive/），filter frontmatter `domain == {domain}`：

```
找到 N 個 active PRD（domain={domain}）：
1. journey-contact-trigger (status=approved)
2. journey-datetime-scheduled (status=draft)
3. journey-whatsapp-node (status=tested)
```

若無 active PRD：「指定 domain 沒有 active PRD，spec 改動無需 sync。」結束。

### Step 4：對每個 (PRD × spec change) 提示 PM 決定

呈現 matrix 給 PM：

```markdown
## Sync Decisions Required

domain: journey | spec changes: 3 | active PRDs: 3

### Change #1：Added REQ-JRN-042（abc123）
> "Journey contact trigger 支援 ..."

| PRD | 相關性建議 | 動作 |
|---|---|---|
| journey-contact-trigger | **High**（直接相關） | [ ] update / [ ] skip |
| journey-datetime-scheduled | Low | [ ] update / [ ] skip |
| journey-whatsapp-node | Medium | [ ] update / [ ] skip |

### Change #2：Modified "trigger" capability（def456）
> ...

[類似 table]

### Change #3：Removed REQ-JRN-013（ghi789）
> ...

[類似 table]
```

「相關性建議」用 keyword overlap heuristic：
- High：spec 變動的 keyword 出現在 PRD title / Problem Statement / Spec Delta
- Medium：出現在 User Stories / Proposed Solution
- Low：未出現但同 domain

PM 對每個 cell 標 update / skip。**等 PM 全部標完才進 Step 5**。

### Step 5：寫入 PRD 的「Post-PRD Spec Changes」段落

對每個被標 update 的 (PRD, change) pair：

1. 讀 `prds/{prd-name}/prd.md`
2. 找「## Post-PRD Spec Changes」段落（如不存在，append 在 「## Spec Delta」之後）
3. Append 一個 entry：

   ```markdown
   ## Post-PRD Spec Changes

   <!-- spec 直接改動的回填紀錄；正常 lifecycle 改動應透過 Spec Delta + /archive-prd -->

   ### {YYYY-MM-DD} | {commit-hash}
   - **Type:** Added / Modified / Removed
   - **Section:** {spec section / REQ ID}
   - **Change:** {summary}
   - **Source:** specs/{domain}/spec.md @ {commit} ({author})
   - **Impact on this PRD:** {PM 補充 1-2 句，或留 TBD}
   ```

4. 更新 PRD frontmatter：
   - `updated: {today}`
   - `spec_synced_at: {ISO 8601 timestamp}`
   - `spec_synced_to: {commit-hash}`

5. 對每個被修改的 PRD 顯示 final diff 讓 PM confirm 後才寫檔。

### Step 6：摘要回報

```markdown
## Sync Summary

- domain: {domain}
- spec changes processed: 3 / 3
- PRDs updated: 2
  - journey-contact-trigger ← change #1, #2
  - journey-whatsapp-node ← change #2
- PRDs skipped: 1
  - journey-datetime-scheduled (PM 標 skip 全部)

每份 PRD 已加 "Post-PRD Spec Changes" 段落，frontmatter `spec_synced_at` 已更新。
```

提醒 PM：
> 若這次 spec change 來自 hot-fix（非 PRD lifecycle），考慮在這幾份 PRD 的 Spec Delta 段落補一筆「上線時 hot-fix 已調整 X」，以免下次 archive 時 spec delta 跟 spec 已經一致導致誤判。

## Common Mistakes

- ❌ **覆寫 PRD 主要區塊**：`Post-PRD Spec Changes` 段落是 append-only，**不要**改 Background / Goals / User Stories / Spec Delta 等
- ❌ **沒問 PM 自己決定相關性**：keyword overlap 只是 heuristic 建議，最終由 PM 決定
- ❌ **重複寫入相同 commit**：寫前先檢查目標 PRD 是否已有 same commit-hash entry，避免重複
- ❌ **跨 domain 強行對齊**：本 skill 只處理 same domain；不同 domain spec 改動不會自動傳到別 domain 的 PRD

## Why this skill exists

dual SSOT 架構下，正常流程是 PRD → archive → spec 更新（前向）。但實務上會有：

- **Hot-fix**：上線後發現 spec 描述跟實作不符，直接改 spec
- **合規 / 文件 cleanup**：legal 或文件管理需求，直接改 spec
- **Reverse-engineering 後修正**：`/gen-product-spec` 反向產出後手動修正

這些動作會讓 active PRD 跟 spec 偏離。沒有這個 skill 的話，下次 `/archive-prd` 套 Spec Delta 時可能誤判（spec 已有此項就跳過 vs 真的需要更新），或 PM 看 PRD 跟 spec 對不上感到困惑。

`sync-spec-to-prd` 不嘗試「自動完美同步」，只做：明確顯示 diff、讓 PM 決定每個 PRD 是否要記錄這筆變動。記錄後 audit trail 完整。

## Example Invocation

```bash
# 對 journey domain spec 最近改動跑
/sync-spec-to-prd journey

# 從特定 commit 起
/sync-spec-to-prd journey --since abc1234

# 從特定日期起
/sync-spec-to-prd broadcast --since 2026-04-01

# 用 spec path 直接指
/sync-spec-to-prd --spec specs/audience/spec.md
```
