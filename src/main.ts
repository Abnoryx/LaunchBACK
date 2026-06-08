import { Actor, log as apifyLog } from 'apify';
import { RequestQueue, log } from 'crawlee';
import { validateInput } from './utils.js';
import { buildGoogleSearchRequests, createGoogleCrawler } from './google-search.js';
import { createProfileCrawler, makeProfileRequest } from './profile-enrichment.js';
import { createWebsiteCrawler, makeWebsiteRequest } from './website-detection.js';
import { savedCount } from './output.js';
import type { Platform } from './types.js';

await Actor.init();

try {
  const rawInput = await Actor.getInput();
  const input = validateInput(rawInput);

  log.info(`Starting Creator Discovery Engine`, {
    platform: input.platform,
    keyword: input.keyword,
    country: input.country || 'worldwide',
    minFollowers: input.minFollowers,
    maxFollowers: input.maxFollowers,
    maxResults: input.maxResults,
  });

  // ── Proxy configuration ────────────────────────────────────────────────────

  const hasToken = Boolean(process.env['APIFY_TOKEN']);

  const googleProxyConfig = hasToken
    ? await Actor.createProxyConfiguration({ groups: ['GOOGLE_SERP'] })
    : undefined;

  const residentialProxyConfig = hasToken
    ? await Actor.createProxyConfiguration({ groups: ['RESIDENTIAL'] })
    : undefined;

  if (!hasToken) {
    log.warning('APIFY_TOKEN not set — running without proxy. For production use, set APIFY_TOKEN.');
  }

  // ── Shared queues ──────────────────────────────────────────────────────────

  const googleQueue = await RequestQueue.open('google-search');
  const profileQueue = await RequestQueue.open('profile-enrichment');
  const websiteQueue = await RequestQueue.open('website-detection');

  // ── Phase 1: Google Search ─────────────────────────────────────────────────

  log.info('Phase 1: Enqueuing Google Search pages...');

  const searchRequests = buildGoogleSearchRequests(input);
  for (const req of searchRequests) {
    await googleQueue.addRequest(req);
  }

  const googleCrawler = createGoogleCrawler({
    proxyConfiguration: googleProxyConfig,
    input,
    onProfileFound: async (profileUrl: string, username: string) => {
      const profileReq = makeProfileRequest(
        profileUrl,
        username,
        input.keyword,
        input.platform as Platform,
      );
      await profileQueue.addRequest(profileReq, { forefront: false });
      log.debug(`Queued profile: ${profileUrl}`);
    },
  });

  googleCrawler.requestQueue = googleQueue;
  await googleCrawler.run() 
log.info(`Phase 1 complete. Queued ${(await profileQueue.getInfo())?.totalRequestCount ?? 0} profiles.`);

  // ── Phase 2: Profile Enrichment ────────────────────────────────────────────

  log.info('Phase 2: Enriching creator profiles...');

  const profileCrawler = createProfileCrawler({
    proxyConfiguration: residentialProxyConfig,
    input,
    onWebsiteFound: async (username: string, platform: Platform, websiteUrl: string) => {
      const websiteReq = makeWebsiteRequest(username, platform, websiteUrl);
      await websiteQueue.addRequest(websiteReq, { forefront: false });
      log.debug(`Queued website: ${websiteUrl} for @${username}`);
    },
  });

  profileCrawler.requestQueue = profileQueue;
  await profileCrawler.run();
  log.info(`Phase 2 complete. Saved ${savedCount()} creators.`);

  // ── Phase 3: Website & Monetization Detection ──────────────────────────────

const websiteCount = (await websiteQueue.getInfo())?.totalRequestCount ?? 0;

  if (websiteCount > 0) {
    log.info(`Phase 3: Detecting website/product signals for ${websiteCount} creators...`);

    const websiteCrawler = createWebsiteCrawler({
      proxyConfiguration: residentialProxyConfig,
    });

    websiteCrawler.requestQueue = websiteQueue;
    await websiteCrawler.run();
    log.info('Phase 3 complete.');
  } else {
    log.info('Phase 3: No websites found — skipping.');
  }

  // ── Summary ────────────────────────────────────────────────────────────────

  apifyLog.info(`Creator Discovery Engine finished. Total creators saved: ${savedCount()}`);

} catch (err) {
  log.error(`Actor failed: ${(err as Error).message}`);
  throw err;
} finally {
  await Actor.exit();
}
