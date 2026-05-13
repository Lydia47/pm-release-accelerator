# PM Release Accelerator

## Overview
25 個 Claude Code Skills，分四層（2026-05-13 優化：移除 4 個低使用率 skill、補進 3 個本地獨有 skill、aggressive description 重寫）：
- **探索層**：`/evaluate-feature`（scope 模糊時銜接 superpowers:brainstorming）、`/competitive-research`
- **PRD Lifecycle**（Git-as-SSOT）：`/new-prd`, `/sync-prd`, `/review-prd`, `/triple-a-review`, `/sync-outline`, `/pull-outline-comments`, `/sync-gdoc`, `/pull-gdoc-comments`, `/archive-prd`, `/gen-product-spec`, `/patch-outline-safely`, `/tidy-outline-headings`, `/check-prd-status`
- **發布鏈**：`/gen-test-cases`, `/record-test-run`, `/gen-release-notes`, `/gen-hc-content`, `/translate-locales`, `/verify-release`, `/run-release-pipeline`, `/embed-ga4`, `/announce-launch`
- **工具型**：`/pack-repo`（Repomix 打包 repo context 給非技術同事或 Claude Web）

**已歸檔到 `~/.claude/skills-archive/`**（30 天 0 使用率，需要時可手動 mv 回來）：`screenshot-competitors`, `run-launch-retro`, `sync-task-board`, `sync-spec-to-prd`, `check-deploy-status`, `init-project`, `locales-publish`（已被 translate-locales 取代）

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
| gws CLI | `~/.cargo/bin/gws` | `/sync-gdoc`, `/pull-gdoc-comments`, `/translate-locales`, `/verify-release`, `/announce-launch` |
| Slack MCP | — | `/sync-prd`, `/gen-release-notes`, `/translate-locales`, `/announce-launch` |
| Playwright MCP | — | `/record-test-run --auto`, `/verify-release`, `/embed-ga4` |
| Figma MCP | — | `/record-test-run`（PD 比對）, `/verify-release` |
| Asana MCP | — | `/record-test-run`, `/verify-release` |
| GitHub MCP / CLI | `gh` | `/gen-product-spec`, `/verify-release` |
| cl-outline plugin | `mcp__plugin_cl-outline_outline__*` | **`/sync-outline`**, **`/pull-outline-comments`**, `/patch-outline-safely`, `/announce-launch` |
| cl-locales | `cl-locales`（plugin）or `~/.claude/skills/cl-locales/scripts/locales-cli`（手動） | `/translate-locales` |

## Spec / PRD 連動機制

- **PRD 寫在 `prds/{name}/prd.md`** — frontmatter 含 `status` (draft/in-review/approved/archived)、`domain`、`outline_doc_id`（內部 SSOT primary）、`gdoc_id`（對外 alternative）
- **Spec Delta** — PRD 中的 `## Spec Delta` 區塊標 Added/Modified/Removed
- **歸檔時 `/archive-prd`** — 讀 Spec Delta 更新 `specs/{domain}/spec.md`，搬 PRD 到 `prds/archive/{date}-{name}/`
- **Test cases 與 PRD 同步** — PRD 改了就重跑 `/gen-test-cases` 覆蓋 `test-cases.md`；test runs 不會被覆蓋
- **Outline snapshot（primary）** — `/sync-outline` 每個 .md 對應一個 nested child doc；內部 SSOT 預設路徑
- **Google Doc snapshot（cross-org alternative）** — `/sync-gdoc` 每個 .md 對應一個 tab；給沒 Outline 帳號的外部 stakeholder
- **Source of truth 永遠是 repo** — Outline / GDoc 都是 read-only snapshot

## 部署

- **GitHub Pages**: `index.html`（single-page slide deck，已對齊 24 skill 三層架構）
- 修改後 push 到 main 即自動部署到 https://lydia47.github.io/pm-release-accelerator/

## 與 pm-hub 的關係

- pm-hub 是上游：所有 PRD lifecycle skill 來自 pm-hub
- 本 repo 是超集：加上 4 支發布鏈獨有 skill（translate-locales, verify-release, embed-ga4, run-release-pipeline）
- 若 pm-hub 更新核心 skill，可手動 sync：`cp -r ~/pm-hub/.claude/skills/{name}/SKILL.md .claude/skills/{name}/`
