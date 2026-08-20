# Claudette SEO

An AI-powered SEO/GEO audit and content-generation agent for Ibiza Beauty Store's Shopify catalog. Built with Claude (Anthropic API) and the Shopify Admin API.

## What she does

Claudette scans product listings for common SEO gaps — oversized meta titles/descriptions, missing or placeholder image alt text — and generates AI-written replacements for human review. Nothing is pushed live automatically; all output lands in a CSV for approval before it touches the live store.

## Structure

```
shopify-seo-agent/
├── test_connection.py      # Verifies Shopify API auth is working
├── count_products.py       # Quick product count for the store
├── seo_audit.py            # Rule-based audit: flags issues, no AI, no cost
├── seo_fix_generator.py    # Full pipeline: audits + generates AI replacements
├── .env                    # Secrets (never committed — see below)
└── .gitignore              # Excludes .env and generated CSVs
```

## How it works

1. **Auth**: exchanges the app's Client ID + Secret for a short-lived Admin API access token via Shopify's client credentials grant (required for Dev Dashboard apps created after Jan 2026).
2. **Audit** (`seo_audit.py`): pulls product data, flags meta titles >60 chars, meta descriptions >160 chars, and missing/placeholder (<10 char) alt text. Prints a plain report, no AI calls.
3. **Generate** (`seo_fix_generator.py`): for every product, sends product info to Claude for a properly-sized meta title + description, and sends each flagged image to Claude (vision) for descriptive alt text. Always includes "Nu Skin" in titles for brand-search matching. Output: `seo_suggestions_full.csv`, written incrementally so a Ctrl+C mid-run doesn't lose progress.

## Setup

Requires Python 3, and a `.env` file (not committed — copy the format below):

```
SHOPIFY_CLIENT_ID=your-client-id
SHOPIFY_CLIENT_SECRET=your-client-secret
SHOP_URL=ibizabeautystore.myshopify.com
```

Also requires `ANTHROPIC_API_KEY` set as an environment variable.

```
pip3 install ShopifyAPI anthropic python-dotenv --break-system-packages
```

## Usage

```
python3 test_connection.py       # confirm auth works
python3 seo_audit.py             # free, rule-based audit report
python3 seo_fix_generator.py     # full AI-generated suggestions -> CSV
```

## Status

- ✅ Single-region (UK), English-only version working end to end
- ✅ Tested on full 112-product catalog (546 suggestions generated)
- ⏳ Not yet built: pushing approved suggestions back to Shopify
- ⏳ v2 planned: Shopify Markets integration (real per-product region availability) + Translations API (multi-language meta content)
- ⏳ Schema.org structured data generation (separate from meta tags — lives in theme, not product data)

## Security notes

- Client Secret and Access Tokens should be rotated periodically via the Dev Dashboard — never commit them
- `.env` and all `*.csv` files are gitignored by design
