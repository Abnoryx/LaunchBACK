import { Actor } from 'apify';
import { ActorInput, CreatorRecord, Platform, WebsiteUpdate } from './types.js';
import { isInFollowerRange } from './filters.js';

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
}

export async function flushCreators(): Promise<void> {
  const records = [...creatorStore.values()];
  if (records.length > 0) await Actor.pushData(records);
}

export function getCreator(platform: Platform, username: string): CreatorRecord | undefined {
  return creatorStore.get(dedupeKey(platform, username));
}
