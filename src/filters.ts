import { Platform } from './types.js';

const INSTAGRAM_BLOCKED_PATHS = new Set([
  'p', 'reel', 'reels', 'stories', 'explore', 'tv',
  'accounts', 'direct', 'about', 'ar', 'developer',
  'legal', 'privacy', 'safety', 'help', 'press',
  'blog', 'api', 'oauth', 'static', 'graphql',
]);

const INSTAGRAM_USERNAME_RE = /^[a-zA-Z0-9._]{1,30}$/;

export function isValidInstagramProfileUrl(url: string): boolean {
  try {
    const parsed = new URL(url);
    if (!parsed.hostname.endsWith('instagram.com')) return false;
    const segments = parsed.pathname.split('/').filter(Boolean);
    if (segments.length !== 1) return false;
    const username = segments[0];
    if (INSTAGRAM_BLOCKED_PATHS.has(username)) return false;
    return INSTAGRAM_USERNAME_RE.test(username);
  } catch {
    return false;
  }
}

export function isValidYoutubeChannelUrl(url: string): boolean {
  try {
    const parsed = new URL(url);
    if (!parsed.hostname.endsWith('youtube.com')) return false;
    const path = parsed.pathname;
    if (/^\/@[^/]+\/?$/.test(path)) return true;
    if (/^\/c\/[^/]+\/?$/.test(path)) return true;
    if (/^\/channel\/UC[^/]+\/?$/.test(path)) return true;
    if (/^\/user\/[^/]+\/?$/.test(path)) return true;
    return false;
  } catch {
    return false;
  }
}

export function isValidProfileUrl(url: string, platform: Platform): boolean {
  return platform === 'instagram'
    ? isValidInstagramProfileUrl(url)
    : isValidYoutubeChannelUrl(url);
}

export function isInFollowerRange(
  followerCount: number | null,
  minFollowers: number,
  maxFollowers: number,
): boolean {
  if (followerCount === null) return false;
  return followerCount >= minFollowers && followerCount <= maxFollowers;
}

export function extractUsernameFromUrl(url: string, platform: Platform): string {
  try {
    const parsed = new URL(url);
    const segments = parsed.pathname.split('/').filter(Boolean);
    if (platform === 'instagram') {
      return segments[0] ?? '';
    }
    if (segments[0] === 'channel' || segments[0] === 'c' || segments[0] === 'user') {
      return segments[1] ?? '';
    }
    if (segments[0]?.startsWith('@')) {
      return segments[0].slice(1);
    }
    return segments[0] ?? '';
  } catch {
    return '';
  }
}
