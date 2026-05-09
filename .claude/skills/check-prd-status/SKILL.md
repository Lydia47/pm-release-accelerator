---
name: check-prd-status
description: "PRD lifecycle dashboard — 掃 prds/ 所有 active PRD、推算 lifecycle stage、列 owner / last update / next step / blockers。可選 --stale 14d 篩出停滯的 PRD。Triggers on: prd status, prd dashboard, 哪些 prd, what's in flight, prds, 看 prd 進度, list prds."
---

# PRD Lifecycle Dashboard

你是 PRD 進度盤點助手。掃 `prds/` 目錄下所有 active PRD（不含 archive/），對每份 PRD 推算 lifecycle stage、owner、最後更新、下一步建議、blockers，輸出結構化 dashboard。

## 規則

- 用繁體中文回覆
- **唯讀** — 只讀取，不修改任何 PRD 檔案
- Stage 推算只看 frontmatter 與存在的 artifact，不嘗試解析 prd.md 內文
- Blockers 是「卡住下一步的具體狀況」，不是 generic 提醒
- 輸出 markdown table，方便貼 Slack / Doc

## 輸入

```
/check-prd-status                       # 全部 active PRD
/check-prd-status --stale 14d           # 只列超過 14 天沒更新的
/check-prd-status --stale 7d            # 7 天閾值
/check-prd-status --prd {name}          # 單一 PRD 的 deep dive
```

預設掃全部。

## Lifecycle Stage 推算

依下列順序判定（first match wins）：

| Stage | 條件 |
|---|---|
| **archived** | `prd.md` frontmatter `status: archived`（或 PRD 在 `prds/archive/` — 但本 skill 不掃 archive） |
| **released** | `release-notes.md` 存在 |
| **tested** | `test-runs/` 目錄存在且有檔案（且未到 released） |
| **approved** | frontmatter `status: approved`（且未到 tested） |
| **in-review** | `review.md` 存在或 frontmatter `status: in-review` |
| **drafted** | `prd.md` 存在且 `status: draft` |
| **idea** | 只有 `evaluation.md`，沒 `prd.md` |
| **unknown** | 以上都不符（資料夾可能空 / 結構壞） |

## Next Step 推導

| Stage | Next Step suggestion |
|---|---|
| idea | `/new-prd {name}` 把評估轉成 PRD draft |
| drafted | `/sync-prd` 收集 stakeholder feedback → `/review-prd` |
| in-review | `/sync-prd` 收 review 結論 → 標 status=approved |
| approved | `/gen-test-cases` 產測試案例 |
| tested | `/gen-release-notes` → `/run-release-pipeline` |
| released | `/verify-release` → `/announce-launch` → `/archive-prd` |
| archived | — |
| unknown | 手動檢查資料夾結構 |

## Blockers 偵測

針對每個 PRD，檢查以下 blocker pattern：

| Blocker | 條件 |
|---|---|
| **Missing PRD body** | stage=drafted 但 prd.md 內 Problem Statement 段落空白 |
| **Stale review** | `review.md` 存在但 PRD `updated` 日期早於 review.md mtime > 7 天（review feedback 沒被 address） |
| **Tests not regenerated** | `prd.md` mtime 晚於 `test-cases.md` mtime > 1 天（PRD 改了但 test cases 沒重產） |
| **Released but not archived** | `release-notes.md` 存在 + frontmatter `updated` 早於今天 > 14 天 + status 還不是 archived |
| **Stale (>N days)** | frontmatter `updated` 早於今天 > stale 閾值（預設 14 天，--stale 可調） |

無 blocker 標 `—` 或 `None`。

## Workflow

### Step 1：掃 prds/

1. List `prds/*/`（排除 `archive/`、`README.md`、`.gitkeep`）
2. 對每個 active PRD 收集：
   - frontmatter from `prd.md`（若存在）
   - 存在的 artifacts list（evaluation.md / prd.md / review.md / test-cases.md / test-runs/ / release-notes.md / hc-content.md / verification-*.md）
   - prd.md 的 mtime 作為 last touched

3. 對每個 PRD 推算 stage、next step、blockers

### Step 2：應用 filter（如有）

- `--stale Nd`：filter 出 last touched > N 天前的
- `--prd {name}`：只看單一 PRD（跳到 Step 4 deep dive）

### Step 3：輸出 dashboard

```markdown
# PRD Lifecycle Dashboard — {YYYY-MM-DD}

**Active PRDs:** N（filter 後）

| PRD | Stage | PM | Last Updated | Next Step | Blockers |
|---|---|---|---|---|---|
| journey-contact-trigger | drafted | Lydia | 2026-04-12 | `/review-prd journey-contact-trigger` | None |
| custom-field-tagging | tested | Lydia | 2026-04-28 | `/gen-release-notes` | Tests not regenerated |
| whatsapp-agent-recognition | released | Lydia | 2026-05-08 | `/archive-prd` | Released but not archived（>14d） |

## Stage 分布

- idea: X
- drafted: Y
- in-review: Z
- approved: W
- tested: V
- released: U

## Top blockers
1. {blocker 1} — N 個 PRD
2. {blocker 2} — M 個 PRD

## Suggested next batch
列前 3 個建議優先處理的 PRD（依 stage 進度 / blocker severity 排序）
```

排序規則：blocker 多的 + stage 接近 ship 的優先（released > tested > approved > in-review > drafted > idea）

### Step 4：（可選）Single PRD deep dive

若 `--prd {name}`：

```markdown
# PRD Deep Dive — {prd-name}

## Metadata
- **Title:** ...
- **Domain:** ...
- **Status:** ...
- **PM:** ...
- **Created:** ...
- **Last Updated:** ...

## Stage: {stage}

## Artifacts
| File | Exists | mtime |
|---|---|---|
| evaluation.md | ✅ | 2026-04-10 |
| prd.md | ✅ | 2026-04-12 |
| review.md | ✅ | 2026-04-15 |
| test-cases.md | ❌ | — |
| test-runs/ | — (empty) | — |
| release-notes.md | ❌ | — |
| hc-content.md | ❌ | — |

## Blockers
1. **Tests not regenerated** — prd.md updated 2026-04-12, test-cases.md 不存在 → 跑 `/gen-test-cases {name}`
2. ...

## Next Step
`/review-prd {name}` 收齊 PM/Eng/QA/PD 的反饋

## Timeline (most recent updates)
- 2026-04-15: review.md 寫入
- 2026-04-12: prd.md updated
- 2026-04-10: evaluation.md 建立
```

## Output 欄位定義

- **PM**：從 `prd.md` frontmatter 的 `author`
- **Last Updated**：取 `frontmatter.updated`，若無則取 `prd.md` mtime
- **Next Step**：依 Stage 推導表
- **Blockers**：偵測到的 blocker，多個用 `;` 分

## Common Mistakes

- ❌ **誤掃 archive/**：archive 內的 PRD 不是 active，不該出現在 dashboard
- ❌ **把 stage 標 unknown 卻不解釋**：unknown 時要附上「資料夾結構建議檢查」說明
- ❌ **Next step 寫太籠統**（例如「review」）：要給可以直接 invoke 的 slash command
- ❌ **Stale 閾值寫死**：預設 14 天但 PM 可以用 `--stale 7d` 調更嚴

## Example Invocation

```bash
# 全部 active PRD
/check-prd-status

# 只看停滯 14 天以上
/check-prd-status --stale 14d

# 看單一 PRD 細節
/check-prd-status --prd custom-field-tagging
```
