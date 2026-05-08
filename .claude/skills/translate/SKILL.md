---
name: translate
description: "UI 字串翻譯流程：填 zh-TW → 自動翻譯 EN/TH/JA → cl-locales 寫回 Sheet → 推 Slack review → cl-locales publish 發到 Firebase Storage。Triggers on: translate, 翻譯, locales, 多國語言, ui translation."
---

# Translation Flow

你是漸強的多語產品在地化專家。當 PM 填好 zh-TW UI 字串後，自動翻譯到 EN/TH/JA、用 `cl-locales` CLI 寫回同一份 Google Sheet（含 AI signature），推 Slack review request 附 PRD 連結，等 reviewer 確認後透過 `cl-locales publish` 發到 staging 與 production。

## 規則

- 用繁體中文回覆
- UI label 必須與線上產品一致 — 用 sheet 既有翻譯為 source of truth
- 同一個術語在整份 sheet 中必須一致
- 不確定的詞用 `[REVIEW]` 標記，不要猜
- 寫 Sheet 與 publish 都先 `--dry-run --json` 預覽，PM 確認後才執行
- production publish **絕對需要 PM 明確授權**
- 寫入時 `cl-locales` 會自動加 AI signature（🤖 [AI Agent]）

## 前置：cl-locales CLI

本 skill 依賴 `cl-locales`（取代舊的 `locales-publish`）。安裝路徑以你的環境為準：

| 安裝方式 | 指令呼叫 |
|---|---|
| Claude Code plugin（chatbotgang/cclab） | `cl-locales` 直接呼叫 |
| 手動 clone | `~/.claude/skills/cl-locales/scripts/locales-cli` |

下面 workflow 用 `cl-locales` 當代稱；若你是手動安裝，把它替換成完整路徑。

支援 apps：`caac`, `maac`, `liff`, `admin-center`  
支援語言：`zh-hant`, `en`, `th`, `ja`

首次使用：`cl-locales login`（瀏覽器登入 Firebase）

## 輸入

PM 可提供以下任一種：

1. **翻譯 keys**（必填）：
   - **Google Sheet 範圍**：例 `MAAC main content rows 3090-3095`
   - **Key list**：例 `leadCapture.form.title = 收集聯絡資訊`
   - **`auto`**：AI 掃描 sheet 找 zh-TW 已填但 EN/TH/JA 為空的列
2. **Product**（必填）：`maac` / `caac` / `admin-center` / `liff`
3. **PRD 連結**（選填）：Google Doc URL，會附在 Slack review request 裡
4. **目標語言**（選填）：`en`, `th`, `ja` 的子集，預設全部

## Workflow

### Phase 1：讀取 source 與載入 glossary

1. **找出要翻譯的 keys**：
   - **`auto` 模式** — 用 `gws sheets +read` 掃整份 sheet 找 zh-hant 有值但 en/th/ja 缺值的列：
     ```bash
     gws sheets +read --spreadsheet 1XWSlNk8b5G9ru2mNrE3O7lsiA-yHjC4nkV_MkQEU_Fk \
       --range '<TAB>!A1:E5000'
     ```
     Tab 對應：`MAAC main content`, `CAAC main content`, etc.
   - **指定 keys** — 用 `cl-locales lookup` 查現況：
     ```bash
     cl-locales lookup --app caac --key "leadCapture.form" --json
     ```
   - 列出來請 PM 確認再進 Phase 2

2. **載入翻譯指南**：
   ```bash
   gws drive files export --params '{"fileId":"1Rhg8d0CbtfTfFGpqiBH5Eui-ML1T2wxQGfS_imjThwE","mimeType":"text/plain"}'
   ```

3. **建工作 glossary** — 用 `cl-locales lookup --json` 抓相關 prefix 的既有翻譯當術語表

### Phase 2：翻譯

對每個 key 產生 EN/TH/JA：

#### English (en-US)
- 專業 SaaS UI 用語，清楚、直接、任務導向
- 沿用 sheet 既有英文詞
- Active voice，第二人稱「you」

#### Thai (th)
- 正式商務泰文（ภาษาทางการ），專業但平易近人
- 沿用既有泰文用語
- 不要從中文逐字直譯

#### Japanese (ja)
- 敬語體（です/ます）
- IT 詞彙優先用片假名

#### 通用規則
- 產品名不翻：MAAC、CAAC、Crescendo Lab 保留原文
- UI label 跟既有翻譯保持一致
- 不確定標 `[REVIEW: term — suggested translation]`

把翻譯以表格呈現給 PM：

```
| key | zh-TW | EN | TH | JA |
```

### Phase 3：用 cl-locales 寫回 Sheet

PM 確認後，**先 dry-run 預覽，再執行**。

#### 全新 keys（add）

```bash
# 預覽
cl-locales add --app maac --batch-json '[
  {"key":"leadCapture.form.title","zh-hant":"收集聯絡資訊","en":"Collect contact info","ja":"連絡先を収集","th":"เก็บข้อมูลติดต่อ"},
  {"key":"leadCapture.form.submit","zh-hant":"送出","en":"Submit","ja":"送信","th":"ส่ง"}
]' --dry-run --json
```

呈現預覽結果給 PM，確認後執行（拿掉 `--dry-run`）。

#### 既有 keys 補語言（update）

```bash
# 預覽
cl-locales update --app maac --batch-json '[
  {"key":"existing.key.a","en":"New English","ja":"新しい日本語"},
  {"key":"existing.key.b","th":"ใหม่"}
]' --dry-run --json
```

PM 確認後執行。

#### 注意

- `cl-locales` 會自動：pre-check（重複 / 缺值會整批拒絕）→ 寫入單一 contiguous range（add）或 batchUpdate（update）→ 加 AI signature → 讀回驗證
- **不要直接用 `gws sheets values update`** — cl-locales 的 batch + 驗證機制更安全
- 失敗時根據錯誤訊息：
  - `already exists` → 改用 `update`
  - `not found` → 改用 `add`
  - `Column layout mismatch` → 跑 `cl-locales header --app <X>` 查 schema

### Phase 4：發 Slack review

自動發給對應 reviewer：

1. **TH review** → Channel `C02KEBW93JT`，Reviewer Oat（`U04UP7B83AN`）
2. **JA review** → Channel `C085FL7Q23C`，Reviewer Hisae Ishikura（`U08BNF3S45U`）
3. **EN review** → 問 PM 要不要發、發給誰

訊息格式：
```
`Request for Review`
• Assignee: <@USER_ID>
• Translations: https://docs.google.com/spreadsheets/d/1XWSlNk8b5G9ru2mNrE3O7lsiA-yHjC4nkV_MkQEU_Fk/edit
• Keys: [list]
• Reference doc: [PRD link if provided]
Please review the {LANG} translations and confirm. Thank you!
```

記下 message timestamp。告知 PM：「已發送 review request。reviewer 確認後跟我說『confirmed』或『TH confirmed』/『JA confirmed』，會自動進到發布階段。」

### Phase 5：吸收 reviewer 回饋（如有）

PM 回報修正時用 `cl-locales update` 套同樣 dry-run → confirm → execute 流程：

```bash
cl-locales update --app maac --key existing.key --th "修正後的泰文" --dry-run --json
```

PM 確認後拿掉 `--dry-run` 執行。

### Phase 6：Publish 到 Firebase Storage

PM 確認 review 完成（"confirmed"、"all confirmed"）：

1. **Dry-run 預覽**：
   ```bash
   cl-locales publish --app maac --dry-run --json
   ```
   秀出 added / removed / modified keys 摘要

2. **若只翻部分 keys**，加 `--keys` 過濾：
   ```bash
   cl-locales publish --app maac --keys leadCapture.form.title leadCapture.form.submit --dry-run --json
   ```

3. **Publish staging**（預設環境）：
   ```bash
   cl-locales publish --app maac --yes
   ```

4. **Publish production** — 問 PM：「Staging 已更新。確認要發 production 嗎？這會影響線上用戶。」
   ```bash
   cl-locales publish --app maac --env production --yes
   ```
   **沒有 PM 明確同意絕對不發 production。**

5. **認證錯誤處理**：
   - "Not logged in" → 請 PM 跑 `! cl-locales login`（會開瀏覽器）
   - "gws authentication failed" → 請 PM 跑 `! gws auth login`
   - "Unable to parse range" → 升級 gws CLI 到 ≥ 0.13.3：`! pnpx @googleworkspace/cli`

6. **完成回報**：「翻譯已發布到 staging / production，共 X 個 keys。」

### Phase 7：（可選）同步 local locale cache

提醒 PM 在對應的 frontend repo 跑 locale sync 讓 dev server 撈最新翻譯。常見 npm script 名稱：`cacheLocale`、`downloadLocales`。

## End-to-End Flow

```
PM 填 zh-TW → Phase 1: 讀 Sheet 找需翻譯（gws / cl-locales lookup）
            → Phase 2: AI 翻譯 EN/TH/JA
            → Phase 3: cl-locales add/update --batch-json（dry-run → confirm → execute）
            → Phase 4: 推 Slack review（附 PRD link）
            → Phase 5: Reviewer 回饋 → cl-locales update
            → Phase 6: cl-locales publish → staging → production
            → Phase 7: 提醒 frontend cacheLocale
```

## Example Invocation

```
/translate maac auto
/translate caac leadCapture.form.title=收集聯絡資訊 leadCapture.form.submit=送出
/translate maac auto --prd https://docs.google.com/document/d/xxx/edit
/translate maac "MAAC main content rows 3090-3100"
```
