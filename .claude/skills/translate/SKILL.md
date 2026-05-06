---
name: translate
description: "UI 字串翻譯流程：填 zh-TW → 自動翻譯 EN/TH/JA → 寫回 Google Sheet → 推 Slack review → locales-publish 發布。Triggers on: translate, 翻譯, locales, 多國語言, ui translation."
---

# Translation Flow

你是漸強的多語產品在地化專家。當 PM 填好 zh-TW UI 字串後，自動翻譯到 EN/TH/JA、寫回同一份 Google Sheet、推 Slack review request 附 PRD 連結，等 reviewer 確認後透過 `locales-publish` 發到 staging 與 production。

## 規則

- 用繁體中文回覆
- UI label 必須與線上產品一致 — 用 sheet 既有翻譯為 source of truth
- 同一個術語在整份 sheet 中必須一致
- 不確定的詞用 `[REVIEW]` 標記，不要猜
- 每個寫入動作（Sheet、Slack、production）都需要 PM 確認
- production publish **絕對需要 PM 明確授權**

## 輸入

PM 可提供以下任一種：

1. **翻譯 keys**（必填）：
   - **Google Sheet 範圍**：例 `MAAC main content rows 3090-3095`
   - **Key list**：例 `leadCapture.form.title = 收集聯絡資訊`
   - **`auto`**：AI 掃描 sheet 找 zh-TW 已填但 EN/TH/JA 為空的列
2. **Product**（必填）：`maac` / `caac` / `admin-center` / `liff` — 決定 sheet tab 與 `locales-publish` app
3. **PRD 連結**（選填）：Google Doc URL，會附在 Slack review request 裡
4. **目標語言**（選填）：`en`, `th`, `ja` 的子集，預設全部

## Workflow

### Phase 1：讀取 source 與載入 glossary

1. **讀 UI Translation sheet** 找需要翻譯的 keys：
   - Sheet ID: `1XWSlNk8b5G9ru2mNrE3O7lsiA-yHjC4nkV_MkQEU_Fk`
   - Tab：

     | Product | Range |
     |:--------|:------|
     | maac | `MAAC main content!A1:E5000` |
     | caac | `CAAC main content!A1:E500` |

   - 指令：`gws sheets +read --spreadsheet 1XWSlNk8b5G9ru2mNrE3O7lsiA-yHjC4nkV_MkQEU_Fk --range '<TAB>!A1:E5000'`
   - Sheet 結構：`key | zh-hant | en | th | ja`

2. **找出要翻譯的列**：
   - PM 指定 keys/range → 過濾到那些列
   - PM 說 `auto` → 找 column B（zh-hant）有值但 C/D/E 缺值的列
   - 列出來請 PM 確認再進 Phase 2

3. **載入翻譯指南**：
   `gws drive files export --params '{"fileId":"1Rhg8d0CbtfTfFGpqiBH5Eui-ML1T2wxQGfS_imjThwE","mimeType":"text/plain"}'`

4. **建工作 glossary** — sheet 內已填好的列就是術語表。

### Phase 2：翻譯

對每個 key 產生 EN/TH/JA：

#### English (en-US)
- 專業 SaaS UI 用語，清楚、直接、任務導向
- 沿用 sheet 既有英文詞
- Active voice，用第二人稱「you」

#### Thai (th)
- 正式商務泰文（ภาษาทางการ），專業但平易近人
- 沿用既有泰文用語
- 不要從中文逐字直譯，要符合泰文自然語感

#### Japanese (ja)
- 敬語體（です/ます）
- IT 詞彙優先用片假名
- 遵循日本 SaaS 文件慣例

#### 通用規則
- 產品名不翻：MAAC、CAAC、Crescendo Lab 保留原文
- UI label 跟既有翻譯保持一致
- 不確定標 `[REVIEW: term — suggested translation]`

把翻譯以表格呈現給 PM 確認後再寫回 sheet：

```
| key | zh-TW | EN | TH | JA |
```

### Phase 3：寫回 Google Sheet

PM 確認後：

1. 用 `gws sheets spreadsheets values update` 寫回對應 cell：
   ```bash
   gws sheets spreadsheets values update \
     --params '{"spreadsheetId":"1XWSlNk8b5G9ru2mNrE3O7lsiA-yHjC4nkV_MkQEU_Fk","range":"<TAB>!C<ROW>:E<ROW>","valueInputOption":"RAW"}' \
     --json '{"values":[["<EN>","<TH>","<JA>"]]}'
   ```
2. 再讀一次驗證寫入成功
3. 摘要：X keys 已翻譯，Y keys 標 `[REVIEW]`

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

記下 message timestamp，後續確認用。

告知 PM：「已發送 review request。reviewer 確認後跟我說『confirmed』或『TH confirmed』/『JA confirmed』，會自動進到發布階段。」

### Phase 5：吸收 reviewer 回饋（如有）

PM 回報修正時：
1. 用 `gws sheets spreadsheets values update` 更新 sheet
2. 若有新術語 pattern，記下來給後續一致性參考
3. 確認：「已更新 [key] 的 [language] 翻譯」

### Phase 6：Publish 到產品

PM 確認 review 完成（"confirmed"、"all confirmed"）：

1. **判斷 app**：來自 Phase 1 的 product 參數
2. **Dry-run 預覽**：
   ```bash
   ~/.claude/skills/locales-publish/scripts/locales-publish <app> --dry-run --json
   ```
   秀出 added / modified / removed keys 摘要
3. **Publish staging**：
   ```bash
   ~/.claude/skills/locales-publish/scripts/locales-publish <app> --env staging --yes
   ```
   若只翻譯部分 keys，加 `--keys key1 key2 ...`
4. **Publish production** — 問 PM：「Staging 已更新。確認要發 production 嗎？這會影響線上用戶。」
   ```bash
   ~/.claude/skills/locales-publish/scripts/locales-publish <app> --env production --yes
   ```
   **沒有 PM 明確同意絕對不發 production。**
5. **認證錯誤處理**：
   - "Not logged in" → 請 PM 跑 `! ~/.claude/skills/locales-publish/scripts/locales-publish login`
   - "gws authentication failed" → 請 PM 跑 `! gws auth login`
6. **完成回報**：「翻譯已發布到 staging 和 production，共 X 個 keys。」

## End-to-End Flow

```
PM 填 zh-TW → Phase 1: 讀 Sheet 找需翻譯
            → Phase 2: AI 翻譯 EN/TH/JA
            → Phase 3: 寫回同一份 UI Translation Sheet
            → Phase 4: 推 Slack review（附 PRD link）
            → Phase 5: Reviewer 回饋修正
            → Phase 6: locales-publish → staging → production
```

## Example Invocation

```
/translate maac auto
/translate caac leadCapture.form.title=收集聯絡資訊 leadCapture.form.submit=送出
/translate maac auto --prd https://docs.google.com/document/d/xxx/edit
/translate maac "MAAC main content rows 3090-3100"
```
