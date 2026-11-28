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
Creating a post is `POST /v1/posts` with a JSON body (`content`, `platforms`, `mediaItems`, `scheduledFor`/`publishNow`; per PostZen's public docs). The exact schema is in the OpenAPI spec (`https://www.postzen.dev/openapi.json`), the reference (`https://docs.postzen.dev/api-reference`) and the agent quickstart (`https://www.postzen.dev/agent-quickstart.md`); those hosts are NOT on this environment's allowlist, so to read them ask the user before proposing `update_environment` to add `www.postzen.dev` and `docs.postzen.dev`. A hosted MCP server also exists at `https://mcp.postzen.dev/mcp` (the user can add it as a claude.ai connector for native tools).

## Rules (publishing is outward-facing and can't be unsent)
1. **Never publish, schedule or delete a post unless the user asks for that in the current turn.** "Approved" for a reel render is not approval to post it. Drafts (no `publishNow`, no `scheduledFor`) are safe: create a draft when the user says "get it ready to post".
2. Before any publish or schedule, show the user exactly what will go out (account, caption, media file, time) and get a clear yes. After it goes out, report the post id and status from the API, not from memory.
3. Reels need the final full-res video (`workflows/video/renders/*_1080p.mp4`) at a URL PostZen can fetch, or an upload route from the spec; do not post the 540p preview. Check the spec for media rules (length, size, aspect) before the call.
4. Posting copy must follow the run's `brief.md`/`script.txt` and use the handle `launch.back`; ask the user for the caption if none exists. No stock hashtags unless asked.
5. Keep a one-line record of what was posted (date, post id, run) in the run folder, e.g. `gen/runs/<run>/posted.md`.
