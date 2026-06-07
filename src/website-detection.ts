import { PlaywrightCrawler, Request, log } from 'crawlee';
import type { ProxyConfiguration } from 'apify';
import { Platform } from './types.js';
import { updateCreatorWebsite } from './output.js';

// ─── Classification tables ────────────────────────────────────────────────────

const WEBSITE_TYPE_PATTERNS: [RegExp, string][] = [
  [/linktr\.ee/i, 'Linktree'],
  [/beacons\.ai/i, 'Beacons'],
  [/stan\.store/i, 'Stan Store'],
  [/kajabi\.com/i, 'Kajabi'],
  [/skool\.com/i, 'Skool'],
  [/beehiiv\.com/i, 'Beehiiv'],
  [/substack\.com/i, 'Substack'],
  [/gumroad\.com/i, 'Gumroad'],
  [/myshopify\.com/i, 'Shopify'],
];

const PRODUCT_KEYWORDS = [
  'course', 'coaching', 'membership', 'community', 'program',
  'academy', 'workshop', 'kajabi', 'stan', 'skool',
  'gumroad', 'teachable', 'thinkific',
];

const PRODUCT_PLATFORM_PATTERNS: [RegExp, string][] = [
  [/kajabi\.com/i, 'Kajabi'],
  [/skool\.com/i, 'Skool'],
  [/stan\.store/i, 'Stan'],
  [/gumroad\.com/i, 'Gumroad'],
  [/myshopify\.com/i, 'Shopify'],
  [/beehiiv\.com/i, 'Beehiiv'],
  [/substack\.com/i, 'Substack'],
  [/circle\.so/i, 'Circle'],
  [/teachable\.com/i, 'Teachable'],
  [/thinkific\.com/i, 'Thinkific'],
];

// ─── Pure classification functions ───────────────────────────────────────────

export function detectWebsiteType(url: string): string {
  if (!url) return '';
  for (const [pattern, type] of WEBSITE_TYPE_PATTERNS) {
    if (pattern.test(url)) return type;
  }
  return 'Personal Website';
}

export function detectHasProductLinks(outboundUrls: string[]): boolean {
  const combined = outboundUrls.join(' ').toLowerCase();
  return PRODUCT_KEYWORDS.some((kw) => combined.includes(kw));
}

export function detectProductPlatform(outboundUrls: string[]): string {
  for (const url of outboundUrls) {
    for (const [pattern, platform] of PRODUCT_PLATFORM_PATTERNS) {
      if (pattern.test(url)) return platform;
    }
  }
  return '';
}

// ─── Crawler factory ──────────────────────────────────────────────────────────

export interface WebsiteCrawlerOptions {
  proxyConfiguration: ProxyConfiguration | undefined;
}

export function createWebsiteCrawler(opts: WebsiteCrawlerOptions): PlaywrightCrawler {
  const { proxyConfiguration } = opts;

  return new PlaywrightCrawler({
    proxyConfiguration,
    maxRequestRetries: 2,
    requestHandlerTimeoutSecs: 30,
    retryOnBlocked: true,
    useSessionPool: true,
    maxConcurrency: 3,

    launchContext: {
      launchOptions: {
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox'],
      },
    },

    preNavigationHooks: [
      async ({ page }) => {
        await page.route(
          '**/*.{png,jpg,jpeg,gif,svg,webp,woff,woff2,ttf,eot,ico,mp4,mp3}',
          (r) => r.abort(),
        ).catch(() => {});
      },
    ],

    requestHandler: async ({ page, request }) => {
      const { username, platform, websiteUrl } = request.userData as {
        username: string;
        platform: Platform;
        websiteUrl: string;
      };

      await page.waitForLoadState('domcontentloaded');

      // Extract all outbound links visible after render
      const outboundUrls: string[] = await page.evaluate(() =>
        Array.from(document.querySelectorAll('a[href]'))
          .map((a) => (a as HTMLAnchorElement).href)
          .filter((href) => href.startsWith('http')),
      ).catch(() => []);

      // Also include the final URL after any redirects for classification
      const finalUrl = page.url();
      const classifyUrl = finalUrl || websiteUrl;

      const websiteType = detectWebsiteType(classifyUrl);
      const hasProductLinks = detectHasProductLinks([classifyUrl, ...outboundUrls]);
      const productPlatform = detectProductPlatform([classifyUrl, ...outboundUrls]);

      log.debug(`Website detection for @${username}: type=${websiteType}, hasProducts=${hasProductLinks}, platform=${productPlatform}`);

      await updateCreatorWebsite(username, platform, {
        websiteUrl,
        hasWebsite: true,
        websiteType,
        hasProductLinks,
        productPlatform,
      });
    },

    failedRequestHandler: async ({ request, error }) => {
      const { username, platform, websiteUrl } = request.userData as {
        username: string;
        platform: Platform;
        websiteUrl: string;
      };

      log.warning(`Website visit failed for @${username} (${websiteUrl}): ${(error as Error).message}`);

      // Still persist what we can classify from the URL alone
      await updateCreatorWebsite(username, platform, {
        websiteUrl,
        hasWebsite: true,
        websiteType: detectWebsiteType(websiteUrl),
        hasProductLinks: false,
        productPlatform: '',
      });
    },
  });
}

export function makeWebsiteRequest(
  username: string,
  platform: Platform,
  websiteUrl: string,
): Request {
  return new Request({
    url: websiteUrl,
    label: 'WEBSITE_DETECTION',
    userData: { label: 'WEBSITE_DETECTION', username, platform, websiteUrl },
  });
}
