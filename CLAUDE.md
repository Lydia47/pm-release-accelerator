# PM Release Accelerator

## Overview
6 個 Claude Code Skills 自動化 PM release lifecycle：`/prd` → `/test-case` → `/release-note` → `/translate`，由 `/release-pipeline` 串接，搭配 `/verify` 上線驗證。

## Skills 檔案位置
- Skills: `.claude/commands/*.md`
- Resources: `.claude/commands/resources/prd-template.md`
- 安裝路徑同步：修改後需 `cp -r .claude/commands/* ~/.claude/commands/`

## 開發慣例
- Commit message: conventional commits (`feat:`, `fix:`, `docs:`, `style:`, `refactor:`)
- Branch: `feature/xxx`, `fix/xxx` → PR → squash merge
- 語言：Skill 內容繁體中文 + 英文技術詞；README 繁體中文
- Skill 結構：# Title → ## Inputs → ## Workflow (Phase 1-N) → ## Rules → ## Example Invocation

## 關鍵整合
- `gws CLI` (`~/.cargo/bin/gws`) — Google Drive/Sheets/Docs
- Slack MCP — 發訊息、搜尋頻道歷史
- Playwright MCP — 瀏覽器自動化（/test-case, /verify）
- Asana MCP — Bug task 建立
- GitHub CLI (`gh`) — Codebase 搜尋、PR 管理

## Placeholder 機制
PRD Google Doc 使用 `{{PLACEHOLDER}}` markers，下游 skill 用 `replaceAllText` API 回寫：
- `{{TEST_CASE_CONTENT}}` ← `/test-case`
- `{{INTERNAL_UPDATE_CONTENT}}` ← `/release-note`

## 部署
- GitHub Pages: `index.html` (single-page slide deck)
- 修改 index.html 後 push 即自動部署
