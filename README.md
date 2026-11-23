# LaunchBack video workflow

Short-form reels for LaunchBack, built in our own WebGL engine. Everything lives in `workflows/video/`.

- Rules and state: `workflows/video/REQUIREMENTS.md`, `ROADMAP.md`, `HANDOFF.md`
- Skills: `/rescene` (reel or .aep -> templates) and `/gen` (script -> finished reel)

## Library site (`/site`)
A password-protected Next.js page, deployed on Vercel from this repo, to browse the shot library and delete templates/assets, edit shot notes and upload assets. Every action is one commit on `main`. Vercel setup: import the repo, **Root Directory = `site`**, env `GITHUB_TOKEN` (fine-grained, Contents read/write on this repo only), `ADMIN_PASSWORD`, `REPO=abnoryx/launchback`. Bought scenes are shown read-only (their files are never in git). Look: the `ui-ux-pro-max` skill (`.claude/skills`); animated bits from React Bits (`site/components`).
