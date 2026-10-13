import os
import urllib.request
import urllib.parse
import json
import time
import html as htmlmod
from datetime import datetime, timezone

import shopify
from dotenv import load_dotenv

load_dotenv()

SHOP_URL = os.environ["SHOP_URL"]
CLIENT_ID = os.environ["SHOPIFY_CLIENT_ID"]
CLIENT_SECRET = os.environ["SHOPIFY_CLIENT_SECRET"]
API_VERSION = "2026-07"

token_url = f"https://{SHOP_URL}/admin/oauth/access_token"
data = urllib.parse.urlencode({
    "grant_type": "client_credentials",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
}).encode()
req = urllib.request.Request(token_url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
with urllib.request.urlopen(req) as response:
    ACCESS_TOKEN = json.loads(response.read())["access_token"]

session = shopify.Session(SHOP_URL, API_VERSION, ACCESS_TOKEN)
shopify.ShopifyResource.activate_session(session)

all_products = []
page = shopify.Product.find(limit=250)
all_products.extend(page)
while page.has_next_page():
    page = page.next_page()
    all_products.extend(page)

rows = []
for p in all_products:
    time.sleep(0.6)
    metafields = p.metafields()
    title_tag = next((m.value for m in metafields if m.key == "title_tag"), None)
    desc_tag = next((m.value for m in metafields if m.key == "description_tag"), None)
    missing_alt = sum(1 for img in p.images if not getattr(img, "alt", None))

    issues = []
    if not title_tag:
        issues.append("Missing meta title")
    elif len(title_tag) > 60:
        issues.append(f"Meta title too long ({len(title_tag)} chars)")
    if not desc_tag:
        issues.append("Missing meta description")
    elif len(desc_tag) > 160:
        issues.append(f"Meta description too long ({len(desc_tag)} chars)")
    if missing_alt:
        issues.append(f"{missing_alt} image{'s' if missing_alt > 1 else ''} missing alt text")

    rows.append({"title": p.title, "issues": issues})

shopify.ShopifyResource.clear_session()

flagged = [r for r in rows if r["issues"]]
clean = [r for r in rows if not r["issues"]]
flagged.sort(key=lambda r: -len(r["issues"]))
generated = datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC")


def esc(s):
    return htmlmod.escape(s, quote=True)


flagged_html = ""
for r in flagged:
    chips = "".join(f'<li class="issue">{esc(i)}</li>' for i in r["issues"])
    flagged_html += f"""
    <li class="row">
      <div class="row-main">
        <span class="dot warn" aria-hidden="true"></span>
        <span class="row-title">{esc(r['title'])}</span>
      </div>
      <ul class="issue-list">{chips}</ul>
    </li>"""

clean_html = "".join(f'<li>{esc(r["title"])}</li>' for r in clean)

html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Claudette SEO Audit</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400..600&family=Work+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@500&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg: #eef1ed; --surface: #f8faf7; --surface-raised: #ffffff; --border: #d7ddd3;
    --ink: #1b2420; --ink-soft: #52604f; --accent: #1f6f63; --accent-soft: #e2eeea;
    --ok: #3f7d4f; --ok-soft: #e5f0e3; --warn: #a4631f; --warn-soft: #faeee0;
    --mono: "IBM Plex Mono", ui-monospace, monospace;
    --display: "Fraunces", Georgia, serif;
    --body-font: "Work Sans", -apple-system, system-ui, sans-serif;
  }}
  @media (prefers-color-scheme: dark) {{
    :root:not([data-theme="light"]) {{
      --bg: #11160f; --surface: #171e16; --surface-raised: #1d251c; --border: #2b342a;
      --ink: #eceee8; --ink-soft: #a9b3a4; --accent: #6fcdb8; --accent-soft: #1d2f2b;
      --ok: #7cc98c; --ok-soft: #1d2a1f; --warn: #e3a35c; --warn-soft: #302417;
    }}
  }}
  :root[data-theme="dark"] {{
    --bg: #11160f; --surface: #171e16; --surface-raised: #1d251c; --border: #2b342a;
    --ink: #eceee8; --ink-soft: #a9b3a4; --accent: #6fcdb8; --accent-soft: #1d2f2b;
    --ok: #7cc98c; --ok-soft: #1d2a1f; --warn: #e3a35c; --warn-soft: #302417;
  }}
  * {{ box-sizing: border-box; }}
  html, body {{ margin: 0; padding: 0; }}
  body {{
    background: var(--bg); color: var(--ink); font-family: var(--body-font);
    font-size: 15px; line-height: 1.5; padding: clamp(20px, 5vw, 56px); min-height: 100vh;
  }}
  @media (prefers-reduced-motion: no-preference) {{ .row {{ transition: background-color 120ms ease; }} }}
  .wrap {{ max-width: 860px; margin: 0 auto; }}
  header {{
    display: flex; align-items: baseline; justify-content: space-between; gap: 16px;
    flex-wrap: wrap; margin-bottom: 28px; padding-bottom: 20px; border-bottom: 1px solid var(--border);
  }}
  .brand {{ font-family: var(--display); font-weight: 600; font-size: 28px; letter-spacing: -0.01em; text-wrap: balance; }}
  .brand span {{ color: var(--accent); }}
  .meta {{ font-size: 13px; color: var(--ink-soft); text-align: right; }}
  .meta .shop {{ font-weight: 500; color: var(--ink); }}
  .stats {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 36px; }}
  .stat {{ background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 16px 18px; }}
  .stat .num {{ font-family: var(--mono); font-variant-numeric: tabular-nums; font-size: 30px; font-weight: 500; line-height: 1; }}
  .stat.ok .num {{ color: var(--ok); }}
  .stat.warn .num {{ color: var(--warn); }}
  .stat .label {{ margin-top: 6px; font-size: 12px; color: var(--ink-soft); text-transform: uppercase; letter-spacing: 0.04em; }}
  section {{ margin-bottom: 32px; }}
  h2 {{ font-family: var(--body-font); font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: var(--ink-soft); margin: 0 0 12px; }}
  ul.rows {{ list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 8px; }}
  .row {{ background: var(--surface-raised); border: 1px solid var(--border); border-radius: 10px; padding: 14px 16px; }}
  .row-main {{ display: flex; align-items: center; gap: 10px; }}
  .dot {{ width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }}
  .dot.warn {{ background: var(--warn); }}
  .row-title {{ font-weight: 500; }}
  .issue-list {{ list-style: none; margin: 8px 0 0 18px; padding: 0; display: flex; flex-direction: column; gap: 4px; }}
  .issue {{ font-size: 13px; color: var(--warn); background: var(--warn-soft); display: inline-block; padding: 2px 8px; border-radius: 6px; width: fit-content; }}
  details {{ background: var(--surface); border: 1px solid var(--border); border-radius: 10px; overflow: hidden; }}
  summary {{ padding: 14px 16px; cursor: pointer; font-weight: 500; display: flex; align-items: center; gap: 10px; list-style: none; }}
  summary::-webkit-details-marker {{ display: none; }}
  summary .dot {{ background: var(--ok); }}
  summary:focus-visible, .row:focus-visible {{ outline: 2px solid var(--accent); outline-offset: 2px; }}
  .clean-list {{ margin: 0; padding: 4px 16px 16px 44px; columns: 2; column-gap: 24px; font-size: 13.5px; color: var(--ink-soft); }}
  .clean-list li {{ margin-bottom: 4px; }}
  footer {{ margin-top: 40px; padding-top: 16px; border-top: 1px solid var(--border); font-size: 12px; color: var(--ink-soft); }}
  footer code {{ font-family: var(--mono); background: var(--surface); padding: 2px 6px; border-radius: 4px; }}
  @media (max-width: 520px) {{ .stats {{ grid-template-columns: 1fr; }} .clean-list {{ columns: 1; }} .meta {{ text-align: left; }} }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="brand">Claudette <span>SEO AIO</span></div>
    <div class="meta">
      <div class="shop">{esc(SHOP_URL)}</div>
      <div>Audited {esc(generated)}</div>
    </div>
  </header>

  <div class="stats">
    <div class="stat"><div class="num">{len(rows)}</div><div class="label">Products audited</div></div>
    <div class="stat ok"><div class="num">{len(clean)}</div><div class="label">SEO-clean</div></div>
    <div class="stat warn"><div class="num">{len(flagged)}</div><div class="label">Need fixes</div></div>
  </div>

  <section>
    <h2>Needs attention ({len(flagged)})</h2>
    <ul class="rows">
      {flagged_html if flagged_html else '<li class="row">No issues found — every product is fully optimized.</li>'}
    </ul>
  </section>

  <section>
    <details>
      <summary><span class="dot" aria-hidden="true"></span> Clean catalog ({len(clean)} products, no action needed)</summary>
      <ul class="clean-list">
        {clean_html}
      </ul>
    </details>
  </section>

  <footer>
    Connected live to the Shopify Admin API via <code>{esc(SHOP_URL)}</code>. Checks meta titles, meta descriptions, and image alt text on every product.
  </footer>
</div>
</body>
</html>
"""

out_path = os.path.join(os.path.dirname(__file__), "..", "docs", "index.html")
with open(out_path, "w") as f:
    f.write(html)

print(f"Audited {len(rows)} products, {len(clean)} clean, {len(flagged)} flagged")
