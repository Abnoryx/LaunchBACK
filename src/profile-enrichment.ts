import { PlaywrightCrawler, Request, log } from 'crawlee';
import type { Page } from 'playwright';
import type { ProxyConfiguration } from 'apify';
import { ActorInput, EnrichmentResult, Platform } from './types.js';
import { parseFollowerCount, extractEmail, normalizeUrl } from './utils.js';
import { saveCreator, savedCount } from './output.js';

export interface ProfileCrawlerOptions {
  proxyConfiguration: ProxyConfiguration | undefined;
  input: ActorInput;
  onWebsiteFound: (username: string, platform: Platform, websiteUrl: string) => Promise<void>;
}

// ─── Instagram ────────────────────────────────────────────────────────────────

async function fetchInstagramViaApi(username: string, page: Page): Promise<EnrichmentResult | null> {
  try {
    const data = await page.evaluate(async (uname: string) => {
      const res = await fetch(
        `https://i.instagram.com/api/v1/users/web_profile_info/?username=${uname}`,
        {
          headers: {
            'x-ig-app-id': '936619743392459',
            Accept: 'application/json',
          },
        },
      );
      if (!res.ok) return null;
      return res.json();
    }, username);

    const user = (data as Record<string, unknown> | null)?.['data'] as Record<string, unknown> | null;
    if (!user?.['user']) return null;
    const u = user['user'] as Record<string, unknown>;

    if (u['is_private']) return null;

    const followerEdge = u['edge_followed_by'] as Record<string, unknown> | undefined;

    return {
      name: (u['full_name'] as string) || username,
      username: (u['username'] as string) || username,
      bio: (u['biography'] as string) || '',
      followerCount: typeof followerEdge?.['count'] === 'number' ? (followerEdge['count'] as number) : null,
      country: '',
      email: extractEmail((u['biography'] as string) || ''),
      websiteUrl: normalizeUrl((u['external_url'] as string) || ''),
    };
  } catch {
    return null;
  }
}

async function parseInstagramMeta(page: Page, username: string): Promise<EnrichmentResult | null> {
  try {
    const description = await page.$eval(
      'meta[name="description"]',
      (el) => el.getAttribute('content') ?? '',
    ).catch(() => '');

    if (!description) return null;

    // "X Followers, Y Following, Z Posts - See Instagram photos..."
    const followerMatch = description.match(/([\d.,]+[KMBkmb]?)\s*Followers/i);
    const followerCount = followerMatch ? parseFollowerCount(followerMatch[1]) : null;

    const nameEl = await page.$eval('title', (el) => el.textContent ?? '').catch(() => '');
    const name = nameEl.replace(/\s*•.*$/, '').replace(/\s*\(@.*$/, '').trim() || username;

    return {
      name,
      username,
      bio: description,
      followerCount,
      country: '',
      email: extractEmail(description),
      websiteUrl: '',
    };
  } catch {
    return null;
  }
}

async function handleInstagramProfile(
  page: Page,
  url: string,
  username: string,
  keyword: string,
  input: ActorInput,
  onWebsiteFound: ProfileCrawlerOptions['onWebsiteFound'],
): Promise<void> {
  // Detect login wall
  if (page.url().includes('accounts/login')) {
    log.warning(`Instagram login wall for @${username} — trying API`);
  }

  let result = await fetchInstagramViaApi(username, page);

  if (!result) {
    result = await parseInstagramMeta(page, username);
  }

  if (!result || result.followerCount === null) {
    log.warning(`Could not extract follower count for Instagram @${username} — skipping`);
    return;
  }

  const saved = await saveCreator(
    { name: result.name, username: result.username, platform: 'instagram', profileUrl: url,
      bio: result.bio, followerCount: result.followerCount, country: result.country,
      email: result.email, keyword },
    input,
  );

  if (saved && result.websiteUrl) {
    await onWebsiteFound(result.username, 'instagram', result.websiteUrl);
  }
}

// ─── YouTube ──────────────────────────────────────────────────────────────────

function parseYtSubscriberText(text: string): number | null {
  if (!text) return null;
  const match = text.match(/([\d.,]+[KMBkmb]?)\s*subscriber/i);
  return match ? parseFollowerCount(match[1]) : null;
}

function parseYtInitialData(data: Record<string, unknown>, fallbackUsername: string): EnrichmentResult | null {
  try {
    const meta = (data['metadata'] as Record<string, unknown>)?.['channelMetadataRenderer'] as Record<string, unknown>;
    const name = (meta?.['title'] as string) || fallbackUsername;
    const bio = (meta?.['description'] as string) || '';
    const website = normalizeUrl((meta?.['doNotContactUrl'] as string) || '');

    // Modern header path
    let subscriberText = '';
    const header = data['header'] as Record<string, unknown> | undefined;
    const metaParts = (
      (header?.['pageHeaderRenderer'] as Record<string, unknown>)
        ?.['content'] as Record<string, unknown>
    )?.['pageHeaderViewModel'] as Record<string, unknown>;
    const parts = (
      (metaParts?.['metadata'] as Record<string, unknown>)
        ?.['contentMetadataViewModel'] as Record<string, unknown>
    )?.['metadataParts'];

    if (Array.isArray(parts)) {
      for (const part of parts as Record<string, unknown>[]) {
        const text =
          ((part['text'] as Record<string, unknown>)?.['content'] as string) ||
          (((part['text'] as Record<string, unknown>)?.['runs'] as Record<string, unknown>[])?.[0]?.['text'] as string) ||
          '';
        if (/subscriber/i.test(text)) {
          subscriberText = text;
          break;
        }
      }
    }

    // Legacy header path
    if (!subscriberText) {
      const legacy = header?.['c4TabbedHeaderRenderer'] as Record<string, unknown> | undefined;
      subscriberText =
        ((legacy?.['subscriberCountText'] as Record<string, unknown>)?.['simpleText'] as string) ||
        (((legacy?.['subscriberCountText'] as Record<string, unknown>)?.['runs'] as Record<string, unknown>[])?.[0]?.['text'] as string) ||
        '';
    }

    const followerCount = parseYtSubscriberText(subscriberText);

    // Email from about links
    let email = extractEmail(bio);
    if (!email) {
      const aboutLinks = (
        (header?.['pageHeaderRenderer'] as Record<string, unknown>)
          ?.['content'] as Record<string, unknown>
      )?.['links'] as Record<string, unknown> | undefined;
      const linkItems = (
        (aboutLinks?.['channelHeaderLinksViewModel'] as Record<string, unknown>)
          ?.['secondaryLink'] as Record<string, unknown>
      )?.['content'];
      if (Array.isArray(linkItems)) {
        for (const item of linkItems as Record<string, unknown>[]) {
          const href = (
            ((item?.['commandRuns'] as Record<string, unknown>[])?.[0]
              ?.['onTap'] as Record<string, unknown>)
              ?.['innertubeCommand'] as Record<string, unknown>
          )?.['urlEndpoint'] as Record<string, unknown> | undefined;
          const hrefUrl = href?.['url'] as string;
          if (hrefUrl?.startsWith('mailto:')) {
            email = hrefUrl.replace('mailto:', '');
            break;
          }
        }
      }
    }

    return { name, username: fallbackUsername, bio, followerCount, country: '', email, websiteUrl: website };
  } catch {
    return null;
  }
}

async function parseYoutubeOpenGraph(page: Page, fallbackUsername: string): Promise<EnrichmentResult | null> {
  try {
    const description = await page.$eval(
      'meta[property="og:description"], meta[name="description"]',
      (el) => el.getAttribute('content') ?? '',
    ).catch(() => '');

    const title = await page.$eval('title', (el) => el.textContent ?? '').catch(() => '');
    const name = title.replace(/\s*-\s*YouTube\s*$/, '').trim() || fallbackUsername;
    const followerCount = parseYtSubscriberText(description);

    return {
      name,
      username: fallbackUsername,
      bio: description,
      followerCount,
      country: '',
      email: extractEmail(description),
      websiteUrl: '',
    };
  } catch {
    return null;
  }
}

async function handleYoutubeProfile(
  page: Page,
  url: string,
  username: string,
  keyword: string,
  input: ActorInput,
  onWebsiteFound: ProfileCrawlerOptions['onWebsiteFound'],
): Promise<void> {
  await page.waitForLoadState('domcontentloaded');
  await page.waitForSelector('ytd-channel-name, #channel-name, yt-formatted-string', { timeout: 10000 }).catch(() => {});

  let result: EnrichmentResult | null = null;

  const ytData = await page.evaluate(() => (window as unknown as Record<string, unknown>)['ytInitialData'] ?? null).catch(() => null);

  if (ytData) {
    result = parseYtInitialData(ytData as Record<string, unknown>, username);
  }

  if (!result) {
    result = await parseYoutubeOpenGraph(page, username);
  }

  if (!result || result.followerCount === null) {
    log.warning(`Could not extract subscriber count for YouTube @${username} — skipping`);
    return;
  }

  const saved = await saveCreator(
    { name: result.name, username: result.username, platform: 'youtube', profileUrl: url,
      bio: result.bio, followerCount: result.followerCount, country: result.country,
      email: result.email, keyword },
    input,
  );

  if (saved && result.websiteUrl) {
    await onWebsiteFound(result.username, 'youtube', result.websiteUrl);
  }
}

// ─── Crawler factory ──────────────────────────────────────────────────────────

export function createProfileCrawler(opts: ProfileCrawlerOptions): PlaywrightCrawler {
  const { proxyConfiguration, input, onWebsiteFound } = opts;

  return new PlaywrightCrawler({
    proxyConfiguration,
    maxRequestRetries: 3,
    maxSessionRotations: 5,
    requestHandlerTimeoutSecs: 60,
    retryOnBlocked: true,
    useSessionPool: true,
    persistCookiesPerSession: true,
    maxConcurrency: 5,
    sameDomainDelaySecs: 3,

    launchContext: {
      launchOptions: {
        headless: true,
        args: [
          '--no-sandbox',
          '--disable-setuid-sandbox',
          '--disable-blink-features=AutomationControlled',
        ],
      },
    },

    preNavigationHooks: [
      async ({ page }) => {
        await page.setExtraHTTPHeaders({
          'Accept-Language': 'en-US,en;q=0.9',
          Accept: 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        });
        await page.route('**/*.{png,jpg,jpeg,gif,svg,webp,woff,woff2,ttf,eot,ico}', (r) => r.abort()).catch(() => {});
      },
    ],

    requestHandler: async ({ page, request }) => {
      if (savedCount() >= input.maxResults) return;

      const { label, username, keyword } = request.userData as { label: string; username: string; keyword: string };
      const url = request.url;

      if (label === 'INSTAGRAM_PROFILE') {
        await handleInstagramProfile(page, url, username, keyword, input, onWebsiteFound);
      } else if (label === 'YOUTUBE_PROFILE') {
        await handleYoutubeProfile(page, url, username, keyword, input, onWebsiteFound);
      }
    },

    failedRequestHandler: async ({ request, error }) => {
      log.warning(`Profile enrichment failed for ${request.url}: ${(error as Error).message}`);
    },
  });
}

export function makeProfileRequest(
  profileUrl: string,
  username: string,
  keyword: string,
  platform: Platform,
): Request {
  const label = platform === 'instagram' ? 'INSTAGRAM_PROFILE' : 'YOUTUBE_PROFILE';
  return new Request({
    url: profileUrl,
    label,
    userData: { label, profileUrl, username, keyword },
  });
}
