import { ActorInput } from './types.js';

export function parseFollowerCount(text: string): number | null {
  if (!text) return null;
  const cleaned = text.replace(/,/g, '').trim();
  const match = cleaned.match(/([0-9]+(?:\.[0-9]+)?)\s*([KMBkmb])?/);
  if (!match) return null;
  const num = parseFloat(match[1]);
  const suffix = match[2]?.toUpperCase();
  if (suffix === 'K') return Math.round(num * 1_000);
  if (suffix === 'M') return Math.round(num * 1_000_000);
  if (suffix === 'B') return Math.round(num * 1_000_000_000);
  return Math.round(num);
}

export function extractEmail(text: string): string {
  if (!text) return '';
  const match = text.match(/[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}/);
  return match ? match[0] : '';
}

export function normalizeUrl(url: string): string {
  if (!url) return '';
  let normalized = url.trim();
  if (!/^https?:\/\//i.test(normalized)) {
    normalized = `https://${normalized}`;
  }
  try {
    const parsed = new URL(normalized);
    parsed.search = '';
    parsed.hash = '';
    return parsed.toString().replace(/\/$/, '');
  } catch {
    return normalized;
  }
}

export function stripSurroundingQuotes(text: string): string {
  return text.replace(/^["']|["']$/g, '').trim();
}

export function validateInput(input: unknown): ActorInput {
  const inp = input as Record<string, unknown>;
  if (!inp) throw new Error('Input is required');

  if (!['instagram', 'youtube'].includes(inp['platform'] as string)) {
    throw new Error(`Invalid platform: "${inp['platform']}". Must be "instagram" or "youtube".`);
  }

  const keyword = inp['keyword'];
  if (typeof keyword !== 'string' || keyword.trim().length === 0) {
    throw new Error('keyword is required and must be a non-empty string.');
  }

  const minFollowers = inp['minFollowers'];
  if (typeof minFollowers !== 'number' || minFollowers < 0) {
    throw new Error('minFollowers must be a non-negative number.');
  }

  const maxFollowers = inp['maxFollowers'];
  if (typeof maxFollowers !== 'number' || maxFollowers <= (minFollowers as number)) {
    throw new Error('maxFollowers must be a number greater than minFollowers.');
  }

  const maxResults = inp['maxResults'];
  if (typeof maxResults !== 'number' || maxResults < 1 || maxResults > 500) {
    throw new Error('maxResults must be between 1 and 500.');
  }

  const minResults = inp['minResults'];

  return {
    platform: inp['platform'] as ActorInput['platform'],
    keyword: keyword.trim(),
    country: typeof inp['country'] === 'string' ? inp['country'].trim() : undefined,
    minFollowers: minFollowers as number,
    maxFollowers: maxFollowers as number,
    maxResults: maxResults as number,
    minResults: typeof minResults === 'number' && minResults >= 1 ? minResults : undefined,
  };
}
