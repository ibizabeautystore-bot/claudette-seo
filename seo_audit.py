import urllib.request
import urllib.parse
import json
import shopify

SHOP_URL = "ibizabeautystore.myshopify.com"
CLIENT_ID = "08031bb7d24cf43edce8da86b8a41e34"
CLIENT_SECRET = "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"
API_VERSION = "2026-07"

token_url = f"https://{SHOP_URL}/admin/oauth/access_token"
data = urllib.parse.urlencode({
    "grant_type": "client_credentials",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET
}).encode()

req = urllib.request.Request(token_url, data=data, headers={
    "Content-Type": "application/x-www-form-urlencoded"
})

with urllib.request.urlopen(req) as response:
    result = json.loads(response.read())
    ACCESS_TOKEN = result["access_token"]

session = shopify.Session(SHOP_URL, API_VERSION, ACCESS_TOKEN)
shopify.ShopifyResource.activate_session(session)

products = shopify.Product.find(limit=20)

print(f"Auditing {len(products)} products...\n")
print("=" * 60)

for p in products:
    issues = []

    # Check meta title / description (stored as metafields)
    metafields = p.metafields()
    title_tag = next((m.value for m in metafields if m.key == "title_tag"), None)
    desc_tag = next((m.value for m in metafields if m.key == "description_tag"), None)

    if not title_tag:
        issues.append("Missing meta title")
    elif len(title_tag) > 60:
        issues.append(f"Meta title too long ({len(title_tag)} chars)")

    if not desc_tag:
        issues.append("Missing meta description")
    elif len(desc_tag) > 160:
        issues.append(f"Meta description too long ({len(desc_tag)} chars)")

    # Check image alt text
    missing_alt = sum(1 for img in p.images if not getattr(img, "alt", None))
    if missing_alt > 0:
        issues.append(f"{missing_alt} image(s) missing alt text")

    print(f"\n{p.title}")
    if issues:
        for i in issues:
            print(f"  ⚠ {i}")
    else:
        print("  ✓ No issues found")

shopify.ShopifyResource.clear_session()
print("\n" + "=" * 60)
print("Audit complete.")
