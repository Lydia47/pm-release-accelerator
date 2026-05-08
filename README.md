# PM Release Accelerator

> Git-as-SSOT × AI Skills × Google Workspace × Slack — 從探索到上線、從寫 PRD 到發翻譯，一條龍 PM 工作流。

整合 **pm-hub 的規格閉環架構** 與 **release-side 自動化** 的混合式 PM 工作流：PRD 與 Spec 住在 Git repo，Google Doc 是 read-only snapshot，下游發布鏈（test → release notes → translate → verify）全部 AI 自動化。

**[Documentation Site →](https://lydia47.github.io/pm-release-accelerator/)**

---

## 三層架構

```
┌─────────────────────────────────────────────────────────────┐
│ 1. 探索 / 評估                                                │
│    /product-thinking   ICE × 風險 × 指標 × 假設句型           │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. PRD Lifecycle（Git-as-SSOT）                              │
│    /new-prd        建立 prds/{name}/ + evaluation.md         │
│    /sync-prd       會議結論 / Slack 討論回流到 PRD            │
│    /review-prd     PM/Eng/QA/PD 四角色平行 review            │
│    /sync-gdoc      推到 Google Doc 給 stakeholder            │
│    /pull-gdoc-comments   把 Doc 評論整理回 PRD                │
│    /archive-prd    更新 specs/ + 搬到 archive                │
│    /gen-product-spec     從 source code 反向產 SSOT spec      │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. 上線發布鏈                                                 │
│    /gen-test-cases     從 PRD 產測試定義（覆蓋）             │
│    /test-run           QA 執行紀錄（手動 or --auto Playwright）│
│    /gen-release-notes  External + Internal + 推 Slack        │
│    /gen-hc-content     Help Center 素材                      │
│    /translate          UI 翻譯 → Sheet → Slack review → publish│
│    /verify             上線前 build check + Playwright       │
│    /release-pipeline   一鍵串接：test → release-note → translate│
│    /ga-tracking        GA4 SPA 埋碼（gtag + analytics module）│
└─────────────────────────────────────────────────────────────┘
```

## Skills 全覽（16 支）

### 探索 / 評估

| Skill | 功能 | 輸出 |
|:------|:-----|:-----|
| `/product-thinking` | ICE 評分 / 四大風險掃描 / 成功指標 / 假設句型 | 評估報告（→ `/new-prd` 整理進 `evaluation.md`） |

### PRD Lifecycle

| Skill | 功能 | 輸出 |
|:------|:-----|:-----|
| `/new-prd` | 整理對話結論 + 讀現有 spec → 建 PRD draft | `prds/{name}/prd.md` + `evaluation.md` |
| `/sync-prd` | 把會議 / Slack 決策同步進 PRD（含人工確認 gate） | 修改 `prds/{name}/prd.md` |
| `/review-prd` | PM/Eng/QA/PD **四 subagent 平行** review，含跨 PRD 衝突偵測 | `prds/{name}/review.md` |
| `/sync-gdoc` | PRD 資料夾 → Google Doc，每個 .md 一個分頁 | Google Doc URL（寫回 `gdoc_id` frontmatter） |
| `/pull-gdoc-comments` | Google Doc 評論 → 結構化摘要 → 回流到 PRD | 修改 `prd.md`、可選 mark resolved |
| `/archive-prd` | Spec Delta 更新 `specs/` + 搬 PRD 到 archive | `specs/{domain}/spec.md` 更新 + `prds/archive/{date}-{name}/` |
| `/gen-product-spec` | 平行 subagent 讀 source code → 反向產出 Product Spec | `specs/{domain}/spec.md` + capability files |

### 上線發布鏈

| Skill | 功能 | 輸出 |
|:------|:-----|:-----|
| `/gen-test-cases` | 從 PRD 產 P0/P1/P2 × Happy/Edge/Error/Regression test cases | `prds/{name}/test-cases.md`（覆蓋） |
| `/test-run` | 建 QA 執行紀錄，**`--auto` 模式用 Playwright 自動跑** | `prds/{name}/test-runs/{date}.md` + screenshots |
| `/gen-release-notes` | External + Internal Update，可選推 Slack（學頻道風格） | `prds/{name}/release-notes.md` + Slack post |
| `/gen-hc-content` | Help Center 等級素材（功能介紹 + 情境 + 步驟 + FAQ） | `prds/{name}/hc-content.md` |
| `/translate` | zh-TW → EN/TH/JA + 術語表 + Slack review + cl-locales publish | Google Sheet + 翻譯發布到 Firebase Storage（staging/production） |
| `/verify` | 上線前 build check + Playwright golden path + 截圖報告 | `prds/{name}/verification-{date}.md` + Drive |
| `/release-pipeline` | Orchestrator：串 gen-test-cases → test-run → gen-release-notes → translate → sync-gdoc | 全套產物 + summary dashboard |
| `/ga-tracking` | GA4 SPA 埋碼（gtag.js + 集中式 analytics module + RouteTracker） | `index.html`, `src/lib/analytics.js`, App.jsx |

## 目錄結構

```
.
├── specs/                  # Product Spec（持續演進的 SSOT）
│   └── {domain}/
│       ├── spec.md
│       └── capabilities/
│           └── {name}.md
│
├── prds/                   # PRD（每次專案的變更提案）
│   ├── {prd-name}/           # 進行中
│   │   ├── evaluation.md     #   product-thinking 評估報告
│   │   ├── prd.md            #   PRD 主文（含 Spec Delta）
│   │   ├── review.md         #   review-prd 結果
│   │   ├── test-cases.md     #   測試案例定義
│   │   ├── test-runs/        #   每次測試執行紀錄
│   │   │   └── YYYY-MM-DD.md
│   │   ├── release-notes.md  #   External + Internal
│   │   ├── hc-content.md     #   Help Center 素材
│   │   └── verification-*.md #   上線前驗證報告
│   └── archive/              # 已歸檔
│       └── YYYY-MM-DD-{prd-name}/
│
├── templates/              # 範本
│   ├── prd-template.md
│   ├── test-cases-template.md
│   ├── release-notes-template.md
│   ├── hc-content-template.md
│   └── spec-template.md
│
├── scripts/
│   └── md_to_gdoc.py       # Markdown → Google Doc 格式轉換
│
├── .claude/skills/         # 16 支 SKILL.md
│
└── docs/                   # 靜態網站
    └── index.html
```

## 核心概念

| 概念 | 說明 |
|:-----|:-----|
| **Product Spec** (`specs/`) | 產品規格的 SSOT，描述系統目前的行為，依 domain 分模組 |
| **PRD** (`prds/`) | 針對某次專案的需求文件，描述要對 Product Spec 做什麼變更 |
| **Spec Delta** | PRD 中的區塊，描述對 Product Spec 的差異，歸檔時更新到 `specs/` |
| **evaluation.md** | `/product-thinking` 的 ICE/風險/指標分析存檔 |
| **review.md** | `/review-prd` 四角色 subagent debate 結果 |
| **Test Cases** | 從 PRD 產生的測試案例定義，PRD 改了就重新產生（會被覆蓋） |
| **Test Run** | 每次測試的執行紀錄，從 test cases 複製，QA 打勾用（不會被覆蓋） |
| **Closed Loop** | Slack/會議/Google Doc 的外部討論透過 `/sync-prd` 與 `/pull-gdoc-comments` 回流 |

## 生命週期

```
draft → in-review → approved → archived
```

| 階段 | 動作 | Git 操作 |
|:-----|:-----|:---------|
| **draft** | PM + AI refine PRD | branch + commit `prds/{name}/` |
| **in-review** | team review | 開 PR、用 `/sync-gdoc` 推 Google Doc |
| **approved** | PRD 定稿 | merge PR |
| **archived** | spec-delta 更新 spec + PRD 搬到 archive | `/archive-prd` |

## 典型流程

```
自然對話探索 ──── PM 跟 AI 討論問題、用戶痛點、解法方向
   │
   │ ← /product-thinking ── 結構化評估（ICE、風險、指標）
   │
   │ 方向確定 → 建立 PRD
   ▼
/new-prd ────────── 建 PRD draft + evaluation.md
   │
   │ refine ↔ /sync-prd ── 會議 / Slack 決策回流
   ▼
/review-prd ─────── PM/Eng/QA/PD 四 subagent 平行 review
   │
   │ 修改完成 → 進入發布鏈
   ▼
/release-pipeline ─┬─→ /gen-test-cases ─→ /test-run（--auto Playwright）
                   ├─→ /gen-release-notes ─→ Slack
                   ├─→ /translate ──────→ Sheet → review → publish
                   └─→ /sync-gdoc ──────→ Google Doc
   │
   │ 上線前
   ▼
/verify ─────────── build check + Playwright golden path + 報告
   │
   │ 上線後
   ▼
/archive-prd ────── 更新 specs/ + 搬 archive
```

## 安裝

### 1. Clone

```bash
git clone https://github.com/lydia47/pm-release-accelerator.git
cd pm-release-accelerator
```

### 2. 安裝 gws CLI（Google Workspace）

```bash
npm install -g @googleworkspace/cli
gws auth setup        # 一次性設定 GCP project
gws auth login -s drive,sheets,docs,gmail,calendar
```

### 3. 複製 Skills 到 Claude Code

```bash
# 全 user-level（所有專案可用）
cp -r .claude/skills/* ~/.claude/skills/

# 或 project-level（僅當前 repo）
# .claude/skills/ 直接放在你的 PM repo 即可
```

### 4. （可選）安裝 cl-locales

`/translate` skill 需要 `cl-locales` CLI（前身是 locales-publish，現已改名並大幅擴充功能 — 支援 add/update/delete/publish + batch + AI signature）：

**方式 A（推薦）：透過 Claude Code plugin**
```bash
# 從 chatbotgang/cclab 安裝
# 詳細指令請見 https://github.com/chatbotgang/cclab
```

**方式 B：手動 clone**
```bash
git clone https://github.com/chatbotgang/skills.git /tmp/cl-skills
cp -r /tmp/cl-skills/skills/cl-locales ~/.claude/skills/cl-locales
# 之後在 /translate 中用完整路徑：~/.claude/skills/cl-locales/scripts/locales-cli
```

首次使用需 Firebase 登入：`cl-locales login`（會開瀏覽器）

### 5. （可選）MCP servers

- **Slack** — `/gen-release-notes`、`/translate`、`/sync-prd` 用
- **Playwright** — `/test-run --auto`、`/verify`、`/ga-tracking` 用
- **Figma** — `/test-run`（PD 比對）、`/verify` 用
- **Asana** — `/test-run`（建 bug task）、`/verify` 用

## 整合工具

| 工具 | 用途 | 使用的 Skills |
|:-----|:-----|:-------------|
| **gws CLI** | Google Drive/Sheets/Docs 讀寫 | `/sync-gdoc`, `/pull-gdoc-comments`, `/translate`, `/verify` |
| **Slack MCP** | 讀 thread / 發訊息 / review request | `/sync-prd`, `/gen-release-notes`, `/translate` |
| **Figma MCP** | 設計稿截圖比對 | `/test-run`, `/verify` |
| **Asana MCP** | Bug task 建立 | `/test-run`, `/verify` |
| **Playwright MCP** | AI 驅動瀏覽器測試 | `/test-run --auto`, `/verify`, `/ga-tracking` |
| **GitHub CLI** | Codebase 搜尋 / PR 管理 | `/gen-product-spec`, `/verify` |
| **cl-locales** | 翻譯 CRUD + 發布到 Firebase Storage | `/translate` |

## 與 pm-hub 的關係

本專案是 [pm-hub](https://github.com/chatbotgang/pm-hub) 的**超集**：

- 採用 pm-hub 的 12 支核心 skill（PRD lifecycle + 規格閉環）
- 加上 4 支發布鏈獨有 skill（`/translate`, `/verify`, `/ga-tracking`, `/release-pipeline`）

如果你只需要 PRD 管理 → 用 pm-hub 即可。  
如果你還要做 release / 翻譯 / 上線驗證 / GA 埋碼 → 用本專案。

## 參考

- [pm-hub](https://github.com/chatbotgang/pm-hub) — PRD/Spec 閉環架構來源
- [awesome-cresclab](https://github.com/chatbotgang/awesome-cresclab) — Codebase index
- [gws CLI](https://github.com/googleworkspace/cli) — Google Workspace CLI
- [chatbotgang/skills — cl-locales](https://github.com/chatbotgang/skills/tree/main/skills/cl-locales) — 翻譯 CRUD + publish CLI（取代 locales-publish）
- [chatbotgang/cclab](https://github.com/chatbotgang/cclab) — Claude Code plugin marketplace（含 cl-locales plugin）
- [HC Release Skill](https://github.com/kaddwang/Helping-Center-Release-Skill) — 早期設計參考

---

Built with [Claude Code](https://claude.ai/claude-code)
