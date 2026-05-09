---
name: record-test-run
description: "從 test-cases.md 建立一份新的 test run 執行紀錄供 QA 打勾（前身 test-run）。可選 --auto 用 Playwright AI 自動執行並填入結果。Triggers on: record test run, test run, 開測試, 建立測試, new test run, 開始測試, auto test, playwright run."
---

# Test Run

從 test cases 定義建立一份新的 test run 執行紀錄。預設手動模式（QA 自行打勾），加 `--auto` 用 Playwright AI-driven 自動跑完並填入結果。

## 規則

- 用繁體中文回覆
- `test-cases.md` 是測試案例的定義（source of truth），不可修改
- test run 是每次測試的執行紀錄，獨立一份檔案
- Auto 模式：staging URL 必須含 `staging` / `dev` / `test` / `demo`，否則 STOP（不打 production）
- Auto 模式：actual 完全等於 expected 才能標 PASS；flaky 重試一次再決定
- Auto 模式：失敗時繼續跑剩下的，不在第一個 fail 就停

## 概念

```
test-cases.md（定義）          test-runs/（執行紀錄）
  AI 從 PRD 產生                 每次測試複製一份
  PRD 改了就重新產生             QA 打勾、記錄結果
  ─────────────────             ─────────────────
  不打勾                         打勾
```

## When to use this vs `/verify-release`

兩者都會用 Playwright，但目的不同：

| 場景 | 用 `/record-test-run` | 用 `/verify-release` |
|---|---|---|
| 階段 | 開發中 / staging QA 迭代 | Ship gate（上線前最後一道） |
| 範圍 | 全套 P0/P1/P2 test cases | golden path 只走核心 happy path |
| 產出 | `prds/{name}/test-runs/{date}.md`（給 QA 打勾或 auto fill） | `prds/{name}/verification-{date}.md`（含截圖 + verdict） |
| 失敗時 | 繼續跑剩下的，最後標 fail count；可直接建 Asana bug | 卡住 ship、要 PM decide hold or ship-with-known-issues |
| 觸發 | `/run-release-pipeline` Phase 3 自動帶；或手動 | `/run-release-pipeline` 完成後另外觸發 |

簡單記憶：**record-test-run = 開發過程的 QA checklist；verify-release = ship 前的 final gate**。同 PRD 通常先 record-test-run（多次），最後上線前跑一次 verify-release。

## 輸入

```
/record-test-run <prd-name>                          # 手動模式（產 checklist）
/record-test-run <prd-name> --auto <staging-url>     # Playwright 自動執行
/record-test-run <prd-name> --auto <staging-url> --auth user@email:pwd
```

如果沒有指定 PRD，掃 `prds/` 找有 `test-cases.md` 的 PRD 詢問。

## Workflow

### Step 1：確認 test cases 存在

讀 `prds/{name}/test-cases.md`。

不存在 → 提醒 PM 先跑 `/gen-test-cases`。

### Step 2：建立 test run 檔案

1. 建 `prds/{name}/test-runs/`（如不存在）
2. 從 `test-cases.md` 複製內容到 `prds/{name}/test-runs/{YYYY-MM-DD}.md`
   - 同一天已有就加序號：`{YYYY-MM-DD}-2.md`
3. 頂部加 metadata：

```markdown
---
prd: "{PRD 名稱}"
date: YYYY-MM-DD
tester: "{待填}"
mode: manual  # manual | auto
status: in-progress  # in-progress | passed | failed
staging_url: "{若 auto}"
---
```

4. 所有 checkbox 重置為未勾選

### Step 3a：手動模式（預設）

告知 PM / QA：
- test run 檔案位置
- 測試時直接在檔案上打勾
- 完成後更新 frontmatter `status` 與 `tester`

跳到 Step 4。

### Step 3b：Auto 模式（`--auto`）

**前置檢查：**
- staging URL 含 `staging`/`dev`/`test`/`demo`，否則 STOP
- Playwright MCP 可用，否則降級到手動模式並提醒 PM

**執行：**

1. **登入**（若 PRD 註明需登入或 PM 提供 `--auth`）：
   - `browser_navigate` 開 staging
   - `browser_fill_form` 填帳密
   - `browser_click` 送出
   - `browser_snapshot` 確認登入成功
2. **遍歷 test cases**（依 P0 → P1 → P2）：

   對每個 test case：
   a. Setup precondition（建測試 entity、清狀態等）
   b. 依 Steps 表執行每步：
      - FE 類：`browser_click` / `browser_fill_form` / `browser_select_option`
      - BE 類：`Bash` 跑 `curl` 或 node script
      - PD 類（Figma 比對）：`browser_take_screenshot` 並用 Figma MCP `get_screenshot` 比對
   c. 檢查 expected result：`browser_snapshot` 取 DOM 或解析 API response
   d. 截圖：`browser_take_screenshot path=screenshots/{TC-ID}.png`
   e. 紀錄：PASS / FAIL / BLOCKED
   f. FAIL → 補抓 actual 行為描述 + 錯誤截圖

3. **更新 test run 檔案**：
   - 對每個 test case row 把 checkbox 標 `[x]`（PASS）/ `[ ]` + 加 `❌ FAIL`（FAIL）/ `⚠️ BLOCKED`
   - 新增「Execution Results」section：

   ```markdown
   ## Execution Results

   | TC ID | Status | Actual | Screenshot |
   |-------|--------|--------|------------|
   | TC-001 | ✅ PASS | (matches) | screenshots/TC-001.png |
   | TC-002 | ❌ FAIL | Modal didn't open | screenshots/TC-002.png |
   ```

   - 更新 frontmatter `status`：全 PASS → `passed`；有 FAIL → `failed`
4. **截圖目錄：** `prds/{name}/test-runs/screenshots/{date}/`

### Step 4：摘要回報

```
✅ Test Run 建立
- 檔案: prds/{name}/test-runs/{date}.md
- 模式: [manual / auto]
- 結果（auto only）: Pass X / Fail Y / Blocked Z

[手動] 提醒 QA 在檔案上打勾
[auto + 有 FAIL] 失敗的 case 是否要建 Asana bug task？
```

### Step 5：（可選）建 Asana bug task

若 auto 模式有 FAIL 且 PM 同意：

對每個 FAIL 的 P0/P1 case，用 Asana MCP `create_task_preview` → `create_task_confirm`：
- Title: `[Bug] {TC-ID}: {Test Name}`
- Description: actual vs expected + 截圖路徑 + 重現步驟
- Priority: P0 → High / P1 → Medium / P2 → Low
- Assignee: 問 PM

### Step 6：（測試完成後）回流到 PRD

PM 回報結果或 auto 模式跑完後：
- 更新 test run frontmatter `status`、`tester`
- 失敗的 case → 問 PM 是否加到 PRD 的 Open Questions
- 影響 scope 的 bug → 問 PM 是否更新 PRD 的 Spec Delta

## Example Invocation

```bash
# 手動模式
/record-test-run journey-contact-trigger

# Playwright auto 模式
/record-test-run journey-contact-trigger --auto https://staging.maac.io

# 帶登入
/record-test-run custom-field-tagging --auto https://staging.maac.io --auth user@test.com:pwd
```
