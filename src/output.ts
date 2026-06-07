import { Actor } from 'apify';
import { ActorInput, CreatorRecord, Platform, WebsiteUpdate } from './types.js';
import { isInFollowerRange } from './filters.js';

// In-memory store: dedup key → full record (used by Phase 3 to enrich)
const creatorStore = new Map<string, CreatorRecord>();

function dedupeKey(platform: Platform, username: string): string {
  return `${platform}:${username.toLowerCase()}`;
}

export function isAlreadySaved(platform: Platform, username: string): boolean {
  return creatorStore.has(dedupeKey(platform, username));
}

export function savedCount(): number {
  return creatorStore.size;
}

export async function saveCreator(
  partial: Omit<CreatorRecord, 'websiteUrl' | 'hasWebsite' | 'websiteType' | 'hasProductLinks' | 'productPlatform'>,
  input: ActorInput,
): Promise<boolean> {
  const key = dedupeKey(partial.platform, partial.username);
  if (creatorStore.has(key)) return false;

  if (!isInFollowerRange(partial.followerCount, input.minFollowers, input.maxFollowers)) {
    return false;
  }

  const record: CreatorRecord = {
    ...partial,
    name: partial.name || partial.username,
    websiteUrl: '',
    hasWebsite: false,
    websiteType: '',
    hasProductLinks: false,
    productPlatform: '',
  };

  creatorStore.set(key, record);
  // Push immediately for crash-safety; Phase 3 will push an enriched version
  await Actor.pushData(record);
  return true;
}

export async function updateCreatorWebsite(
  username: string,
  platform: Platform,
  update: WebsiteUpdate,
): Promise<void> {
  const key = dedupeKey(platform, username);
  const existing = creatorStore.get(key);
  if (!existing) return;

  const updated: CreatorRecord = { ...existing, ...update };
  creatorStore.set(key, updated);

  // Re-push updated record. Dataset will have two entries per enriched creator;
  // downstream consumers should deduplicate by (platform, username), keeping latest.
  await Actor.pushData(updated);
}

export function getCreator(platform: Platform, username: string): CreatorRecord | undefined {
  return creatorStore.get(dedupeKey(platform, username));
}
