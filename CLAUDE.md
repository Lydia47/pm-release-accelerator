# PM Release Accelerator

## Overview
20 個 Claude Code Skills，分三層：
- **探索層**：`/product-thinking`, `/competitor-screenshot`
- **PRD Lifecycle**（Git-as-SSOT）：`/new-prd`, `/sync-prd`, `/review-prd`, `/sync-gdoc`, `/pull-gdoc-comments`, `/archive-prd`, `/gen-product-spec`, `/outline-patch-safe`
- **發布鏈**：`/gen-test-cases`, `/test-run`, `/gen-release-notes`, `/gen-hc-content`, `/translate`, `/verify`, `/release-pipeline`, `/ga-tracking`, `/deploy-status`, `/announce-slack`

採用 **pm-hub 架構**（PRD/Spec 住在 `prds/`、`specs/`），加上 release-side 自動化。

## 檔案位置

| 路徑 | 內容 |
|------|------|
| `.claude/skills/{name}/SKILL.md` | 各 skill 的指令定義（含 frontmatter trigger） |
| `templates/` | PRD / test-cases / release-notes / hc-content / spec 範本 |
| `scripts/md_to_gdoc.py` | Markdown → Google Docs batchUpdate 轉換 |
| `prds/{name}/` | 進行中的 PRD（含所有產出檔案） |
| `prds/archive/{date}-{name}/` | 已歸檔的 PRD |
| `specs/{domain}/spec.md` | Product Spec SSOT |
| `specs/{domain}/capabilities/{name}.md` | 拆分的 capability spec |

**安裝同步**：修改 skill 後 `cp -r .claude/skills/* ~/.claude/skills/`（user-level 安裝）

## 開發慣例

- **Commit**：conventional commits (`feat:`, `fix:`, `docs:`, `style:`, `refactor:`)
- **Branch**：每個 task 從 main 切獨立 branch（`feature/xxx`, `fix/xxx`, `refactor/xxx`），不 stack
- **PR**：squash merge
- **語言**：Skill 內容繁體中文 + 英文技術詞；README 繁體中文
- **Skill 結構**：frontmatter（name + description with triggers）→ Title → Rules → Inputs → Workflow → Common Mistakes（如有）→ Example Invocation

## Skill Frontmatter 格式

```yaml
---
name: skill-name
description: "一行描述功能。Triggers on: keyword1, keyword2, 中文觸發詞."
---
```

`description` 內的 `Triggers on:` 是 Claude Code 觸發判斷依據，列關鍵詞（含中英）。

## 關鍵整合

| 工具 | 路徑 | 使用的 Skills |
|:-----|:-----|:-------------|
| gws CLI | `~/.cargo/bin/gws` | `/sync-gdoc`, `/pull-gdoc-comments`, `/translate`, `/verify`, `/announce-slack` |
| Slack MCP | — | `/sync-prd`, `/gen-release-notes`, `/translate`, `/announce-slack` |
| Playwright MCP | — | `/test-run --auto`, `/verify`, `/ga-tracking`, `/competitor-screenshot` |
| Figma MCP | — | `/test-run`（PD 比對）, `/verify` |
| Asana MCP | — | `/test-run`, `/verify` |
| GitHub MCP / CLI | `gh` | `/gen-product-spec`, `/verify`, `/deploy-status` |
| cl-outline plugin | `mcp__plugin_cl-outline_outline__*` | `/outline-patch-safe`, `/announce-slack`, `/competitor-screenshot` |
| GCS (gcloud/gsutil) | — | `/competitor-screenshot` |
| Firebase CLI | `firebase` | `/deploy-status`（Firebase Hosting release 查詢） |
| cl-locales | `cl-locales`（plugin）or `~/.claude/skills/cl-locales/scripts/locales-cli`（手動） | `/translate` |

## Spec / PRD 連動機制

- **PRD 寫在 `prds/{name}/prd.md`** — frontmatter 含 `status` (draft/in-review/approved/archived)、`domain`、`gdoc_id`（如同步過）
- **Spec Delta** — PRD 中的 `## Spec Delta` 區塊標 Added/Modified/Removed
- **歸檔時 `/archive-prd`** — 讀 Spec Delta 更新 `specs/{domain}/spec.md`，搬 PRD 到 `prds/archive/{date}-{name}/`
- **Test cases 與 PRD 同步** — PRD 改了就重跑 `/gen-test-cases` 覆蓋 `test-cases.md`；test runs 不會被覆蓋
- **Google Doc snapshot** — `/sync-gdoc` 每個 .md 對應一個 tab；source of truth 是 repo

## 部署

- **GitHub Pages**: `index.html`（single-page slide deck，已對齊 20 skill 三層架構）
- 修改後 push 到 main 即自動部署到 https://lydia47.github.io/pm-release-accelerator/

## 與 pm-hub 的關係

- pm-hub 是上游：所有 PRD lifecycle skill 來自 pm-hub
- 本 repo 是超集：加上 4 支發布鏈獨有 skill（translate, verify, ga-tracking, release-pipeline）
- 若 pm-hub 更新核心 skill，可手動 sync：`cp -r ~/pm-hub/.claude/skills/{name}/SKILL.md .claude/skills/{name}/`
