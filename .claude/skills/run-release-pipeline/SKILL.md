---
name: run-release-pipeline
description: "Release Pipeline orchestrator（前身 release-pipeline）：給 PRD（local prds/{name} 或 Google Doc ID），依序串接 gen-test-cases → record-test-run → gen-release-notes → translate-locales，可選 sync-gdoc 同步。每步都有 user confirmation gate。Triggers on: run release pipeline, release pipeline, pipeline, 串接, 一鍵發布, end-to-end release."
---

# Release Pipeline Orchestrator

你是漸強的 PM workflow 編排專家。給定一份 PRD（local 或 Google Doc），依序串接下游 skills — `gen-test-cases` → `record-test-run` → `gen-release-notes` → `translate-locales` — 每步之間都有 PM 確認 gate。

## 規則

- **每步都要 PM confirmation** — 絕不自動進入下一步
- 某步失敗時問 PM：retry / skip / abort
- PRD 內容只讀一次，後續 phase 重複使用
- 所有 downstream skill 的安全規則仍適用（Slack 發送前確認、production publish 需明確授權）
- 用繁體中文回覆

## 輸入

PM 提供：

1. **PRD 來源**（必填，二擇一）：
   - **Local**：`<PRD_NAME>`（對應 `prds/{name}/` 資料夾）
   - **Google Doc**：完整 URL 或 Doc ID
2. **Staging URL**（選填）：`test-run --auto` 用，沒給就在 Phase 3 詢問
3. **Product**（選填）：`maac` / `caac` / `admin-center` / `liff`，`translate-locales` 用
4. **`--skip`**（選填）：逗號分隔，可選 `gen-test-cases`, `record-test-run`, `gen-release-notes`, `translate-locales`
5. **`--auto-test`**（選填）：test-run 用 Playwright 自動執行（需 staging URL）

## Workflow

### Phase 1：Validate PRD & Plan Pipeline

1. **解析 PRD 來源**：
   - 若是 PRD name → 讀 `prds/{name}/prd.md`，檢查是否存在 + 取得 frontmatter
   - 若是 Doc ID/URL → `gws docs documents get --params '{"documentId":"<DOC_ID>","includeTabsContent":true}'`
2. **抽 metadata**：
   - Feature Name — PRD title 或 frontmatter
   - PM Owner、Product、Domain、Target Release Date
   - 若 PRD frontmatter 有 `gdoc_id`，後面用得到
3. **檢查既有產物**：列出 `prds/{name}/` 下已存在的檔案（test-cases.md / release-notes.md / hc-content.md / verification-*.md），決定哪些 phase 要跑、哪些要 skip 或覆蓋
4. **呈現 pipeline 計畫**：

   ```
   📋 Release Pipeline for: [Feature Name]
   PRD: [path or URL]
   Domain: [domain] | Product: [product]

   Step 1: gen-test-cases   — 從 PRD 產生測試案例定義
   Step 2: test-run         — 建測試執行紀錄（[--auto: Playwright 自動跑 / 手動 checklist]）
   Step 3: gen-release-notes — 產 Release Notes（External + Internal 版本）
   Step 4: translate-locales       — UI 翻譯 EN/TH/JA → Sheet → Slack review
   Step 5: sync-gdoc        — [若有 gdoc_id] 同步所有 .md 到 Google Doc

   Skipped: [none / list]

   繼續？
   ```

5. 等 PM 確認

### Phase 2：Gen Test Cases

**Skip：** 若 `gen-test-cases` 在 `--skip`，標 SKIPPED 進 Phase 3

1. 確認：「準備從 PRD 產生 test cases。會覆蓋既有 `prds/{name}/test-cases.md`。繼續？」
2. **委派給 `gen-test-cases` skill**：
   - 讀 `prds/{name}/prd.md` + `specs/{domain}/spec.md`
   - 依 P0/P1/P2 規則 + Happy/Edge/Error/Regression 四類產出
   - TBD 項標 BLOCKED
   - 寫到 `prds/{name}/test-cases.md`
3. 結果摘要：

   ```
   ✅ Test Cases 產出
   - P0: X 項 / P1: Y 項 / P2: Z 項
   - Blocked: N 項（TBD）
   檔案: prds/[name]/test-cases.md

   繼續到 test-run？
   ```

### Phase 3：Test Run

> **Note：** 這個 phase 跑的是 `record-test-run`（開發階段全套 P0/P1/P2 testing）。
> Ship 前最後驗證請另外觸發 `/verify-release`（golden path smoke test），不在 pipeline 內。
> 詳見兩個 SKILL.md 的「When to use this vs the other」段落。

**Skip：** 若 `record-test-run` 在 `--skip`，標 SKIPPED 進 Phase 4

1. 確認：「準備建立 test run 執行紀錄。」
2. **判定模式：**
   - 若有 `--auto-test` + staging URL → Playwright AI-driven 模式
   - 否則 → 手動 checklist 模式（QA 人工打勾）
3. **委派給 `record-test-run` skill**：
   - 從 `test-cases.md` 複製到 `prds/{name}/test-runs/{YYYY-MM-DD}.md`
   - Auto 模式：跑 Playwright 後填入結果（pass/fail/blocked + screenshot 路徑）
   - 手動模式：交給 QA 自行打勾
4. 結果摘要：

   ```
   ✅ Test Run 建立
   - 檔案: prds/[name]/test-runs/[date].md
   - 模式: [auto-execute / manual checklist]
   - 結果: Pass X / Fail Y / Blocked Z（auto only）

   繼續到 release notes？
   ```

5. 若 auto 模式有失敗，問 PM：「有 Y 個測試失敗，要先處理還是繼續？」

### Phase 4：Gen Release Notes

**Skip：** 若 `gen-release-notes` 在 `--skip`，標 SKIPPED 進 Phase 5

1. 確認：「準備產 Release Notes（External + Internal 兩個版本）。」
2. **委派給 `gen-release-notes` skill**：
   - 讀 `prds/{name}/prd.md` 重點（Background、User Stories、Proposed Solution、Success Metrics）
   - 套 `templates/release-notes-template.md`
   - 產出寫到 `prds/{name}/release-notes.md`
3. **可選：推 Slack**（Internal Update）— 問 PM 要不要、推哪個 channel
   - mrkdwn 格式轉換、~4000 char 切 main + thread replies
   - 推送前 PM 必須確認最終內容與 channel
4. 結果摘要：

   ```
   ✅ Release Notes 產出
   - 檔案: prds/[name]/release-notes.md
   - Slack: [#channel + N thread replies / skipped]

   繼續到翻譯？
   ```

### Phase 5：Translate

**Skip：** 若 `translate-locales` 在 `--skip`，標 SKIPPED 進 Phase 6

1. 確認：「準備開始翻譯流程（需要 product 與翻譯範圍）。」
2. 收集：
   - **Product**：用 Phase 1 抽到的，或問 PM
   - **翻譯範圍**：問 PM — `auto`（自動掃 sheet 找未翻譯）或 specific keys
3. **委派給 `translate-locales` skill**：
   - 讀 UI Translation Sheet
   - 翻 EN（SaaS 專業）/ TH（ภาษาทางการ）/ JA（敬語）
   - 寫回同一份 sheet
   - 推 TH/JA Slack review，附 PRD link
   - **不自動 publish production**，等 PM 明確授權後才 `cl-locales publish --env production`
4. 結果摘要：

   ```
   ✅ Translation 完成
   - Sheet: [N] rows updated
   - Slack Review: TH → #channel | JA → #channel
   - Production publish: 待 reviewer 確認後手動觸發

   繼續到 doc 同步？
   ```

### Phase 6：Sync to Outline / Google Doc（可選）

**只有 PRD 是 local + frontmatter 有 `outline_doc_id` 或 `gdoc_id`，或 PM 要求時才跑。**

預設路徑：

- **Primary：** 若 frontmatter 有 `outline_doc_id` 或 PM 想內部分享 → 委派 `sync-outline`（Outline 為內部 SSOT primary）
- **Alternative：** 若 frontmatter 有 `gdoc_id` 或 PM 要對外分享給沒 Outline 帳號的 stakeholder → 委派 `sync-gdoc`
- 兩者皆需要：先 sync-outline（內部）再 sync-gdoc（對外），分別記在 frontmatter

1. 確認：「準備把 prds/[name]/ 所有 .md 同步到 [Outline / Google Doc / 兩者]。」
2. **委派給 `sync-outline` 或 `sync-gdoc` skill**：
   - 動態掃描資料夾找出存在的 .md
   - 每個檔案對應一個 child doc（Outline）或分頁（GDoc）
   - 已有 doc → 更新；沒有 → 新建並把 ID 寫回 frontmatter
3. 結果：「Outline / Google Doc 已同步：[URL]，N 個 child / 分頁」

### Phase 7：Pipeline Summary

```
═══════════════════════════════════════════
📋 Release Pipeline Summary — [Feature Name]
═══════════════════════════════════════════

PRD: [prds/[name]/ or gdoc URL]
PM: [Owner] | Product: [Product] | Target: [Date]

┌──────────────────┬──────────┬────────────────────────────┐
│ Step              │ Status   │ Output                     │
├──────────────────┼──────────┼────────────────────────────┤
│ gen-test-cases    │ ✅ DONE  │ X cases (P0/P1/P2)         │
│ test-run          │ ✅ DONE  │ Pass X / Fail Y / Block Z  │
│ gen-release-notes │ ✅ DONE  │ Slack #channel + .md       │
│ translate-locales     │ ⏭ SKIP  │ —                          │
│ sync-gdoc         │ ✅ DONE  │ [Google Doc URL]           │
└──────────────────┴──────────┴────────────────────────────┘

📁 Files:
  - prds/[name]/test-cases.md
  - prds/[name]/test-runs/[date].md
  - prds/[name]/release-notes.md

🔗 Links:
  - PRD: prds/[name]/prd.md（gdoc: [URL]）
  - Slack Post: [URL]
  - Translation Sheet: [URL]

Suggested Follow-up:
  - /verify-release "[FeatureName]" [staging_url] — 上線前驗證
  - /archive-prd [name] — 開發完畢後歸檔，更新 Product Spec
  - `cl-locales publish` — reviewer 確認後發翻譯到 Firebase Storage
```

## Error Handling

- PRD 找不到 / Doc ID 無效 → 停 pipeline 報錯
- gws CLI 認證過期 → 提示 `gws auth login`
- Slack MCP 連線失敗 → 跳過 Slack 步驟但繼續其他工作
- Playwright MCP 不可用 → test-run 自動降級到手動模式

## Example Invocation

```bash
# 完整 pipeline，從 local PRD
/run-release-pipeline custom-field-tagging

# 從 Google Doc
/run-release-pipeline 1Fat-GQ4yvnukbsXGK1Md44O1sFm5o8uHrzSpvwyR2nc

# 指定 staging + product + 自動測試
/run-release-pipeline custom-field-tagging --staging https://staging.maac.io --product maac --auto-test

# 跳過翻譯
/run-release-pipeline custom-field-tagging --skip translate-locales

# 只跑 release-notes + translate-locales（跳過測試）
/run-release-pipeline custom-field-tagging --skip gen-test-cases,record-test-run
```
