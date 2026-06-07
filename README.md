# Creator Discovery Engine

An Apify Actor that finds Instagram or YouTube creators via Google Search based on a niche keyword, country, and follower range. Built for influencer sourcing and creator acquisition workflows.

## How It Works

The actor runs in three phases:

1. **Google Search** — Searches `site:instagram.com` or `site:youtube.com` for the given keyword and country. Collects profile URLs from SERP results.
2. **Profile Enrichment** — Visits each profile, extracts name, bio, follower count, email, and website URL.
3. **Website Detection** — Visits each creator's website, classifies the site type (Linktree, Kajabi, etc.), detects product links, and identifies the selling platform. No AI — pure URL pattern matching.

## Input

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `platform` | `instagram` \| `youtube` | Yes | `instagram` | Platform to search |
| `keyword` | string | Yes | — | Niche keyword (pre-processed upstream, e.g. "parenting coach") |
| `country` | string | No | `""` (worldwide) | Target country, e.g. "United States" |
| `minFollowers` | number | Yes | `10000` | Minimum follower count |
| `maxFollowers` | number | Yes | `1000000` | Maximum follower count |
| `maxResults` | number | Yes | `100` | Maximum creators to return (1–500) |

**Note:** The `keyword` is expected to be pre-processed by an upstream AI step. This actor does not transform keywords — it searches exactly as provided.

## Output

Each dataset record:

```json
{
  "name": "Jane Smith",
  "username": "janesmith",
  "platform": "instagram",
  "profileUrl": "https://www.instagram.com/janesmith",
  "bio": "Parenting coach helping moms thrive 🌱",
  "followerCount": 45000,
  "country": "",
  "email": "jane@example.com",
  "keyword": "parenting coach",
  "websiteUrl": "https://linktr.ee/janesmith",
  "hasWebsite": true,
  "websiteType": "Linktree",
  "hasProductLinks": true,
  "productPlatform": "Kajabi"
}
```

### Website Types

`websiteType` is classified from the URL pattern:

- `Linktree`, `Beacons`, `Stan Store`, `Kajabi`, `Skool`, `Beehiiv`, `Substack`, `Gumroad`, `Shopify`, `Personal Website`

### Product Platforms

`productPlatform` is detected from outbound links on the creator's website:

- `Kajabi`, `Skool`, `Stan`, `Gumroad`, `Shopify`, `Beehiiv`, `Substack`, `Circle`, `Teachable`, `Thinkific`

`hasProductLinks` is `true` if any outbound link contains product-related keywords: `course`, `coaching`, `membership`, `community`, `program`, `academy`, `workshop`, or a known product platform domain.

---

## Installation

```bash
# Requires Node.js 20+
npm install
```

## Local Development

```bash
# Run locally (no Apify account needed, no proxy)
npm run dev
```

Create a local input file at `storage/key_value_stores/default/INPUT.json`:

```json
{
  "platform": "instagram",
  "keyword": "parenting coach",
  "country": "United States",
  "minFollowers": 10000,
  "maxFollowers": 500000,
  "maxResults": 10
}
```

Results appear in `storage/datasets/default/`.

## Build

```bash
npm run build
# Compiled output is in dist/
```

## Deployment to Apify

### Prerequisites

```bash
npm install -g apify-cli
apify login
```

### Push and deploy

```bash
npm run build
apify push
```

The actor will be available in your Apify account. Run it from the Apify console or via the API.

### Required proxy groups

The actor uses Apify Proxy. Make sure your Apify plan includes:
- `GOOGLE_SERP` — for Google Search pages
- `RESIDENTIAL` — for Instagram/YouTube profile pages and website visits

On the **Starter** plan and above, both groups are available.

---

## Architecture

```
Phase 1 (CheerioCrawler)          Phase 2 (PlaywrightCrawler)       Phase 3 (PlaywrightCrawler)
─────────────────────────         ──────────────────────────         ──────────────────────────
Google SERP pages         ──▶     Instagram / YouTube profiles ──▶  Creator websites
  ↓ extract profile URLs            ↓ extract followers, bio           ↓ classify site type
  ↓ enqueue to profileQueue         ↓ extract website URL              ↓ detect product links
                                    ↓ enqueue to websiteQueue          ↓ update dataset record
```

## Project Structure

```
src/
  main.ts               Entry point, three-phase orchestration
  types.ts              TypeScript interfaces
  google-search.ts      Query builder, CheerioCrawler, SERP parser
  profile-enrichment.ts PlaywrightCrawler, Instagram + YouTube handlers
  website-detection.ts  Website type/product detection (no AI)
  filters.ts            URL validation, follower range filter
  output.ts             Dataset write with deduplication
  utils.ts              Shared utilities
.actor/
  actor.json            Apify Actor metadata
  input_schema.json     Input schema for Apify console UI
Dockerfile              Production container (Playwright + Chrome)
```
