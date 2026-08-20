import os
import urllib.request
import urllib.parse
import json
import csv
import shopify
import anthropic
from dotenv import load_dotenv

load_dotenv()

SHOP_URL = os.getenv("SHOP_URL")
CLIENT_ID = os.getenv("SHOPIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SHOPIFY_CLIENT_SECRET")
API_VERSION = "2026-07"

client = anthropic.Anthropic()

token_url = f"https://{SHOP_URL}/admin/oauth/access_token"
data = urllib.parse.urlencode({
    "grant_type": "client_credentials",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET
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

print(f"Found {len(all_products)} total products.\n")

rows = []
MIN_ALT_LENGTH = 10

for idx, p in enumerate(all_products, 1):
    print(f"[{idx}/{len(all_products)}] Processing: {p.title}")
    try:
        metafields = p.metafields()
        old_title_tag = next((m.value for m in metafields if m.key == "title_tag"), "")
        old_desc_tag = next((m.value for m in metafields if m.key == "description_tag"), "")

        meta_prompt = f"""Product: {p.title}
Description: {p.body_html or ''}

Write an SEO meta title (max 60 characters, always include "Nu Skin" for brand search matching) and meta description (max 160 characters) for this product. Return ONLY valid JSON: {{"meta_title": "...", "meta_description": "..."}}"""

        msg = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=300,
            messages=[{"role": "user", "content": meta_prompt}]
        )
        try:
            meta_result = json.loads(msg.content[0].text)
        except json.JSONDecodeError:
            meta_result = {"meta_title": "PARSE_ERROR", "meta_description": "PARSE_ERROR"}

        rows.append({"product": p.title, "field": "meta_title", "old_value": old_title_tag, "new_value": meta_result.get("meta_title", "")})
        rows.append({"product": p.title, "field": "meta_description", "old_value": old_desc_tag, "new_value": meta_result.get("meta_description", "")})

        for img in p.images:
            current_alt = getattr(img, "alt", None) or ""
            needs_alt = len(current_alt.strip()) < MIN_ALT_LENGTH

            if needs_alt:
                alt_msg = client.messages.create(
                    model="claude-sonnet-5",
                    max_tokens=100,
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "image", "source": {"type": "url", "url": img.src}},
                            {"type": "text", "text": f"Write concise, descriptive alt text (under 125 characters) for this image of '{p.title}'. Return ONLY the alt text, nothing else."}
                        ]
                    }]
                )
                reason = "missing" if not current_alt.strip() else "too short/placeholder"
                rows.append({
                    "product": p.title,
                    "field": f"alt_text (image {img.id}) [{reason}]",
                    "old_value": current_alt,
                    "new_value": alt_msg.content[0].text.strip()
                })

        with open("seo_suggestions_full.csv", "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["product", "field", "old_value", "new_value"])
            writer.writeheader()
            writer.writerows(rows)

    except Exception as e:
        print(f"  Error on {p.title}: {e}")
        continue

shopify.ShopifyResource.clear_session()
print(f"\nDone. {len(rows)} suggestions written to seo_suggestions_full.csv")
