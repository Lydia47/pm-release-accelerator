#!/usr/bin/env python3
"""
Sync PRD markdown files to a Google Doc with formatted content.

Converts markdown syntax to Google Docs batchUpdate API requests,
preserving headings, bold, inline code, bullet/numbered lists,
code blocks, blockquotes, tables, and horizontal rules.

Requires: gws CLI authenticated.

Usage:
    # Sync a PRD folder to Google Doc (create or update)
    python3 scripts/md_to_gdoc.py sync <prd_dir>

    # Write to an existing Doc with explicit tab mapping
    python3 scripts/md_to_gdoc.py write <doc_id> <prd_dir> <tab_mapping_json>

Commands:
    sync <prd_dir>
        Scans the PRD folder for .md files, creates a new Google Doc
        (or updates an existing one if gdoc_id is in prd.md frontmatter),
        and writes formatted content to one tab per file.

    write <doc_id> <prd_dir> <tab_mapping_json>
        Writes to an existing Doc with an explicit tab mapping.
        Low-level command used internally by sync.

File-to-tab mapping:
    evaluation.md    -> Evaluation
    prd.md           -> PRD
    review.md        -> Agent Reviews
    test-cases.md    -> Test Cases
    release-notes.md -> Release Notes
    hc-content.md    -> HC Content

Supported markdown syntax:
    # through ###### headings, **bold**, `inline code`, ~~strikethrough~~,
    bullet lists (- / *), numbered lists (1.), checkbox lists (- [ ] / - [x]),
    code blocks (```), blockquotes (>), tables (| ... |), horizontal rules (---)
"""
import json
import os
import re
import subprocess
import sys


# --- File/tab mapping ---

FILE_TAB_MAP = {
    "evaluation.md": {"key": "evaluation", "title": "Evaluation"},
    "prd.md": {"key": "prd", "title": "PRD"},
    "review.md": {"key": "agent-reviews", "title": "Agent Reviews"},
    "test-cases.md": {"key": "test-cases", "title": "Test Cases"},
    "release-notes.md": {"key": "release-notes", "title": "Release Notes"},
    "hc-content.md": {"key": "hc-content", "title": "HC Content"},
}

# Ordered list for consistent tab ordering
TAB_ORDER = [
    "evaluation.md", "prd.md", "review.md",
    "test-cases.md", "release-notes.md", "hc-content.md",
]


# --- Frontmatter helpers ---

def read_frontmatter(filepath):
    """Read YAML frontmatter from a markdown file (simple key: value parser)."""
    with open(filepath, 'r') as f:
        text = f.read()
    if text.startswith('---'):
        end = text.find('---', 3)
        if end != -1:
            fm_text = text[3:end]
            result = {}
            for line in fm_text.strip().split('\n'):
                match = re.match(r'^(\w[\w_]*)\s*:\s*(.+)$', line.strip())
                if match:
                    key = match.group(1)
                    value = match.group(2).strip().strip('"').strip("'")
                    result[key] = value
            return result
    return {}


def update_frontmatter(filepath, updates):
    """Update specific fields in a markdown file's YAML frontmatter."""
    with open(filepath, 'r') as f:
        text = f.read()

    if text.startswith('---'):
        end = text.find('---', 3)
        if end != -1:
            fm_text = text[3:end]
            body = text[end + 3:]

            # Parse existing lines, preserving order and comments
            lines = fm_text.strip().split('\n')
            updated_keys = set()
            new_lines = []
            for line in lines:
                match = re.match(r'^(\w[\w_]*)\s*:', line)
                if match and match.group(1) in updates:
                    key = match.group(1)
                    val = updates[key]
                    new_lines.append(f'{key}: "{val}"')
                    updated_keys.add(key)
                else:
                    new_lines.append(line)

            # Append new keys not already present
            for key, val in updates.items():
                if key not in updated_keys:
                    new_lines.append(f'{key}: "{val}"')

            new_fm = '\n'.join(new_lines)
            with open(filepath, 'w') as f:
                f.write(f"---\n{new_fm}\n---{body}")
            return

    # No frontmatter exists, prepend one
    fm_lines = [f'{k}: "{v}"' for k, v in updates.items()]
    fm = '\n'.join(fm_lines)
    with open(filepath, 'w') as f:
        f.write(f"---\n{fm}\n---\n\n{text}")


def strip_frontmatter(text):
    """Remove YAML frontmatter from markdown text."""
    if text.startswith('---'):
        end = text.find('---', 3)
        if end != -1:
            return text[end + 3:].lstrip('\n')
    return text


# --- GWS CLI helpers ---

def gws_run(args, input_json=None):
    """Run a gws CLI command and return parsed JSON output."""
    cmd = ["gws"] + args
    if input_json:
        cmd.extend(["--json", json.dumps(input_json)])
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"gws error: {result.stderr[:500]}")
    return json.loads(result.stdout) if result.stdout.strip() else {}


def create_doc(title):
    """Create a new Google Doc and return its ID."""
    resp = gws_run(
        ["docs", "documents", "create"],
        input_json={"title": title}
    )
    return resp["documentId"]


def get_doc_tabs(doc_id):
    """Get existing tabs from a Google Doc. Returns {title: tab_id}."""
    resp = gws_run([
        "docs", "documents", "get",
        "--params", json.dumps({"documentId": doc_id, "includeTabsContent": True})
    ])
    tabs = {}
    for tab in resp.get("tabs", []):
        props = tab.get("tabProperties", {})
        tabs[props.get("title", "")] = props.get("tabId", "")
    return tabs


def rename_tab(doc_id, tab_id, new_title):
    """Rename a Google Doc tab."""
    gws_run(
        ["docs", "documents", "batchUpdate",
         "--params", json.dumps({"documentId": doc_id})],
        input_json={
            "requests": [{
                "updateDocumentTabProperties": {
                    "tabProperties": {"tabId": tab_id, "title": new_title},
                    "fields": "title"
                }
            }]
        }
    )


def add_tab(doc_id, title):
    """Add a new tab to a Google Doc and return its tab_id."""
    resp = gws_run(
        ["docs", "documents", "batchUpdate",
         "--params", json.dumps({"documentId": doc_id})],
        input_json={
            "requests": [{"addDocumentTab": {"tabProperties": {"title": title}}}]
        }
    )
    for r in resp.get("replies", []):
        adt = r.get("addDocumentTab", {})
        if adt:
            return adt.get("tabProperties", {}).get("tabId")
    return None


# --- Markdown parsing ---

def process_inline_formatting(text, base_idx, tab_id):
    """Process **bold**, `code`, and ~~strikethrough~~."""
    style_requests = []
    result = ""
    pos = 0

    while pos < len(text):
        bold_match = re.search(r'\*\*(.+?)\*\*', text[pos:])
        code_match = re.search(r'`([^`]+)`', text[pos:])
        strike_match = re.search(r'~~(.+?)~~', text[pos:])

        matches = []
        if bold_match:
            matches.append(('bold', bold_match, pos + bold_match.start()))
        if code_match:
            matches.append(('code', code_match, pos + code_match.start()))
        if strike_match:
            matches.append(('strikethrough', strike_match, pos + strike_match.start()))

        if not matches:
            result += text[pos:]
            break

        matches.sort(key=lambda x: x[2])
        match_type, match, match_start = matches[0]

        result += text[pos:match_start]
        current_idx = base_idx + len(result)
        inner = match.group(1)
        result += inner

        if match_type == 'bold':
            style_requests.append({
                "updateTextStyle": {
                    "textStyle": {"bold": True},
                    "range": {"startIndex": current_idx, "endIndex": current_idx + len(inner), "tabId": tab_id},
                    "fields": "bold"
                }
            })
        elif match_type == 'code':
            style_requests.append({
                "updateTextStyle": {
                    "textStyle": {
                        "weightedFontFamily": {"fontFamily": "Roboto Mono", "weight": 400},
                        "foregroundColor": {"color": {"rgbColor": {"red": 0.09, "green": 0.5, "blue": 0.22}}}
                    },
                    "range": {"startIndex": current_idx, "endIndex": current_idx + len(inner), "tabId": tab_id},
                    "fields": "weightedFontFamily,foregroundColor"
                }
            })
        elif match_type == 'strikethrough':
            style_requests.append({
                "updateTextStyle": {
                    "textStyle": {"strikethrough": True},
                    "range": {"startIndex": current_idx, "endIndex": current_idx + len(inner), "tabId": tab_id},
                    "fields": "strikethrough"
                }
            })

        pos = match_start + len(match.group(0))

    return result, style_requests


def _is_wide_char(ch):
    """Check if a character is a CJK wide character (occupies 2 columns)."""
    cp = ord(ch)
    return (
        (0x1100 <= cp <= 0x115F) or   # Hangul Jamo
        (0x2E80 <= cp <= 0x9FFF) or   # CJK Radicals .. CJK Unified Ideographs
        (0xAC00 <= cp <= 0xD7AF) or   # Hangul Syllables
        (0xF900 <= cp <= 0xFAFF) or   # CJK Compatibility Ideographs
        (0xFE30 <= cp <= 0xFE4F) or   # CJK Compatibility Forms
        (0xFF01 <= cp <= 0xFF60) or   # Fullwidth Forms
        (0xFFE0 <= cp <= 0xFFE6) or   # Fullwidth Signs
        (0x20000 <= cp <= 0x2FA1F)    # CJK Extension B..F, Compatibility Supplement
    )


def _display_width(text):
    """Calculate display width: CJK characters count as 2, others as 1."""
    return sum(2 if _is_wide_char(ch) else 1 for ch in text)


def _pad_to_width(text, target_width):
    """Pad text with spaces to reach target display width."""
    current = _display_width(text)
    padding = target_width - current
    return text + ' ' * max(0, padding)


def parse_markdown_to_requests(md_text, tab_id, start_index=1):
    """Parse markdown text and return Google Docs batchUpdate requests."""
    requests = []
    idx = start_index
    lines = md_text.split('\n')
    i = 0
    heading_map = {
        1: 'HEADING_1', 2: 'HEADING_2', 3: 'HEADING_3',
        4: 'HEADING_4', 5: 'HEADING_5', 6: 'HEADING_6'
    }

    while i < len(lines):
        line = lines[i]

        if line.strip() == '':
            i += 1
            continue

        # Horizontal rule — render as empty paragraph with bottom border
        if re.match(r'^---+\s*$', line.strip()):
            text = '\n'
            requests.append({"insertText": {"text": text, "location": {"index": idx, "tabId": tab_id}}})
            requests.append({
                "updateParagraphStyle": {
                    "paragraphStyle": {
                        "borderBottom": {
                            "color": {"color": {"rgbColor": {"red": 0.8, "green": 0.8, "blue": 0.8}}},
                            "width": {"magnitude": 1, "unit": "PT"},
                            "padding": {"magnitude": 6, "unit": "PT"},
                            "dashStyle": "SOLID"
                        }
                    },
                    "range": {"startIndex": idx, "endIndex": idx + len(text), "tabId": tab_id},
                    "fields": "borderBottom"
                }
            })
            idx += len(text)
            i += 1
            continue

        # Table — real Google Docs Table.
        # Formula (verified against API):
        #   - insertTable at location T creates a table that occupies [T+1, T+1+empty_size)
        #   - empty_size = 2 + R * (2C + 1)
        #   - cell (r, c) text-insertion start = T + 4 + r * (2C + 1) + 2c
        #   - next valid insertion location after table = T + 1 + empty_size + total_text
        # We insert cells in REVERSE order so each insertText doesn't shift earlier cells' indices.
        if '|' in line and i + 1 < len(lines) and re.match(r'^[\s|:-]+$', lines[i + 1]):
            headers = [c.strip() for c in line.strip().strip('|').split('|')]
            i += 2
            rows = []
            while i < len(lines) and '|' in lines[i] and lines[i].strip() and not re.match(r'^[\s|:-]+$', lines[i]):
                cells = [c.strip() for c in lines[i].strip().strip('|').split('|')]
                rows.append(cells)
                i += 1

            num_cols = len(headers)
            for row in rows:
                while len(row) < num_cols:
                    row.append('')
                del row[num_cols:]

            all_rows = [headers] + rows
            num_rows = len(all_rows)
            T = idx

            requests.append({
                "insertTable": {
                    "rows": num_rows,
                    "columns": num_cols,
                    "location": {"index": T, "tabId": tab_id}
                }
            })

            for r in range(num_rows - 1, -1, -1):
                for c in range(num_cols - 1, -1, -1):
                    cell_text = all_rows[r][c]
                    if cell_text:
                        cell_pos = T + 4 + r * (2 * num_cols + 1) + 2 * c
                        requests.append({
                            "insertText": {
                                "text": cell_text,
                                "location": {"index": cell_pos, "tabId": tab_id}
                            }
                        })

            # Bold the header row.
            # After all cell inserts, header cell c starts at:
            #   T + 4 + sum(len(headers[k]) for k<c) + 2c
            # Last cell ends at: cell_start + len(headers[C-1])
            cum_header_chars = sum(len(h) for h in headers)
            row0_start = T + 4
            row0_end = T + 4 + cum_header_chars + (num_cols - 1) * 2
            if row0_end > row0_start:
                requests.append({
                    "updateTextStyle": {
                        "textStyle": {"bold": True},
                        "range": {"startIndex": row0_start, "endIndex": row0_end, "tabId": tab_id},
                        "fields": "bold"
                    }
                })

            empty_size = 2 + num_rows * (2 * num_cols + 1)
            total_text = sum(len(all_rows[r][c]) for r in range(num_rows) for c in range(num_cols))
            idx = T + 1 + empty_size + total_text
            continue

        # Headings (h1-h6)
        heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if heading_match:
            level = len(heading_match.group(1))
            raw_text = heading_match.group(2).strip()
            raw_text = re.sub(r'\*\*(.+?)\*\*', r'\1', raw_text)
            raw_text = re.sub(r'`(.+?)`', r'\1', raw_text)
            text = raw_text + '\n'
            requests.append({"insertText": {"text": text, "location": {"index": idx, "tabId": tab_id}}})
            requests.append({
                "updateParagraphStyle": {
                    "paragraphStyle": {"namedStyleType": heading_map.get(level, 'HEADING_6')},
                    "range": {"startIndex": idx, "endIndex": idx + len(text), "tabId": tab_id},
                    "fields": "namedStyleType"
                }
            })
            idx += len(text)
            i += 1
            continue

        # Checkbox list — use Google Docs native checkbox bullet (BULLET_CHECKBOX),
        # not a unicode glyph in the text. For [x] (checked), apply strikethrough on the text.
        checkbox_match = re.match(r'^(\s*)[-*]\s+\[([ xX])\]\s+(.+)$', line)
        if checkbox_match:
            checked = checkbox_match.group(2) in ('x', 'X')
            text_content = checkbox_match.group(3).strip() + '\n'
            plain_text, style_reqs = process_inline_formatting(text_content, idx, tab_id)
            requests.append({"insertText": {"text": plain_text, "location": {"index": idx, "tabId": tab_id}}})
            requests.append({
                "createParagraphBullets": {
                    "range": {"startIndex": idx, "endIndex": idx + len(plain_text), "tabId": tab_id},
                    "bulletPreset": "BULLET_CHECKBOX"
                }
            })
            if checked and len(plain_text) > 1:
                requests.append({
                    "updateTextStyle": {
                        "textStyle": {"strikethrough": True},
                        "range": {"startIndex": idx, "endIndex": idx + len(plain_text) - 1, "tabId": tab_id},
                        "fields": "strikethrough"
                    }
                })
            requests.extend(style_reqs)
            idx += len(plain_text)
            i += 1
            continue

        # Bullet list — collect consecutive bullet lines into ONE list, so
        # createParagraphBullets correctly derives nestingLevel from the
        # leading-tab convention. (Per-line createBullets does NOT recognize
        # leading tabs as nesting hints; it requires multiple paragraphs in
        # a single createBullets range.) Leading tabs are removed by
        # createParagraphBullets after nesting is derived.
        bullet_match = re.match(r'^(\s*)[-*]\s+(.+)$', line)
        # Exclude checkbox bullets (handled by the checkbox branch above)
        if bullet_match and not re.match(r'^(\s*)[-*]\s+\[([ xX])\]\s+', line):
            list_start = idx
            collected = []  # list of (text_with_tabs, nesting)
            while i < len(lines):
                # Stop on checkbox / numbered / non-bullet lines
                if re.match(r'^(\s*)[-*]\s+\[([ xX])\]\s+', lines[i]):
                    break
                bm = re.match(r'^(\s*)[-*]\s+(.+)$', lines[i])
                if not bm:
                    break
                nesting = len(bm.group(1)) // 2
                text_line = '\t' * nesting + bm.group(2).strip() + '\n'
                collected.append((text_line, nesting))
                i += 1

            # Process inline formatting (**bold**, `code`, ~~strike~~) per line.
            # process_inline_formatting returns (plain_text_with_markers_stripped, style_reqs).
            plain_lines = []
            inline_style_reqs = []
            cumulative_offset = 0
            for text_line, _ in collected:
                line_idx = list_start + cumulative_offset
                plain_text, line_styles = process_inline_formatting(text_line, line_idx, tab_id)
                plain_lines.append(plain_text)
                inline_style_reqs.extend(line_styles)
                cumulative_offset += len(plain_text)

            full_text = ''.join(plain_lines)
            requests.append({"insertText": {"text": full_text, "location": {"index": list_start, "tabId": tab_id}}})
            requests.extend(inline_style_reqs)
            requests.append({
                "createParagraphBullets": {
                    "range": {"startIndex": list_start, "endIndex": list_start + len(full_text), "tabId": tab_id},
                    "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE"
                }
            })
            total_tabs_removed = sum(n for _, n in collected)
            idx = list_start + len(full_text) - total_tabs_removed
            continue

        # Numbered list
        numbered_match = re.match(r'^(\s*)\d+\.\s+(.+)$', line)
        if numbered_match:
            text_content = numbered_match.group(2).strip() + '\n'
            plain_text, style_reqs = process_inline_formatting(text_content, idx, tab_id)
            requests.append({"insertText": {"text": plain_text, "location": {"index": idx, "tabId": tab_id}}})
            requests.append({
                "createParagraphBullets": {
                    "range": {"startIndex": idx, "endIndex": idx + len(plain_text), "tabId": tab_id},
                    "bulletPreset": "NUMBERED_DECIMAL_NESTED"
                }
            })
            requests.extend(style_reqs)
            idx += len(plain_text)
            i += 1
            continue

        # Code block
        if line.strip().startswith('```'):
            i += 1
            code_lines = []
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            i += 1
            code_text = '\n'.join(code_lines) + '\n'
            if code_text.strip():
                requests.append({"insertText": {"text": code_text, "location": {"index": idx, "tabId": tab_id}}})
                requests.append({
                    "updateTextStyle": {
                        "textStyle": {
                            "weightedFontFamily": {"fontFamily": "Roboto Mono", "weight": 400},
                            "fontSize": {"magnitude": 9, "unit": "PT"},
                            "backgroundColor": {"color": {"rgbColor": {"red": 0.95, "green": 0.95, "blue": 0.95}}}
                        },
                        "range": {"startIndex": idx, "endIndex": idx + len(code_text), "tabId": tab_id},
                        "fields": "weightedFontFamily,fontSize,backgroundColor"
                    }
                })
                idx += len(code_text)
            continue

        # Blockquote
        if line.startswith('> '):
            text = line[2:].strip() + '\n'
            plain_text, style_reqs = process_inline_formatting(text, idx, tab_id)
            requests.append({"insertText": {"text": plain_text, "location": {"index": idx, "tabId": tab_id}}})
            requests.append({
                "updateParagraphStyle": {
                    "paragraphStyle": {
                        "indentStart": {"magnitude": 30, "unit": "PT"},
                    },
                    "range": {"startIndex": idx, "endIndex": idx + len(plain_text), "tabId": tab_id},
                    "fields": "indentStart"
                }
            })
            requests.extend(style_reqs)
            idx += len(plain_text)
            i += 1
            continue

        # Normal paragraph
        text = line + '\n'
        plain_text, style_reqs = process_inline_formatting(text, idx, tab_id)
        requests.append({"insertText": {"text": plain_text, "location": {"index": idx, "tabId": tab_id}}})
        requests.extend(style_reqs)
        idx += len(plain_text)
        i += 1

    return requests


# --- Google Doc operations ---

def send_batch(doc_id, requests):
    """Send batchUpdate requests in chunks of 100."""
    chunk_size = 100
    for i in range(0, len(requests), chunk_size):
        chunk = requests[i:i + chunk_size]
        payload = json.dumps({"requests": chunk})
        params = json.dumps({"documentId": doc_id})
        result = subprocess.run(
            ["gws", "docs", "documents", "batchUpdate", "--params", params, "--json", payload],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"  ERROR: {result.stderr[:300]}", file=sys.stderr)
            return False
    return True


def clear_tab(doc_id, tab_id):
    """Clear all content from a tab."""
    resp = gws_run([
        "docs", "documents", "get",
        "--params", json.dumps({"documentId": doc_id, "includeTabsContent": True})
    ])
    for tab in resp.get("tabs", []):
        if tab.get("tabProperties", {}).get("tabId") == tab_id:
            content = tab.get("documentTab", {}).get("body", {}).get("content", [])
            if len(content) > 1:
                start = content[1].get("startIndex", 1)
                end = content[-1].get("endIndex", 1) - 1
                if end > start:
                    send_batch(doc_id, [{
                        "deleteContentRange": {
                            "range": {"startIndex": start, "endIndex": end, "tabId": tab_id}
                        }
                    }])


def write_tab(doc_id, tab_id, md_filepath):
    """Clear a tab and write formatted markdown content."""
    with open(md_filepath, 'r') as f:
        md_text = f.read()
    md_text = strip_frontmatter(md_text)

    clear_tab(doc_id, tab_id)
    requests = parse_markdown_to_requests(md_text, tab_id)
    return send_batch(doc_id, requests), len(requests)


# --- Sync command ---

def cmd_sync(prd_dir):
    """Create or update a Google Doc from a PRD folder."""
    prd_path = os.path.join(prd_dir, "prd.md")
    if not os.path.exists(prd_path):
        print(f"ERROR: {prd_path} not found")
        sys.exit(1)

    # Scan existing files
    existing_files = []
    for filename in TAB_ORDER:
        filepath = os.path.join(prd_dir, filename)
        if os.path.exists(filepath):
            existing_files.append(filename)

    if not existing_files:
        print("ERROR: No markdown files found in PRD folder")
        sys.exit(1)

    print(f"Found {len(existing_files)} files: {', '.join(existing_files)}")

    # Check for existing gdoc_id
    fm = read_frontmatter(prd_path)
    doc_id = fm.get("gdoc_id")
    is_new = doc_id is None

    if is_new:
        # Create new doc
        title = fm.get("title", os.path.basename(prd_dir))
        doc_title = f"[PRD] {title}"
        print(f"Creating new Google Doc: {doc_title}")
        doc_id = create_doc(doc_title)
        print(f"  Doc ID: {doc_id}")

        # Set up tabs: rename first tab, create the rest
        first_file = existing_files[0]
        first_tab_title = FILE_TAB_MAP[first_file]["title"]
        rename_tab(doc_id, "t.0", first_tab_title)
        tab_mapping = {first_file: "t.0"}

        for filename in existing_files[1:]:
            tab_title = FILE_TAB_MAP[filename]["title"]
            tab_id = add_tab(doc_id, tab_title)
            tab_mapping[filename] = tab_id
            print(f"  Created tab: {tab_title} ({tab_id})")

    else:
        # Update existing doc
        print(f"Updating existing Google Doc: {doc_id}")
        existing_tabs = get_doc_tabs(doc_id)

        tab_mapping = {}
        for filename in existing_files:
            tab_title = FILE_TAB_MAP[filename]["title"]
            if tab_title in existing_tabs:
                tab_mapping[filename] = existing_tabs[tab_title]
            else:
                tab_id = add_tab(doc_id, tab_title)
                tab_mapping[filename] = tab_id
                print(f"  Created new tab: {tab_title} ({tab_id})")

    # Write content to each tab
    print()
    for filename in existing_files:
        tab_id = tab_mapping[filename]
        tab_title = FILE_TAB_MAP[filename]["title"]
        filepath = os.path.join(prd_dir, filename)

        print(f"{tab_title}: ", end="", flush=True)
        ok, req_count = write_tab(doc_id, tab_id, filepath)
        status = "OK" if ok else "FAIL"
        print(f"{req_count} requests ... {status}")

    # Update frontmatter with gdoc_id
    gdoc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
    if is_new:
        update_frontmatter(prd_path, {
            "gdoc_id": doc_id,
            "gdoc_url": gdoc_url,
        })
        print("\nUpdated prd.md frontmatter with gdoc_id")

    print(f"\nGoogle Doc: {gdoc_url}")


# --- Write command (low-level) ---

def cmd_write(doc_id, prd_dir, tab_mapping_json):
    """Write to an existing Doc with explicit tab mapping."""
    tab_mapping = json.loads(tab_mapping_json)

    key_to_file = {}
    for filename, info in FILE_TAB_MAP.items():
        key_to_file[info["key"]] = filename

    for tab_key, tab_id in tab_mapping.items():
        filename = key_to_file.get(tab_key)
        if not filename:
            continue

        filepath = os.path.join(prd_dir, filename)
        if not os.path.exists(filepath):
            print(f"SKIP: {tab_key}")
            continue

        tab_title = FILE_TAB_MAP[filename]["title"]
        print(f"{tab_title}: ", end="", flush=True)
        ok, req_count = write_tab(doc_id, tab_id, filepath)
        status = "OK" if ok else "FAIL"
        print(f"{req_count} requests ... {status}")


# --- Main ---

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if command == "sync":
        if len(sys.argv) < 3:
            print("Usage: md_to_gdoc.py sync <prd_dir>")
            sys.exit(1)
        cmd_sync(sys.argv[2])

    elif command == "write":
        if len(sys.argv) < 5:
            print("Usage: md_to_gdoc.py write <doc_id> <prd_dir> <tab_mapping_json>")
            sys.exit(1)
        cmd_write(sys.argv[2], sys.argv[3], sys.argv[4])

    else:
        # Backwards compatibility: treat as write command
        if len(sys.argv) >= 4:
            cmd_write(sys.argv[1], sys.argv[2], sys.argv[3])
        else:
            print(__doc__)
            sys.exit(1)


if __name__ == "__main__":
    main()
