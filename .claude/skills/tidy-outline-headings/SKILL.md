---
name: tidy-outline-headings
description: "**Use IMMEDIATELY when user wants to restructure an Outline doc's heading hierarchy or emoji usage** — phrases like tidy outline / outline 不好讀 / outline 結構亂 / 順 outline / restructure outline / heading hierarchy / outline 大小標 / outline 標題層級 / outline 標題重整 / clean outline structure / outline ToC 亂 / outline 標題 emoji / 把 outline 結構整一整. Applies 6 rules in order: 內文從 H2 起跳 / 不跳級 / >8 items 必分組 / H3 不當 label / emoji 只放母章節 / 風格統一. Diagnoses → proposes restructure mapping → applies via patch-outline-safely → re-fetches to verify."
---

# Tidy Outline Headings

讀 Outline doc → 用 6 條原則診斷標題層級與 emoji 使用 → 提出 restructure mapping → 套用更新 → re-fetch 驗證。

## 觸發時機

- Lydia 提「outline 標題層級 / 大小標亂 / outline 不好讀 / restructure outline / 順結構」
- 看到任何 Outline doc 的 ToC：平鋪超過 8 個 H2 / H3 跳級 / 多重 H1 / emoji 零散
- PRD 寫完同步到 Outline 後，發現呈現視覺亂

## 6 條結構原則

> 這 6 條按優先順序排列，由「最高代價」往「次要 polish」。改動同一個 doc 時也依序套用。

**1. 內文最高層從 `## H2` 開始（最重要）**

Outline 的 doc title 已是視覺最大層級，內文再開 `# H1` 等於有兩個最大標題互相搶眼，sidebar / ToC 也會多一層冗餘。所有 `# H1` 一律降到 `## H2`。

**2. 層級漸進不跳級**

`## H2 → ### H3 → #### H4`，禁止 `## H2 → #### H4`。每升一層必須有對應 parent 存在，否則大綱導覽列看起來會像斷掉。

**3. 同層級超過 ~8 個 item 就分組**

ToC 平鋪 12 個 H2 讀者掃不完。加一個母章節 H2 把 items 收成 H3：

```
❌ ## Feature A / ## Feature B / ... / ## Feature G (7 個平鋪)
✅ ## 🧩 Features
     ### Feature A / ### Feature B / ... / ### Feature G
```

**4. H3 不要當「區段標籤」用**

`User Story / Test Cases / 商業邏輯 / Phase 2` 這類在每個 Feature 都會出現的「結構欄位」不是真正的小節，是排版 label。當 H3 會讓 ToC 爆炸（7 features × 4 標籤 = 28 個 H3）。改用粗體段落：

```
❌ ### User Story（v1）
❌ ### Test Cases

✅ **User Story（v1）**
✅ **Test Cases**
```

判斷準則：「這個 heading 值得在 sidebar / ToC 被點到嗎？」如果不值得，就不該是 heading。

**5. Emoji 只放在 H2 母章節**

母章節 emoji 當視覺 anchor 效果好：📋 Overview / 🎯 Flows / 🧩 Features / 🔌 API / ⚙️ NFR。但同份 doc 內 H3 以下加 emoji 會稀釋 anchor 效果、變成雜訊。

不要在 `### Feature E — ⚙️ SRT Setting Flow` 這種 H3 加 emoji。emoji 想保留資訊（例如 ⚙️ 表設定）時，移到正文 inline 或 callout 而非 heading。

**6. 統一就是好（最後 pass）**

要嘛全部加 emoji 要嘛都不加；要嘛全部用 H3 sub-label 要嘛全部用粗體 label；要嘛全部用 `Feature X — 短名稱` 要嘛全部用 `Feature X · 短名稱`。**選一種風格貫徹整份 doc**，不要混用。

## 工作流程

### 1. Fetch
```
mcp__plugin_cl-outline_outline__fetch(resource="document", id=<urlId 或 full URL>)
```
從 URL 抓 doc。Outline URL 格式：`https://outline.cresclab.site/doc/{title-slug}-{urlId}` — `urlId` 就是 fetch 的 id。

### 2. Diagnose
列出所有 heading 與層級。針對 6 條原則找問題：

```
原則 1: H1 在內文出現了 N 次 → 列出位置
原則 2: 跳級在 X 處 → 列出 parent/child
原則 3: H2 平鋪 N 個 → 提議分組
原則 4: H3 當 label 的有哪些 → 列出
原則 5: emoji 分佈 → 一致性檢查
原則 6: 命名 / 格式風格是否統一
```

### 3. Propose
給 Lydia 一份 **mapping table** + **重整後骨架預覽**：

```
| 現在 | 改成 | 理由（套用哪條原則）|
|---|---|---|
| # Feature Spec | ## 📋 Overview | 原則 1 + 5 |
| ## Feature A | ### Feature A | 原則 3（分組到 ## Features 母章節） |
| ### User Story | **User Story** | 原則 4 |
| ...
```

加一個骨架 preview block 給 Lydia 看 ToC 預期長相：

```
（doc title）
## 📋 Overview
   ### Version history
   ### v1 範圍
   ...
## 🎯 Flows
## 🧩 Features
   ### Feature A
   ### Feature B
   ...
```

### 4. Confirm
等 Lydia 確認、修改或要求調整。

### 5. Apply

依改動規模選工具：

- **> 10 處 heading 變動**：用 `mcp__plugin_cl-outline_outline__update_document(editMode="replace")` 全文替換。一次到位，避免多次 patch 互踩。
- **≤ 10 處且分散**：用 `Skill: patch-outline-safely`（包裝 update_document 的 patch mode + pre/post-flight 驗證）逐筆 patch。
- **保險**：套用前先 `fetch` 一次取最新 body，避免 race condition。
- **替換警告**：`replace` mode 會丟失「無法用 markdown 表達的 rich formatting」（highlights、comments、table column widths）。Lydia 個人 SSOT 通常無此問題；多人協作的 doc 要警告。

### 6. Verify
re-fetch doc，跑一次 diagnose（步驟 2）確認所有問題都消失。把 before / after 的 heading 數量比較給 Lydia。

### 7. Report
給 Lydia 一份簡短報告：

```
✅ 套用完成
- H1 → H2：5 處
- H2 → H3（Features 分組到母章節）：7 處
- H3 → 粗體 label：21 處
- API 分組：合併為單一 ### + 2 個粗體 sub-section
- Emoji 統一：所有 ## 母章節 + 移除 H3 emoji

Before: 47 個 heading（5 H1 / 18 H2 / 24 H3）
After:  17 個 heading（0 H1 / 5 H2 / 11 H3 / 1 H4）
```

## Common Patterns Cheat Sheet

### Pattern: 多重 H1
```
❌                          ✅
# Section 1                 ## Section 1
# Section 2                 ## Section 2
# Section 3                 ## Section 3
```

### Pattern: 跳級
```
❌                          ✅
# A                         ## A
### A.1   (跳了 H2)         ### A.1
```

### Pattern: Item 平鋪太多
```
❌                          ✅
## Item 1                   ## 🧩 Items
## Item 2                     ### Item 1
...                           ### Item 2
## Item 12                    ...
                              ### Item 12
```

### Pattern: H3 當區段 label
```
❌                          ✅
## Feature A                ## Feature A
### User Story                **User Story**
### Test Cases                **Test Cases**
### 商業邏輯                   **商業邏輯**
```

### Pattern: Emoji 零散
```
❌                          ✅
## Version history          ## 📋 Overview
## ⚙️ Product Term            ### Version history
## Flow 1                     ### Product Term
## 🎯 MVP 概覽              ## 🎯 MVP 流程
                              ### Flow 1
```

## 注意事項

- **大檔案先 fetch 全文落地**：>3000 token 的 doc 先存 `/tmp/outline-{slug}.md` 再 transform，避免 context 拼裝出錯。對於 SSOT spec 這類大 doc 必做。
- **保留 callout / table / code block / 圖**：純 heading 結構整理，不動內文。確認 transform 後 word count 與原本 ≈ 相同（差距 < 5%）。
- **emoji 本身有資訊不刪**：例如 `⚙️` 表設定、`🎯` 表目標 — 不要無腦 strip，只在它與本原則衝突時移位（從 H3 移到母章節 H2 或正文 callout）。
- **保留現有 v 系列備註**：版本表、`> 📌`、`> ⚠️` 等 metadata callout 一律保留原樣。
- **每次完成後問 Lydia 要不要 memory**：若該 doc 系列有特殊慣例（如 Feature 命名格式 / 特殊 emoji 集），存成 project memory 可累積。

## 與其他 skill 的關係

- `patch-outline-safely`：本 skill 的局部 patch 後端工具。本 skill 是「結構決策」，它是「安全套用」。
- `sync-outline`：把 PRD markdown 同步到 Outline。本 skill 是 sync 完成後的「視覺打磨」步驟，可在 sync 完成後問 Lydia 要不要順手 tidy。
- `pull-outline-comments`：讀別人留的 comment。跟本 skill 無直接關係但常一起出現在 Outline workflow 中。
