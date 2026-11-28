---
name: postzen
description: Post, schedule and manage the user's social posts (Instagram @launch.back reels and posts) through the PostZen API. Use whenever the user asks to post, publish, schedule, draft, queue, check or delete a post or reel, or to send a finished /gen or /rescene reel out, even if they only say "post it" or "put it on Instagram".
---
# PostZen (social posting API)

**Installed 2026-11-28 by the user's request, for every chat.** The API key is saved on the "LaunchBACK" cloud environment as a network secret for `api.postzen.dev`: the proxy injects `Authorization: Bearer ...` on every HTTPS request to that host. Never ask for, print or write the key anywhere (not in chat, not in files, not in git). Do NOT add your own Authorization header. If a script insists on an env var, set it to the placeholder `proxy-injected` for that command only. If a call returns 401/403, the saved key is wrong or revoked: ask the user to re-save it with `request_credential` for host `api.postzen.dev`.

## Connected right now (verified 2026-11-28)
- Instagram `@launch.back` (display name "Launch Back"), profile `LaunchBack` (slug `launchback`), accountId `j97c875mefv7strge0xgxfnpbx8gyg3c`, status connected. Re-read `GET /v1/accounts` before relying on this.
- Base URL `https://api.postzen.dev/v1` (all routes live under `/v1`). Root `GET https://api.postzen.dev/` lists the docs links.

## Calls that are verified to work (read-only)
```bash
curl -s https://api.postzen.dev/v1/accounts      # connected accounts, ids, platform, status
curl -s https://api.postzen.dev/v1/posts          # posts with status (draft | scheduled | ...), platforms, scheduledFor
```
## Posting a reel (verified end to end 2026-11-28; OpenAPI at https://www.postzen.dev/openapi.json, hosts now on the allowlist)
1. Upload the video: `POST /v1/media/presign {"filename","contentType":"video/mp4"}` -> `uploadUrl` (Cloudflare R2, presigned) + `publicUrl` (media.postzen.dev). `PUT` the file to `uploadUrl` with `Content-Type: video/mp4` (200 = done). Hosts `*.r2.cloudflarestorage.com` (the exact postzen-media host) and `media.postzen.dev` were added to the environment allowlist.
2. `POST /v1/posts` with exactly ONE creation mode (`scheduledFor` ISO 8601 | `publishNow` | `isDraft` | `queuedFromProfile`), `content` (<= 2,200 chars), `mediaItems:[{url: publicUrl}]`, `platforms:[{platform:"instagram", accountId, settings:{postType:"reel", shareToFeed:true}}]`. Without `settings.postType:"reel"` a video is rejected ("feed publishing supports images only"). Optional: `settings.collaborators` (<=3), `settings.firstComment`, `settings.trialParams {graduationStrategy: MANUAL|SS_PERFORMANCE}`, `timezone`, `title`, `tags`. Send header `x-request-id: <stable key>` so a retry cannot create a duplicate.
3. Check: `GET /v1/posts` (status scheduled|draft|published...). Change/cancel: `/v1/posts/{postId}` (see the spec). Best times for the account: `GET /v1/analytics/best-time?platform=instagram&accountId=...` (empty until the account has post history, then use research).
Free plan: 20 posts per month. Validation probes with invalid bodies are safe (they create nothing); a body that passes validation DOES create the post.

## Rules (publishing is outward-facing and can't be unsent)
1. **Never publish, schedule or delete a post unless the user asks for that in the current turn.** "Approved" for a reel render is not approval to post it. Drafts (no `publishNow`, no `scheduledFor`) are safe: create a draft when the user says "get it ready to post".
2. Before any publish or schedule, show the user exactly what will go out (account, caption, media file, time) and get a clear yes. After it goes out, report the post id and status from the API, not from memory.
3. Reels need the final full-res video (`workflows/video/renders/*_1080p.mp4`) at a URL PostZen can fetch, or an upload route from the spec; do not post the 540p preview. Check the spec for media rules (length, size, aspect) before the call.
4. Posting copy must follow the run's `brief.md`/`script.txt` and use the handle `launch.back`; ask the user for the caption if none exists. No stock hashtags unless asked.
5. Keep a one-line record of what was posted (date, post id, run) in the run folder, e.g. `gen/runs/<run>/posted.md`.
