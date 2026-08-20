import os
import urllib.request
import urllib.parse
import json
import shopify
from dotenv import load_dotenv

load_dotenv()

SHOP_URL = os.getenv("SHOP_URL")
CLIENT_ID = os.getenv("SHOPIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SHOPIFY_CLIENT_SECRET")
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

products = shopify.Product.find(limit=5)
print(f"Connected. Found {len(products)} products (showing first 5):\n")
for p in products:
    print(f"- {p.title}")

shopify.ShopifyResource.clear_session()
