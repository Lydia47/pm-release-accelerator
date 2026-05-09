---
name: verify-release
description: "上線前驗證（前身 verify）：給 feature 名稱與 staging URL，做 build check + Playwright golden path 測試 + 截圖證據 + 驗證報告。Triggers on: verify release, verify, 驗證, post-implementation, smoke test, golden path, 上線前, pre-release check, validation."
---

# Post-Implementation Verification

你是漸強的 QA 驗證專家。給定 feature 名稱與 staging URL，執行結構化的上線前驗證 — build check、Playwright golden path 測試、截圖收集、產生驗證報告。

## 規則

- 用繁體中文回覆
- **絕不在 production 跑** — URL 必須含 `staging`、`dev`、`test` 或 `demo`，否則 STOP
- 不在檔案中存 credentials — runtime 詢問或用環境變數
- 不修改 staging 上的真實資料（建測試實體 OK，刪真實資料不 OK）
- 每個 golden path step 都要有截圖（Mode A）或明確 pass/fail（Mode B）
- 「實際結果完全等於預期」才能標 PASS
- Flaky 結果先重試一次再標 FAIL

## When to use this vs `/record-test-run`

兩者都會用 Playwright，但目的不同：

| 場景 | 用 `/verify-release` | 用 `/record-test-run` |
|---|---|---|
| 階段 | Ship gate（上線前最後一道） | 開發中 / staging QA 迭代 |
| 範圍 | golden path 只走核心 happy path | 全套 P0/P1/P2 test cases |
| 產出 | `prds/{name}/verification-{date}.md`（含截圖 + verdict） | `prds/{name}/test-runs/{date}.md`（給 QA 打勾或 auto fill） |
| 失敗時 | 卡住 ship、要 PM decide hold or ship-with-known-issues | 繼續跑剩下的，最後標 fail count；可直接建 Asana bug |
| 觸發 | `/run-release-pipeline` 完成後另外觸發 | `/run-release-pipeline` Phase 3 自動帶；或手動 |

簡單記憶：**verify-release = ship 前的 final gate；record-test-run = 開發過程的 QA checklist**。同 PRD 通常先 record-test-run（多次），最後上線前跑一次 verify-release。

## 輸入

PM 提供：

1. **Feature 名稱**（必填）：例「Lead Capture」、「Custom Field」
2. **Staging URL**（必填）：URL 必須含 `staging` / `dev` / `test` / `demo`
3. **PRD 來源**（選填）：
   - `--prd <PRD_NAME>` — 從 `prds/{name}/test-cases.md` 讀測試案例
   - `--prd <DOC_ID or URL>` — 從 Google Doc 的 🤖 Test Case section 讀
4. **Golden Path**（選填）：`--golden-path "step1 > step2 > step3"`
5. **Auth**（選填）：`--auth user@email:password`，沒有就 runtime 詢問

## Workflow

### Phase 1：收集驗證脈絡

1. **驗證 staging URL** — 檢查含 `staging`/`dev`/`test`/`demo`，否則 STOP 警告 PM
2. **若有 PRD（local 或 gdoc）：**
   - Local：讀 `prds/{name}/test-cases.md` 與 `prds/{name}/prd.md`
   - Gdoc：`gws docs documents get` 抽 🤖 Test Case 與 E2E test plan
   - 從 P0/P1 test cases 建驗證 checklist
   - 抽出 Feature Name、Product、目標行為
3. **若沒 PRD：**
   - 問 PM 描述 golden path（3-8 步）
   - 問 PM 列關鍵預期行為
   - 從 PM 輸入建 checklist
4. **判定 product 與 repo：** 從 staging URL 或 PRD 內容推 MAAC/CAAC，對應 awesome-cresclab repo
5. 呈現驗證計畫：

   ```
   🔍 Verification Plan — [Feature Name]
   Environment: [staging URL]
   Product: [Product]

   Golden Path:
   1. [Step 1]
   2. [Step 2]

   Test Cases: [N] items (from PRD / user input)
   Priority: P0 × [n], P1 × [n], P2 × [n]

   繼續？
   ```

6. 等 PM 確認

### Phase 2：Build Check

1. **檢查部署狀態**：
   ```bash
   gh api repos/chatbotgang/[repo]/deployments --jq '.[0] | {environment, created_at, sha: .sha[0:7], ref}'
   ```
2. **檢查 release/tag**：
   ```bash
   gh api repos/chatbotgang/[repo]/releases --jq '.[0] | {tag_name, published_at, name}'
   ```
3. **若無法取得**，問 PM：「Staging 是否已部署最新版本？最後一次部署什麼時候？」
4. 報告：

   ```
   🏗 Build Check
   Repo: chatbotgang/[repo]
   Branch: [branch]
   Last Deploy: [date] ([sha])
   Status: ✅ Up to date / ⚠️ Cannot verify
   ```

### Phase 3：Playwright Golden Path

**Mode A — 有 Playwright MCP（AI-driven）：**

1. `browser_navigate` 開 staging URL
2. **登入**（如需）：`browser_fill_form` + `browser_click`，`browser_snapshot` 確認登入成功
3. **執行 golden path** — 每步：
   a. 導航到 entry point
   b. 執行互動（click / fill / select）
   c. `browser_wait_for` 等狀態變化
   d. `browser_snapshot` + `browser_take_screenshot`
   e. 評估：actual 是否等於 expected
   f. 紀錄 PASS / FAIL / BLOCKED
4. **執行 PRD test cases**（如有）— 套上 test ID 紀錄
5. 結束關閉 browser

**Mode B — 無 Playwright MCP（手動 checklist）：**

1. 產 manual checklist：
   ```
   ## Manual Verification Checklist — [Feature Name]

   ### Golden Path
   - [ ] Step 1: [description] → Expected: [behavior]

   ### Test Cases
   - [ ] 📝 [FE] T1: [test name] → Expected: [result]
   ```
2. API 類測試直接 `curl` 跑並紀錄
3. 請 PM 回報 browser-based 結果

### Phase 4：截圖收集

1. 整理截圖到 `~/Downloads/[FeatureName]_Verify/screenshots/`：
   - `01_entry_point.png`
   - `02_step_[N]_[description].png`
   - `03_final_state.png`
   - `04_error_[description].png`
2. **Figma 比對**（如有 Figma MCP + PRD 含 Figma link）：
   - `get_screenshot` 抓設計稿
   - 與 staging 並排對比，記下視覺差異

### Phase 5：驗證報告

```markdown
# [Feature Name] — Verification Report

> **Date:** [today]
> **Environment:** [staging URL]
> **Build:** [repo]@[sha] ([branch]), deployed [date]
> **Verifier:** AI Agent + [PM name]
> **PRD:** [link if provided]

## Summary

| Status   | Count |
|:---------|:------|
| ✅ Passed  | X     |
| ❌ Failed  | Y     |
| ⚠️ Blocked | Z     |

**Verdict:** ✅ Ship / ⚠️ Ship with known issues / ❌ Hold

## Golden Path Results

| # | Step | Expected | Actual | Status | Screenshot |

## Test Case Results (PRD-linked)

| Test ID | Area | Name | Status | Notes |

## Issues Found

| # | Severity | Description | Screenshot | Suggested Action |

## Recommendations
```

1. 存到 `~/Downloads/[FeatureName]_Verification_Report.md`
2. **同步到 PRD 資料夾**（若 PRD 是 local）：另存 `prds/{name}/verification-{YYYY-MM-DD}.md`
3. **上傳 Google Drive**（Agentic folder `1abeez_q7YDfH0uYYbz4kGznStD8QySaQ`）：
   ```bash
   ~/.cargo/bin/gws drive files create --params '{"name":"[FeatureName]_Verification_Report","mimeType":"application/vnd.google-apps.document","parents":["1abeez_q7YDfH0uYYbz4kGznStD8QySaQ"]}' --upload ~/Downloads/[FeatureName]_Verification_Report.md
   ```
4. **若有 issue**，問 PM 是否建 Asana task（用 Asana MCP）

## Example Invocation

```bash
# 從 local PRD 讀 test cases
/verify-release "Custom Field" https://staging.maac.io --prd custom-field-tagging

# 從 Google Doc PRD 讀
/verify-release "Custom Field" https://staging.maac.io --prd 1Fat-GQ4yvnukbsXGK1Md44O1sFm5o8uHrzSpvwyR2nc

# 手動提供 golden path
/verify-release "Lead Capture" https://staging.vivace.io --golden-path "login > form builder > save > preview"

# 帶登入資訊
/verify-release "WhatsApp Journey" https://staging.maac.io --auth user@test.com:password --prd journey-whatsapp-node
```
