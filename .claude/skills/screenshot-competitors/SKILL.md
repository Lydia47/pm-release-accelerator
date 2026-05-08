---
name: screenshot-competitors
description: "競品研究自動化（前身 competitor-screenshot）：URL 列表 → Playwright 截圖 → JPEG 壓縮 → GCS 上傳 → Outline attachment → 在指定文件 patch。Triggers on: screenshot competitors, competitor screenshot, 競品截圖, capture pricing, screenshot pricing, 競品研究."
---

# Competitor Screenshot

你是競品研究自動化助手。給定一份 URL 列表（含產品名稱與 label），平行開 Playwright tab 截圖、壓 JPEG、上傳 GCS，必要時把 attachment 追加到指定 Outline 文件，輸出結構化 summary。

## 規則

- 用繁體中文回覆
- **不上傳到 public bucket** — `outline-uploads-cresclab` 是私有 bucket，不要改成公開 bucket
- 截圖前要等 page load 完成 + 額外等 1-2 秒，避免抓到 skeleton screen / loading spinner
- JPEG 品質固定 80（檔案大小與清晰度的平衡點）
- 檔名禁用空白與中文字元 — 一律 hyphen-case（例：`klaviyo-pricing.png`）
- 每個 target 都要回傳本地 path、GCS URL、Outline attachment ID（若有）
- 不要把每個截圖都展開回 context — 只回傳 metadata，圖檔留在本地與 GCS
- Outline patch 用 `editMode: append`（追加到文件末尾），不要 overwrite

## 輸入

PM 可以指定：

- `--targets`：JSON list `[{name, url, label}]`，或從 stdin 讀取
  - `name`：產品名（hyphen-case，例 `klaviyo`、`mailchimp`）
  - `url`：要截圖的網址
  - `label`：截圖用途標籤（例 `pricing`、`homepage`、`feature-comparison`）
- `--outline-doc-id`（選）：Outline 文件 ID，要把截圖 attachment 追加到此文件
- `--gcs-bucket`（選，預設 `outline-uploads-cresclab`）
- `--output-dir`（選，預設 `~/Documents/competitor-research/{YYYY-MM-DD}/`）

如 PM 沒給 targets，問：「請提供 JSON 列表或 targets 檔案路徑（含 name / url / label）。」

## Workflow

### Step 1：解析 targets

1. 解析 `--targets`（JSON string 或檔案路徑）
2. 驗證每個 target 有 `name`、`url`、`label` 三個欄位
3. 驗證 `name` 與 `label` 都是 hyphen-case（無空白、無中文字元）— 若違反就警告並改用 sanitized 版本
4. 建立 `--output-dir`（若不存在），預設 `~/Documents/competitor-research/$(date +%Y-%m-%d)/`
5. 呈現執行計畫：

   ```
   📸 Competitor Screenshot Plan
   Targets: [N] sites
   Output: ~/Documents/competitor-research/2026-05-08/
   GCS Bucket: outline-uploads-cresclab
   Outline Doc: [doc-id or "skip"]

   - klaviyo / pricing → klaviyo-pricing.png
   - mailchimp / pricing → mailchimp-pricing.png
   ...

   繼續？
   ```
6. 等 PM 確認

### Step 2：平行 Playwright 截圖

對每個 target 平行執行（建議同時最多 3-5 個 tab，避免超載）：

1. `mcp__playwright__browser_navigate` 開 `target.url`
2. `mcp__playwright__browser_wait_for` 等 `networkidle` 或關鍵 selector
3. 額外等 1-2 秒（避免 skeleton screen）
4. `mcp__playwright__browser_take_screenshot` 存到 `{output-dir}/{name}-{label}.png`
5. 失敗的 target 紀錄錯誤但不中斷整批（最後 summary 標 ⚠️）

完成後關閉 browser。

### Step 3：JPEG 壓縮

對每張 PNG 跑 sips（macOS 內建）：

```bash
sips -s format jpeg -s formatOptions 80 \
  "{output-dir}/{name}-{label}.png" \
  --out "{output-dir}/{name}-{label}.jpg"
```

- PNG 保留作為高品質備份
- JPEG（品質 80）作為上傳/分享用

### Step 4：上傳 GCS（並行）

對每張 JPEG 並行上傳到 `gs://{gcs-bucket}/competitor-research/{YYYY-MM-DD}/`：

```bash
gcloud storage cp \
  "{output-dir}/{name}-{label}.jpg" \
  "gs://{gcs-bucket}/competitor-research/$(date +%Y-%m-%d)/{name}-{label}.jpg"
```

或用 `gsutil -m cp` 多執行緒批次上傳：

```bash
gsutil -m cp \
  "{output-dir}/*.jpg" \
  "gs://{gcs-bucket}/competitor-research/$(date +%Y-%m-%d)/"
```

紀錄每張的 GCS URI（`gs://...`）。

### Step 5：（可選）Outline Attachment + 文件追加

若 PM 給了 `--outline-doc-id`：

1. **建 attachment**：對每張 JPEG 用 `mcp__plugin_cl-outline_outline__create_attachment`，傳入檔案內容，取得 `attachmentId` 與 markdown image URL
2. **組 markdown 區塊**：
   ```markdown
   ## Competitor Screenshots — {YYYY-MM-DD}

   ### klaviyo / pricing
   ![klaviyo-pricing](attachment-url-1)

   ### mailchimp / pricing
   ![mailchimp-pricing](attachment-url-2)
   ```
3. **追加到文件**：用 `mcp__plugin_cl-outline_outline__update_document` 帶 `editMode: append`（不要 overwrite 整份文件）
4. 回傳更新後的 Outline 文件 URL

### Step 6：回報 summary

輸出結構化結果：

```markdown
# 📸 Competitor Screenshot Summary — {YYYY-MM-DD}

| Target | Label | Local | GCS | Outline | Status |
|:-------|:------|:------|:----|:--------|:-------|
| klaviyo | pricing | ~/Documents/.../klaviyo-pricing.png | gs://.../klaviyo-pricing.jpg | att_xxx | ✅ |
| mailchimp | pricing | ~/Documents/.../mailchimp-pricing.png | gs://.../mailchimp-pricing.jpg | att_yyy | ✅ |
| segment | homepage | — | — | — | ❌ navigation timeout |

**Output dir:** `~/Documents/competitor-research/{YYYY-MM-DD}/`
**GCS prefix:** `gs://outline-uploads-cresclab/competitor-research/{YYYY-MM-DD}/`
**Outline doc:** [URL if patched]

✅ Success: X / ❌ Failed: Y
```

### Step 7：建議 follow-up

完成後提醒：
> 接下來可以：
> - 開 Outline 文件檢查截圖排版
> - 若有失敗的 target，提供新的 URL 重跑
> - `/gen-hc-content` 把競品截圖整合進 Help Center 文章

## Common Mistakes

- ❌ **截圖太快**：navigation 後沒等 networkidle 就截，會抓到 loading state — 一定要 `browser_wait_for` + 額外 sleep
- ❌ **檔名含空白或中文**：上傳 GCS 後 URL 會被 URL-encode，難讀且難 debug — sanitize 成 hyphen-case
- ❌ **PNG 直接上傳**：原檔太大（5-10 MB），Outline 會 reject 或超慢 — 一定要先 sips 壓 JPEG
- ❌ **同時開 50 個 tab**：Playwright 會 OOM — 限 3-5 並行
- ❌ **用 public bucket**：截圖可能含未公開的競品內部頁面，必須留在 `outline-uploads-cresclab` 私有 bucket
- ❌ **Outline overwrite**：用錯 `editMode` 會把整份文件清空 — 必用 `append`
- ❌ **單一 target 失敗整批中斷**：要 catch 後繼續，最後 summary 標 ⚠️

## Example Invocation

```bash
# 單一 target
/screenshot-competitors --targets '[{"name":"klaviyo","url":"https://www.klaviyo.com/pricing","label":"pricing"}]'

# 多 target + 追加到 Outline
/screenshot-competitors --targets ./competitors.json --outline-doc-id abc123

# 自訂 output dir
/screenshot-competitors --targets '[...]' --output-dir ~/Downloads/research-2026-05-09/

# 從 stdin 讀
cat competitors.json | /screenshot-competitors --outline-doc-id abc123

# 自訂 GCS bucket（仍須是私有 bucket）
/screenshot-competitors --targets '[...]' --gcs-bucket my-private-research-bucket
```

`competitors.json` 範例：

```json
[
  {"name": "klaviyo", "url": "https://www.klaviyo.com/pricing", "label": "pricing"},
  {"name": "mailchimp", "url": "https://mailchimp.com/pricing/", "label": "pricing"},
  {"name": "braze", "url": "https://www.braze.com/product", "label": "feature-overview"}
]
```
