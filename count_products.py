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
req = urllib.request.Request(token_url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
with urllib.request.urlopen(req) as response:
    ACCESS_TOKEN = json.loads(response.read())["access_token"]

session = shopify.Session(SHOP_URL, API_VERSION, ACCESS_TOKEN)
shopify.ShopifyResource.activate_session(session)

count = shopify.Product.count()
print(f"Total products: {count}")

shopify.ShopifyResource.clear_session()
