import { CheerioCrawler, Request, log } from 'crawlee';
import type { ProxyConfiguration } from 'apify';
import type { CheerioAPI } from 'cheerio';
import { ActorInput, Platform } from './types.js';
import { isValidProfileUrl, extractUsernameFromUrl } from './filters.js';
import { normalizeUrl, stripSurroundingQuotes } from './utils.js';
import { isAlreadySaved, savedCount } from './output.js';

export interface GoogleCrawlerOptions {
  proxyConfiguration: ProxyConfiguration | undefined;
  input: ActorInput;
  onProfileFound: (profileUrl: string, username: string) => Promise<void>;
}

export function buildGoogleQuery(input: ActorInput, variant = 0): string {
  const site = input.platform === 'instagram' ? 'site:instagram.com' : 'site:youtube.com';
  const keyword = stripSurroundingQuotes(input.keyword);
  let keywordPart: string;
  if (variant === 1) keywordPart = keyword;
  else if (variant === 2) keywordPart = `#${keyword.replace(/\s+/g, '')}`;
  else keywordPart = `"${keyword}"`;
  const parts = [site, keywordPart];
  if (input.country) parts.push(`"${input.country}"`);
  return parts.join(' ');
}

export function buildGoogleSearchRequests(input: ActorInput, startPage = 0, variant = 0): Request[] {
  const query = buildGoogleQuery(input, variant);
  const batchSize = Math.max(10, Math.ceil((input.maxResults * 3) / 10));
  const requests: Request[] = [];

  for (let page = startPage; page < startPage + batchSize; page++) {
    const url = `http://www.google.com/search?q=${encodeURIComponent(query)}&start=${page * 10}&num=10&hl=en&gl=us`;
    requests.push(
      new Request({
        url,
        label: 'GOOGLE_SEARCH',
        userData: { label: 'GOOGLE_SEARCH', page, query },
      }),
    );
  }

  return requests;
}

function extractProfileUrls($: CheerioAPI, platform: Platform): string[] {
  const found = new Set<string>();
  const domain = platform === 'instagram' ? 'instagram.com' : 'youtube.com';

  $('a[href]').each((_, el) => {
    const href = $(el).attr('href') ?? '';
    if (href.startsWith('http') && href.includes(domain)) {
      found.add(href);
    }
  });

  $('a[href*="/url?q="]').each((_, el) => {
    const href = $(el).attr('href') ?? '';
    const match = href.match(/\/url\?q=([^&]+)/);
    if (match) {
      const decoded = decodeURIComponent(match[1]);
      if (decoded.includes(domain)) found.add(decoded);
    }
  });

  return [...found].map((u) => normalizeUrl(u));
}

export function createGoogleCrawler(opts: GoogleCrawlerOptions): CheerioCrawler {
  const { proxyConfiguration, input, onProfileFound } = opts;

  return new CheerioCrawler({
    proxyConfiguration,
    maxRequestRetries: 5,
    maxSessionRotations: 20,
    requestHandlerTimeoutSecs: 30,
    retryOnBlocked: true,
    useSessionPool: true,
    persistCookiesPerSession: false,
    sameDomainDelaySecs: 2,
    maxConcurrency: 3,
    minConcurrency: 1,

    requestHandler: async ({ $, response, session, request }) => {
      const body = $('body').text();
      if (
        response.statusCode === 429 ||
        body.includes('unusual traffic') ||
        body.includes('detected unusual')
      ) {
        session?.retire();
        throw new Error('Google rate limit detected — retiring session and retrying');
      }

      if (savedCount() >= input.maxResults) {
        log.info(`Reached maxResults (${input.maxResults}), stopping Google crawl`);
        return;
      }

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const urls = extractProfileUrls($ as any, input.platform);
      log.debug(`Page ${(request.userData as { page: number }).page}: found ${urls.length} candidate URLs`);

      for (const url of urls) {
        if (savedCount() >= input.maxResults) break;
        if (!isValidProfileUrl(url, input.platform)) continue;

        const username = extractUsernameFromUrl(url, input.platform);
        if (!username) continue;
        if (isAlreadySaved(input.platform, username)) continue;

        await onProfileFound(url, username);
      }
    },

    failedRequestHandler: async ({ request, error }) => {
      log.error(`Google search failed after all retries: ${request.url} — ${(error as Error).message}`);
    },
  });
}
