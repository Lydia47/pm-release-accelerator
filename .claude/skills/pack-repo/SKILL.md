---
name: pack-repo
description: "**Use IMMEDIATELY when user wants to bundle a repo into Claude-readable context** — phrases like pack repo / 打包 repo / 產生 repo context / repomix / 給非技術同事看 codebase / share codebase context / 給 Claude Web 用 / 把 repo 打包 / 整個 repo 給 AI 看 / repo 全文. Uses Repomix to produce a single AI-friendly XML at the working directory. Best for teammates without local Claude Code access or one-shot codebase reviews."
user_invocable: true
---

# Pack Repo — 為非技術同事打包 Repo Context

## 任務
使用 Repomix MCP 將指定 repo 打包成 AI 友好的單一檔案，方便非技術同事在 Claude Web/Desktop 使用。

## 步驟

1. **確認目標 repo**
   - 如果在專案目錄中，預設打包當前 repo
   - 如果使用者指定 GitHub URL，使用 `pack_remote_repository`

2. **執行打包**
   - 使用 Repomix MCP 的 `pack_codebase` 工具
   - 或使用 CLI：`npx repomix@latest --compress`（加 `--compress` 減少 70% tokens）

3. **產出檔案**
   - 預設輸出：`repomix-output.xml`
   - 告知使用者檔案位置與大小

4. **使用說明**
   - 提供給非技術同事的使用方式：
     - 打開 claude.ai
     - 點「附加檔案」上傳 repomix-output.xml
     - 開始對話，Claude 會有完整 repo context

## 替代方案
如果只需要快速瀏覽 GitHub 上的 repo：
- 把 `github.com` 改成 `gitingest.com`
- 例：`gitingest.com/user/repo`
- 零安裝，直接在瀏覽器操作
