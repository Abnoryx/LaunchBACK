export type Platform = 'instagram' | 'youtube';

export interface ActorInput {
  platform: Platform;
  keyword: string;
  country?: string;
  minFollowers: number;
  maxFollowers: number;
  maxResults: number;
}

export interface CreatorRecord {
  name: string;
  username: string;
  platform: Platform;
  profileUrl: string;
  bio: string;
  followerCount: number | null;
  country: string;
  email: string;
  keyword: string;
  websiteUrl: string;
  hasWebsite: boolean;
  websiteType: string;
  hasProductLinks: boolean;
  productPlatform: string;
}

export interface WebsiteUpdate {
  websiteUrl: string;
  hasWebsite: boolean;
  websiteType: string;
  hasProductLinks: boolean;
  productPlatform: string;
}

export interface EnrichmentResult {
  name: string;
  username: string;
  bio: string;
  followerCount: number | null;
  country: string;
  email: string;
  websiteUrl: string;
}

export type RequestLabel =
  | 'GOOGLE_SEARCH'
  | 'INSTAGRAM_PROFILE'
  | 'YOUTUBE_PROFILE'
  | 'WEBSITE_DETECTION';

export interface GoogleSearchUserData {
  label: 'GOOGLE_SEARCH';
  page: number;
  query: string;
}

export interface ProfileUserData {
  label: 'INSTAGRAM_PROFILE' | 'YOUTUBE_PROFILE';
  profileUrl: string;
  username: string;
  keyword: string;
}

export interface WebsiteUserData {
  label: 'WEBSITE_DETECTION';
  username: string;
  platform: Platform;
  websiteUrl: string;
}

export type CrawlUserData = GoogleSearchUserData | ProfileUserData | WebsiteUserData;
