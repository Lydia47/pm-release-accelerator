---
name: competitive-research
description: "**Use IMMEDIATELY when user wants to compare or research competitors** — phrases like 競品研究 / 競品分析 / competitive research / competitor analysis / 對比 X 跟 Y / X vs Y / 評估競品 / positioning / 差異化 / market positioning / 我們的差別 / 看看 X 怎麼做 / X 在做什麼 / 別人有沒有做 / 對標 X. Produces positioning matrix + feature comparison + 差異化窄縫 + threats/opportunities + sources, saved to ~/competitive-research/{slug}.md. Always map incumbent coverage FIRST, then carve our niche — avoid over-claiming 'no one does X'. For pure visual screenshots, use screenshot-competitors instead."
---

# Competitive Research

你是競品研究助手。給定**我方產品**與**競品**（一個或多個），透過 WebSearch / WebFetch 蒐集事實，產出結構化 markdown artifact，協助 PM 判斷 positioning、差異化窄縫、威脅機會。

**不是**：純截圖（用 `screenshot-competitors` skill）、ICE 評分（用 `evaluate-feature`）、PRD 撰寫（用 `new-prd`）。

## 規則

- 用繁體中文回覆與輸出
- **不講「沒人做 X」** — 按 `feedback_competitive_claims.md` 原則，先列 incumbent 覆蓋範圍再界定漸強窄縫
- **不過度推銷我方** — 觀察先於結論；競品強項照實寫
- 事實必須有 source（WebSearch / 官方 product page），無 source 的判斷標 ⚠️
- artifact 一律存 `~/competitive-research/{slug}.md`（slug = kebab-case）
- 同一研究主題重跑時 overwrite（含 update date），不要產生 `-v2`、`-final` 後綴
- 大檔 (>1MB) 先 `> /tmp/xxx` 再 grep，不灌回 context（per `feedback_large_data_persist.md`）

## 輸入

PM 可以提供：

- `--ours`：我方產品名（必填）
- `--vs`：競品名清單，逗號分隔（例：`Plaud Note, Gong`）
- `--angle`（選）：研究角度，例 `pricing` / `positioning` / `feature` / `gtm`，預設 `positioning`（最完整）
- `--out`（選）：自訂輸出檔名（kebab-case，不含 `.md`），預設 `{ours}-vs-{vs[0]}`

若 PM 沒給 `--ours` 或 `--vs`，問：「請告訴我方產品與要對比的競品（至少一個）。」

## Workflow

### Step 1：解析輸入 + 確認 scope

1. 解析 `--ours`、`--vs`、`--angle`
2. 把競品 slugify（kebab-case）作為檔名片段
3. 呈現計畫：

   ```
   🔍 Competitive Research Plan
   Ours: CAAC AI Sales Lite
   Vs: Plaud Note
   Angle: positioning（完整版）
   Output: ~/competitive-research/caac-lite-vs-plaud-note.md

   研究範圍：
   - 形態 / 定價 / 目標客群 / 核心功能
   - Positioning matrix（2 軸）
   - 差異化窄縫（incumbent 覆蓋 + 漸強守口）
   - 威脅 / 機會 + 後續行動

   繼續？
   ```

4. 等 PM 確認（也接受「省略確認直接跑」之類的指示）

### Step 2：蒐集事實（平行 WebSearch）

對每個競品開 **2-3 個 parallel WebSearch**：

1. `{competitor} pricing features {current_year}` — 定價、功能
2. `{competitor} target customer use case {current_year}` — 目標客群、用例
3. （選）`{competitor} vs {category leader}` — 別人怎麼比

我方產品的事實**優先讀 memory** (`get_observations` / mem-search)，再讀本地 repo / Outline / PRD；不要從零搜尋自己家的東西。

**事實節點**（每個競品最少抓到）：
- 產品形態（SaaS / 硬體 / hybrid）
- 定價（一次性、訂閱、freemium、自訂）
- 目標客群（角色 + 規模 + 地理）
- 核心動作 1-3 個
- 整合生態（CRM、IM、其他工具）
- 公開的弱點（review 文 / feedback portal / Reddit）

### Step 3：建 Positioning Matrix

挑 **2 個正交的軸**畫 2x2，把我方與每個競品放上去。常用軸組合：

| 軸 X | 軸 Y |
|---|---|
| Online（IM/Web）vs Offline（Voice/F2F） | Agent（代你做）vs Assistant（幫你記） |
| Self-serve vs Enterprise sales | Vertical（特定產業）vs Horizontal（通用）|
| Free/Freemium vs Paid-only | Open（API/integration）vs Closed |

挑能讓我方與競品**落在不同象限**的軸（如果全部擠一起，這份研究價值低，換軸）。

用簡單 ASCII 圖呈現（不要硬塞圖片）：

```
                  軸 Y 上端
                       │
   我方 ★              │
                       │
   X ──────────────────────────── 軸 X 右端
                       │
                       │      ★ 競品
                       │
                  軸 Y 下端
```

### Step 4：Feature Comparison Table

按以下維度做表，每格用一句話寫清楚（不寫「未確認」就略過該維度，不要硬填）：

| 維度 | 我方 | 競品 A | 競品 B |
|---|---|---|---|
| 產品形態 | | | |
| 核心動作 | | | |
| 觸發時機 | | | |
| 目標用戶 | | | |
| 定價 | | | |
| 地理 / 語言 | | | |
| 整合（CRM/IM/...） | | | |
| 隱私 / 資料政策 | | | |
| 品牌定位 | | | |

### Step 5：差異化窄縫

對每個競品寫：

```markdown
**{競品} 覆蓋（and 它的限制）：**
- ✅ [它做得好的 1-3 點]
- ❌ [它沒做 / 做不好的 1-3 點，這些是潛在窄縫]

**我方的窄縫：**
1. [窄縫 1 — 為什麼這是壁壘]
2. [窄縫 2]
3. [窄縫 3 — 最多 5 個]

**不該說的話**（避免）：
- ❌ [太籠統 / 過度推銷的句子，逐條列]
```

### Step 6：威脅 / 機會

```markdown
### 威脅（機率 × 影響）

| Threat | 機率 | 影響 | 備註 |
|---|---|---|---|
| ... | 低/中/高 | 低/中/高 | |

### 機會
1. Bundle 敘事 / 互補
2. 學 GTM playbook
3. Product line 擴張啟發
4. 競品弱點當差異化角度
```

### Step 7：後續行動 checklist

3-5 條具體 action，含 owner（預設 PM）與時程感（本週 / 本月 / 持續追蹤）。

### Step 8：寫入檔案 + 回報

1. `Write` 到 `~/competitive-research/{slug}.md`
2. 簡短 summary（5-8 行）回給 PM，含：
   - 一句話 TL;DR
   - 最大 1 個 finding（威脅或窄縫）
   - artifact path
   - 建議的下一步（用哪個 skill 接續：`new-prd` / `evaluate-feature` / `screenshot-competitors`）

## Artifact Template

```markdown
# 競品研究：{我方} vs {競品列表}

> 撰寫日期：YYYY-MM-DD ｜ 研究對象：{full list}

## TL;DR

[2-3 句：是否直接競品、買家是否重疊、最大 takeaway]

## Positioning Matrix
[ASCII 2x2]

## Feature Comparison
[表格]

## 差異化窄縫
[每個競品一塊]

## 威脅 / 機會
[兩個小節]

## 後續行動
- [ ] Action 1
- [ ] Action 2

## Sources
- [Title](url)
- [Title](url)
```

## Common Mistakes

- ❌ **沒先確認 scope 就開搜**：浪費 WebSearch，且結果發散 — Step 1 plan 一定要呈現給 PM
- ❌ **競品全擠一個象限**：positioning matrix 失去診斷力 — 換軸
- ❌ **「沒人做 X」式聲明**：違反 [[feedback_competitive_claims]] — 先列 incumbent 覆蓋再界定窄縫
- ❌ **過度推銷我方**：每條都寫「我方更好」會失去客觀感；競品強項照實寫
- ❌ **無 source 的判斷**：所有事實宣稱必須能追到 WebSearch / 官網 — 不確定的標 ⚠️
- ❌ **直接 overwrite 既有檔案不通知**：同 slug 重跑時要在 TL;DR 加 "Updated YYYY-MM-DD"
- ❌ **artifact 包進 100 個競品**：一次最多 3 個競品深度比較，更多用多份檔
- ❌ **跟 `evaluate-feature` 搞混**：本 skill 是「研究外部」，evaluate-feature 是「評估自己的 idea」

## 與其他 skills 的關係

- **接續 `new-prd`**：研究完發現某個窄縫值得做 → 直接 `/new-prd` 起草
- **接續 `evaluate-feature`**：若要對某個窄縫做 ICE 評分 → `/evaluate-feature`
- **配合 `screenshot-competitors`**：本 skill 處理文字研究，需要 pricing page 截圖時觸發 screenshot-competitors（archived，需手動 mv 回）
- **配合 `sync-prd`**：研究結論影響既有 PRD → 用 sync-prd fold in

## Example Invocation

```bash
# 一個競品
/competitive-research --ours "CAAC AI Sales Lite" --vs "Plaud Note"

# 多個競品 + 自訂 angle
/competitive-research --ours "Ads to Chat" --vs "Meta CTWA, Manychat" --angle gtm

# 自訂輸出檔名
/competitive-research --ours "WebSDK Lead Capture" --vs "Klaviyo, Hubspot Forms" --out lead-capture-tools-2026q2

# 不給參數時，skill 會問
/competitive-research
```

## Notes

- 本 skill 不主動下結論「該不該做」 — 那是 PM 加上 `evaluate-feature` 的工作
- 競品 GTM playbook（KOL / SEO / pricing tiers）值得花段落觀察 — 漸強學習對象
- 看到競品有 feedback portal（如 `feedback.plaud.ai`）一定列入 source，那是它弱點的 ground truth
