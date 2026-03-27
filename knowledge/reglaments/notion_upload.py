#!/usr/bin/env python3
"""Upload 3 AI regulation pages to Notion with attestation links."""

import os, json, re, textwrap
import urllib.request, urllib.error

NOTION_KEY = os.environ.get("NOTION_API_KEY", "")
PARENT_ID  = "3096fc6c-b62a-811b-8b5a-ef08d4c1a310"
NOTION_VER = "2025-09-03"
BASE_URL   = "https://api.notion.com/v1"

REGLAMENTS = [
    {
        "file":  "/home/axis/openclaw/knowledge/reglaments/ai-agents-guide.md",
        "title": "Руководство для команды: pi-api и pi-web",
        "form":  "https://docs.google.com/forms/d/e/1FAIpQLSeOCKkyXqqirTOasfm0mripwGQqYOQwmEwg35H67QforHT_Mg/viewform",
    },
    {
        "file":  "/home/axis/openclaw/knowledge/reglaments/ai-provider-switching.md",
        "title": "Регламент: Переключение провайдеров AI",
        "form":  "https://docs.google.com/forms/d/e/1FAIpQLSf9iqiD_RlDELZ_xbavye4qHpFIWdGkD-YZTkQM6a0NH0ihhQ/viewform",
    },
    {
        "file":  "/home/axis/openclaw/knowledge/reglaments/trello-api-for-agents.md",
        "title": "TRELLO API для агентов",
        "form":  "https://docs.google.com/forms/d/e/1FAIpQLSePKxyLDt8to-cvcUY29xbrFvilE-eKJAFz8-XCZtBGrTJP5A/viewform",
    },
]


def api(method, path, body=None):
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {NOTION_KEY}",
        "Notion-Version": NOTION_VER,
        "Content-Type":   "application/json",
    })
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        msg = e.read().decode()
        print(f"  ❌ HTTP {e.code}: {msg[:300]}")
        return None


def rich(text, bold=False, url=None):
    t = {"type": "text", "text": {"content": text}}
    if url:
        t["text"]["link"] = {"url": url}
    if bold:
        t["annotations"] = {"bold": True}
    return t


def md_to_blocks(md_text):
    """Convert markdown lines to Notion blocks (simplified)."""
    blocks = []
    lines = md_text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]

        # Skip attestation section (we'll add our own)
        if line.strip().startswith("## 📝 Аттестация"):
            while i < len(lines):
                i += 1
                if i < len(lines) and lines[i].startswith("## ") and "Аттестация" not in lines[i]:
                    break
            continue

        # H1 (# Title) - skip if it's the page title
        if re.match(r'^# ', line) and not blocks:
            i += 1
            continue

        # H2
        if re.match(r'^## ', line):
            text = line[3:].strip()
            blocks.append({"object":"block","type":"heading_2","heading_2":{"rich_text":[rich(text)]}})

        # H3
        elif re.match(r'^### ', line):
            text = line[4:].strip()
            blocks.append({"object":"block","type":"heading_3","heading_3":{"rich_text":[rich(text)]}})

        # Horizontal rule
        elif re.match(r'^---+$', line.strip()):
            blocks.append({"object":"block","type":"divider","divider":{}})

        # Code block
        elif line.startswith("```"):
            code_lines = []
            lang = line[3:].strip() or "plain text"
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code_lines.append(lines[i])
                i += 1
            code = "\n".join(code_lines)
            blocks.append({
                "object":"block","type":"code",
                "code":{"rich_text":[rich(code)],"language":lang if lang in ["bash","python","javascript","json","plain text"] else "plain text"}
            })

        # Bullet
        elif re.match(r'^[-*] ', line):
            text = line[2:].strip()
            # strip markdown bold **...**
            text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
            blocks.append({"object":"block","type":"bulleted_list_item","bulleted_list_item":{"rich_text":[rich(text)]}})

        # Numbered
        elif re.match(r'^\d+\. ', line):
            text = re.sub(r'^\d+\. ', '', line).strip()
            text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
            blocks.append({"object":"block","type":"numbered_list_item","numbered_list_item":{"rich_text":[rich(text)]}})

        # Table (skip — Notion API tables are complex)
        elif line.startswith("|"):
            pass

        # Regular paragraph (non-empty)
        elif line.strip():
            text = line.strip()
            text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
            text = re.sub(r'`(.*?)`', r'\1', text)
            if len(text) > 1:
                blocks.append({"object":"block","type":"paragraph","paragraph":{"rich_text":[rich(text)]}})

        i += 1

    return blocks


def attestation_blocks(form_url):
    return [
        {"object":"block","type":"divider","divider":{}},
        {
            "object":"block","type":"callout",
            "callout":{
                "icon":{"type":"emoji","emoji":"📝"},
                "rich_text":[rich("Аттестация", bold=True)],
                "color":"blue_background"
            }
        },
        {
            "object":"block","type":"paragraph",
            "paragraph":{"rich_text":[rich("Прочитал регламент? Пройди короткую проверку знаний:")]}
        },
        {
            "object":"block","type":"paragraph",
            "paragraph":{"rich_text":[
                rich("🔗 "),
                rich("Пройти аттестацию", url=form_url)
            ]}
        },
    ]


def create_page(title):
    body = {
        "parent": {"page_id": PARENT_ID},
        "properties": {
            "title": {"title": [{"text": {"content": title}}]}
        }
    }
    result = api("POST", "/pages", body)
    if result:
        return result["id"]
    return None


def add_blocks(page_id, blocks):
    # Notion allows max 100 children per request
    chunk_size = 50
    for i in range(0, len(blocks), chunk_size):
        chunk = blocks[i:i+chunk_size]
        result = api("PATCH", f"/blocks/{page_id}/children", {"children": chunk})
        if not result:
            print(f"  ⚠️ Failed to add blocks chunk {i//chunk_size+1}")


def main():
    print(f"Using NOTION_KEY: {NOTION_KEY[:20]}...")
    print(f"Parent page: {PARENT_ID}\n")

    results = []

    for reg in REGLAMENTS:
        print(f"📄 Processing: {reg['title']}")

        # Read .md file
        try:
            with open(reg["file"], "r", encoding="utf-8") as f:
                md_content = f.read()
        except FileNotFoundError:
            print(f"  ❌ File not found: {reg['file']}")
            continue

        # Create page
        print(f"  → Creating page...")
        page_id = create_page(reg["title"])
        if not page_id:
            print(f"  ❌ Failed to create page")
            continue
        print(f"  ✅ Page created: {page_id}")

        # Convert md to blocks
        blocks = md_to_blocks(md_content)
        print(f"  → Adding {len(blocks)} content blocks...")
        add_blocks(page_id, blocks)

        # Add attestation
        att_blocks = attestation_blocks(reg["form"])
        print(f"  → Adding attestation block...")
        add_blocks(page_id, att_blocks)

        url = f"https://notion.so/{page_id.replace('-','')}"
        print(f"  ✅ Done! URL: {url}")
        results.append({"title": reg["title"], "page_id": page_id, "url": url, "form": reg["form"]})
        print()

    print("\n" + "="*60)
    print("ИТОГ:")
    for r in results:
        print(f"  • {r['title']}")
        print(f"    Notion: {r['url']}")
        print(f"    Form:   {r['form']}")


if __name__ == "__main__":
    main()
