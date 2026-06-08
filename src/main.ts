import { Actor, log as apifyLog } from 'apify';
import { RequestQueue, log } from 'crawlee';
import { validateInput } from './utils.js';
import { buildGoogleSearchRequests, createGoogleCrawler } from './google-search.js';
import { createProfileCrawler, makeProfileRequest } from './profile-enrichment.js';
import { createWebsiteCrawler, makeWebsiteRequest } from './website-detection.js';
import { savedCount, flushCreators, getSeenKeys } from './output.js';
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
    minResults: input.minResults ?? 'not set',
  });

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

  // Load cross-run seen usernames to avoid returning the same creator twice
  const seenStore = await Actor.openKeyValueStore('launchback-seen');
  const seenKey = `${input.platform}-seen`;
  const seenList = await seenStore.getValue<string[]>(seenKey) ?? [];
  const seenUsernames = new Set<string>(seenList);
  log.info(`Loaded ${seenUsernames.size} previously seen creators.`);

  const runId = Actor.getEnv().actorRunId ?? 'local';
  const googleQueue = await RequestQueue.open(`google-search-${runId}`);
  const profileQueue = await RequestQueue.open(`profile-enrichment-${runId}`);
  const websiteQueue = await RequestQueue.open(`website-detection-${runId}`);

  const minResults = input.minResults ?? 1;
  const batchSize = Math.max(10, Math.ceil((input.maxResults * 3) / 10));
  const maxPages = 100;
  let nextPage = 0;

  // Phase 1 + 2 loop: keep scraping until minResults met or page limit hit
  while (savedCount() < minResults && nextPage < maxPages) {
    log.info(`Phase 1: Enqueuing Google pages ${nextPage}–${nextPage + batchSize - 1}...`);

    const searchRequests = buildGoogleSearchRequests(input, nextPage);
    for (const req of searchRequests) await googleQueue.addRequest(req);
    nextPage += batchSize;

    const googleCrawler = createGoogleCrawler({
      proxyConfiguration: googleProxyConfig,
      input,
      onProfileFound: async (profileUrl: string, username: string) => {
        const key = `${input.platform}:${username.toLowerCase()}`;
        if (seenUsernames.has(key)) {
          log.debug(`Skipping already-seen creator: @${username}`);
          return;
        }
        const profileReq = makeProfileRequest(profileUrl, username, input.keyword, input.platform as Platform);
        await profileQueue.addRequest(profileReq, { forefront: false });
        log.debug(`Queued profile: ${profileUrl}`);
      },
    });

    googleCrawler.requestQueue = googleQueue;
    await googleCrawler.run();
    log.info(`Phase 1 batch complete. ${(await profileQueue.getInfo())?.totalRequestCount ?? 0} profiles queued total.`);

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
    log.info(`Phase 2 batch complete. ${savedCount()}/${minResults} creators found.`);
  }

  // ── Phase 3: Website & Monetization Detection ──────────────────────────────

  const websiteCount = (await websiteQueue.getInfo())?.totalRequestCount ?? 0;

  if (websiteCount > 0) {
    log.info(`Phase 3: Detecting website/product signals for ${websiteCount} creators...`);
    const websiteCrawler = createWebsiteCrawler({ proxyConfiguration: residentialProxyConfig });
    websiteCrawler.requestQueue = websiteQueue;
    await websiteCrawler.run();
    log.info('Phase 3 complete.');
  } else {
    log.info('Phase 3: No websites found — skipping.');
  }

  // Save seen usernames for next run
  for (const key of getSeenKeys()) seenUsernames.add(key);
  await seenStore.setValue(seenKey, [...seenUsernames]);
  log.info(`Saved ${seenUsernames.size} total seen creators to store.`);

  await flushCreators();
  apifyLog.info(`Creator Discovery Engine finished. Total creators saved: ${savedCount()}`);

} catch (err) {
  log.error(`Actor failed: ${(err as Error).message}`);
  throw err;
} finally {
  await Actor.exit();
}
