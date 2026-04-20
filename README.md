# PM Release Accelerator

> AI Skills × Google Workspace × Slack — 自動化 PM 產品開發文件流程

從 User Scenario 到翻譯發布，一條指令完成所有文件。

**[Documentation Site →](https://lydia47.github.io/pm-release-accelerator/)**

---

## Skills 總覽

| Skill | 功能 | 輸出位置 |
|:------|:-----|:---------|
| `/prd` | User Scenario → Deep Research → PRD + Feature Spec + Test Cases | PRD Google Doc（新建，一條龍產出） |
| `/test-case` | 解析 📝 test cases → Playwright 腳本 + 測試報告 | PRD Google Doc → 🤖 Test Case section |
| `/release-note` | PRD → Internal Update → 推 Slack | PRD Google Doc → 📢 Internal Update + Slack |
| `/translate` | zh-TW → EN/TH/JA + 術語表 + Slack review + 自動發布 | Google Sheet + locales-publish → staging/production |
| `/release-pipeline` | PRD Doc ID → 一鍵串接 /test-case → /release-note → /translate | PRD Google Doc（回寫所有 section）+ Slack |
| `/verify` | Feature + Staging URL → Build check + Playwright 驗證 + 截圖報告 | Verification Report（Google Drive + 本地） |
| `/ga-tracking` | GA4 Measurement ID → React SPA 埋碼（gtag.js + analytics module + router + events） | index.html, src/lib/analytics.js, App.jsx, handlers |

## 整體流程

```
/prd  ──建立完整 PRD──→  /release-pipeline <DOC_ID>  ─┬─→  /test-case    → 測試報告回寫 PRD
         ↓                                             ├─→  /release-note → Internal Update + Slack
  📝 PRD + 🤖 Spec                                    └─→  /translate    → Google Sheet + publish
  + 🤖 Test Cases
                          /verify <feature> <staging_url>  ──→  Build check + Playwright + 截圖報告
```

> 💡 `/release-pipeline` 是 orchestrator — 串接下游 3 個 skill，每步都有 user confirmation gate。
> `/verify` 是獨立的上線前驗證工具，可搭配 `/release-pipeline` 或單獨使用。

所有產出都寫入**同一份 PRD Google Doc**（Agentic Drive folder），使用 `{{PLACEHOLDER}}` markers + Google Docs `replaceAllText` API。

## 安裝

### 1. 安裝 gws CLI

```bash
npm install -g @googleworkspace/cli
```

### 2. 認證 Google Workspace

```bash
gws auth setup        # 一次性設定 GCP project
gws auth login -s drive,sheets,docs,gmail,calendar
```

### 3. 複製 Skills

```bash
# 複製所有 skill 檔案到 Claude Code commands 目錄
cp -r .claude/commands/* ~/.claude/commands/
```

### 4. 開始使用

```bash
# 互動模式：輸入 user scenario 即可
/prd interactive

# 從 Google Doc 開始
/prd https://docs.google.com/document/d/xxx/edit

# 從本地檔案
/prd ~/Downloads/feature_brief.pdf ~/research/competitor.md

# Lite PRD（小功能/優化）
/prd ~/Downloads/scope.md --lite

# 下游串接（拿到 PRD Doc ID 後）
/test-case ~/Downloads/spec.md https://staging.example.com <PRD_DOC_ID>
/release-note ~/Downloads/prd.md <PRD_DOC_ID>
/translate ~/Downloads/release_note.md

# 一鍵串接所有下游流程（推薦）
/release-pipeline <PRD_DOC_ID>
/release-pipeline <PRD_DOC_ID> --staging https://staging.maac.io --product maac
/release-pipeline <PRD_DOC_ID> --skip translate

# 上線前驗證
/verify "Lead Capture" https://staging.vivace.io
/verify "Custom Field" https://staging.maac.io --prd <PRD_DOC_ID>

# GA4 埋碼（給一個 Measurement ID 就開工）
/ga-tracking G-HZRJ3ZNSB9
/ga-tracking help   # 只印 GA4 Measurement ID 建立流程
```

## `/prd` 做了什麼？

一個指令，6 個 Phase：

| Phase | 做什麼 | 整合工具 |
|:------|:-------|:---------|
| 1. Collect | 解析所有輸入（Google Doc/Sheets/PDF/Slack/inline） | gws CLI, Slack MCP |
| 2. Research | Codebase 探索 + Reqflow 查詢 + 競品研究 | GitHub CLI, gws CLI, WebSearch |
| 3. Strategy | PRD 上半部：Goal → Scope → TA → Selling Points → Glossary | — |
| 4. Feature Spec | 下半部：User Stories & AC → User Flow → Business Logic → Test Cases → NFR | — |
| 5. Q&A | 互動解決所有 TBD 和模糊點 | Agent, WebSearch |
| 6. Output | 寫入 Google Drive + 回傳 Doc ID | gws CLI |

## 整合工具

| 工具 | 用途 | 使用的 Skills |
|:-----|:-----|:-------------|
| **gws CLI** | Google Drive/Sheets/Docs 讀寫 | `/prd`, `/translate`, 所有輸出 |
| **Slack MCP** | 讀 thread / 發訊息 / review request | `/prd`, `/release-note`, `/translate` |
| **Figma MCP** | 設計稿截圖比對 | `/test-case` |
| **Asana MCP** | Bug task 建立 | `/test-case` |
| **Playwright MCP** | AI 驅動瀏覽器測試 | `/test-case`, `/verify` |
| **GitHub CLI** | Codebase 搜尋 | `/prd`, `/verify` |
| **locales-publish** | 翻譯發布到 Firebase (staging/production) | `/translate` |

## Google Drive 輸出

| 資料夾 | 用途 |
|:-------|:-----|
| **Agentic** (default) | 所有新建的 PRD、翻譯 Sheet |
| MAAC | 可選額外加入 |
| CAAC | 可選額外加入 |

## 檔案結構

```
.claude/commands/
├── prd.md                    # PRD Generator (策略 + Feature Spec 一條龍)
├── test-case.md              # AI-Driven Test Case Executor
├── release-note.md           # Release Note Generator + Slack
├── translate.md              # Translation Flow + locales-publish
├── release-pipeline.md       # Release Pipeline Orchestrator (串接上述 4 個 skill)
├── verify.md                 # Post-Implementation Verification
├── ga-tracking.md            # GA4 Embedder (Measurement ID → 埋碼完整流程)
└── resources/
    └── prd-template.md       # PRD 範本（Full version）
```

## 參考

- [awesome-cresclab](https://github.com/chatbotgang/awesome-cresclab) — Codebase index
- [gws CLI](https://github.com/googleworkspace/cli) — Google Workspace CLI
- [locales-management](https://github.com/chatbotgang/locales-management) — locales-publish CLI
- [HC Release Skill](https://github.com/kaddwang/Helping-Center-Release-Skill) — 設計參考

---

Built with [Claude Code](https://claude.ai/claude-code)
