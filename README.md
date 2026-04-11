# PM Release Pipeline

> AI Skills × Google Workspace × Slack — 自動化 PM 產品開發文件流程

從 PRD 撰寫到翻譯發布，一條指令串起整條 pipeline。

**[Documentation Site →](https://lydia-hou.github.io/pm-release-skills/)**

---

## Skills 總覽

| Skill | 功能 | 輸出位置 |
|:------|:-----|:---------|
| `/prd-draft` | 散亂資料 + Deep Research → 完整 PRD | PRD Google Doc（新建） |
| `/prd` | Scope → Feature Spec (User Stories, AC, Test Cases) | PRD Google Doc → 🤖 Spec section |
| `/test-case` | 解析 📝 test cases → 腳本 + 測試報告 | PRD Google Doc → 🤖 Test Case section |
| `/release-note` | PRD → Internal Update → 推 Slack | PRD Google Doc → 📢 Internal Update + Slack |
| `/translate` | zh-TW → EN/TH/JA + 術語表 + Slack review | Google Sheet（同 tab 多語言欄位） |

## Pipeline 流程

```
/prd-draft  ──建立 PRD──→  /prd <DOC_ID>  ──→  /test-case <DOC_ID>  ──→  /release-note <DOC_ID>  ──→  /translate
                                ↓                      ↓                         ↓                         ↓
                        🤖 Spec section         🤖 Test Case            📢 Internal Update          Google Sheet
                        (replaceAllText)        (replaceAllText)        (replaceAllText + Slack)    (spreadsheets.create)
```

所有產出都寫入**同一份 PRD Google Doc**，使用 `{{PLACEHOLDER}}` markers + Google Docs `replaceAllText` API。

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
# 互動模式：直接貼入資料
/prd-draft interactive

# 從 Google Doc 開始
/prd-draft https://docs.google.com/document/d/xxx/edit

# 從本地檔案
/prd-draft ~/Downloads/feature_brief.pdf ~/research/competitor.md

# Pipeline 串接（拿到 PRD Doc ID 後）
/prd <PRD_DOC_ID>
/test-case ~/Downloads/spec.md https://staging.example.com <PRD_DOC_ID>
/release-note ~/Downloads/prd.md <PRD_DOC_ID>
/translate ~/Downloads/release_note.md
```

## 整合工具

| 工具 | 用途 | 使用的 Skills |
|:-----|:-----|:-------------|
| **gws CLI** | Google Drive/Sheets/Docs 讀寫 | `/prd-draft`, `/translate`, 所有輸出 |
| **Slack MCP** | 讀 thread / 發訊息 / review request | `/prd-draft`, `/release-note`, `/translate` |
| **Figma MCP** | 設計稿截圖比對 | `/test-case` |
| **Asana MCP** | Bug task 建立 | `/test-case` |
| **Playwright MCP** | AI 驅動瀏覽器測試 | `/test-case` |
| **GitHub CLI** | Codebase 搜尋 | `/prd-draft` |

## Google Drive 輸出資料夾

| Product | Folder |
|:--------|:-------|
| MAAC | Shared Drive → MAAC |
| CAAC | Shared Drive → PRD |

## 檔案結構

```
.claude/commands/
├── prd-draft.md              # PRD Draft Generator
├── prd.md                    # Feature Spec Generator
├── test-case.md              # AI-Driven Test Case Executor
├── release-note.md           # Release Note Generator
├── translate.md              # Translation Flow
└── resources/
    └── prd-template.md       # PRD 範本（Full version）
```

## 參考

- [awesome-cresclab](https://github.com/chatbotgang/awesome-cresclab) — Codebase index
- [gws CLI](https://github.com/googleworkspace/cli) — Google Workspace CLI
- [HC Release Skill](https://github.com/kaddwang/Helping-Center-Release-Skill) — 設計參考

---

Built with [Claude Code](https://claude.ai/claude-code)
