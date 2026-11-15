# Code-driven AI motion graphics: creators and projects using coding agents (Claude Code, Codex, Cursor) with Remotion, HyperFrames, three.js, HTML/Canvas and similar

Research date: 2026-11-15. Scope: 2025 to 2026, newest first.

**Method and limits (read first):**
- WebFetch could not reach any non-GitHub site from this session (substack, vanja.io, rescroll.ai, motion-graphics.org all failed DNS; the Apify fetch fallback was disabled for billing). Reddit is blocked to the search tool. So:
  - Facts about X posts, blogs and Substacks below come from **search-result snippets and summaries**, not full reads. Treat their details as "reported", not verified.
  - GitHub READMEs **were** read in full via raw.githubusercontent.com. Those claims are first-party self-descriptions: verified as what the author says, not as a judgment of quality.
- **I did not watch any of the videos.** Every quality judgment against the earner.co "Psychology Trick" bar (editorial kinetic type with mixed sans + serif italic, paper/film texture, halftone glTF props, camera moves, whip/RGB-split transitions, grade, tight SFX) is an **inference from descriptions, stills listed in READMEs, and techniques claimed**. The user should watch the linked MP4s before relying on any ranking.
- Timeline context from the sources: Remotion Agent Skills launched January 2026. Claude Opus 5.5 was released around 22 September 2026 (sources disagree on the exact date) and set off the "one-prompt motion graphics" wave. Claude Motion, an in-app claude.ai beta, followed on 8 October 2026.

---

## 1. Who has actually posted code-driven, AI-made motion graphics that look premium (not slideshows)?

### Takeaway
Nobody I found has publicly shown a reel that verifiably matches the full earner.co stack: halftone glTF props, paper/film texture, serif-italic editorial type, whip/RGB-split transitions and a grade all together. The closest candidates fall into three groups:
- **Editorial / paper / halftone look:** jaredcassoutt's `vox-skill` (Remotion, halftone paper collage) and bishpls' `animation-pipeline` (cut-paper riso titles, kinetic type).
- **Showreel-grade kinetic type with 3D/WebGL:** tuzhechen2005's `kinetic-reel`, howseen-ai's launch film, and Sunwood-ai-labs' and echris6's skill packs.
- **The most-followed "creator" packs:** Charlie Hills. All of these show heavy human direction plus iteration, with critic loops, not one-shot output.

### Cited Findings

**Closest to the editorial / paper / halftone aesthetic**
- **jaredcassoutt / `vox` (GitHub).** Two Claude Code skills that turn one researched topic into a narrated film.
  - `vox-skill` is built in **Remotion**. Its look is "paper collage, halftone cut-outs, offset red marker stroke". Example: a 65 s film on the founding of Baylor University (`baylor-founding.mp4`).
  - Per the author, "everything in that frame except the three portraits is drawn in code: the state outline, the flag, the charter, the wax seals… the timeline." Portraits are public-domain scans "screened into halftone locally".
  - Narration is the clock: the voiceover is generated first and every cue derives from its word boundaries. The music bed is synthesized to match a measured documentary cue, then sidechain-ducked.
  - The second skill, `vox-editorial` (Python + ffmpeg, 1080×1920), uses image-gen "only ever [for] subjects… the ground, the tape, the newsprint and the headline are drawn locally".
  - [GitHub README](https://github.com/jaredcassoutt/vox-editorial)
- **bishpls / `animation-pipeline` (GitHub).** "A base of operations for making films with Claude Code: songs, animation, typography and sound, all authored in code. Frames are drawn by JavaScript as pure functions of time and locked to the music's own clock."
  - First film: *OPEN ALL NIGHT*, 93 s at 1080p24, a "mid-century cut-paper title sequence (Saul Bass, *Catch Me If You Can*) printed on four riso inks… with overprint".
  - The song was performed by ElevenLabs Music. Seven takes were chosen using beat-grid fit, STT intelligibility and blind Gemini rankings. Lyrics print on the sung syllable.
  - The third film uses "exactly two short Seedance cut-ins".
  - [GitHub README](https://github.com/bishpls/animation-pipeline) · [v1.0 release with MP4](https://github.com/bishpls/animation-pipeline/releases/tag/v1.0)
- **0xS4N4TG / `papercut-explainer`** ("short vertical cut-paper explainer reels… nine Agent Skills plus a Remotion library", 218 stars) and **haiderfarooq3 / `paper-reel`** ("faceless 9:16 explainer reels in a cut-paper style", 140 stars). Both are listed in the curated awesome list. I did not open either.
  - [awesome-claude-video-skills](https://github.com/zhuyansen/awesome-claude-video-skills)
- **Phantomlau3674 / `voxstylehub-steven`** ("Vox-inspired editorial collage… deterministic Remotion assembly") and **kakaxi12 / `vox-director-codex`** ("Vox-style editorial paper-collage videos with ImageGen, HyperFrames, and MiniMax narration"). Codex-based; listed only.
  - [awesome-claude-video-skills](https://github.com/zhuyansen/awesome-claude-video-skills)

**Showreel-grade kinetic typography + 3D / WebGL**
- **tuzhechen2005 / `opus-video-skills` → `kinetic-reel`.** "Combines a 2D type canvas with three.js layers (particle terrain, liquid marble, a chrome knot, a particle cloud that condenses into a shape) and a WebGL post pass. Shots are joined by shape-continuity transitions, and the score is synthesized from the same timeline as the picture."
  - Example: "Work Reel '26", 84 s. "All imagery and all music are generated procedurally in code; no image, video or audio generation model is involved."
  - Sister skill `painted-animation` uses p5.js + p5.brush watercolour.
  - [GitHub README](https://github.com/tuzhechen2005/opus-video-skills) · [plugin listing](https://www.claudepluginhub.com/plugins/tuzhechen2005-kinetic-reel)
- **howseen-ai / `claude-motion-design`.** The launch video for Howseen "was made with Claude Opus 5.5 and this skill, in 5 iterations"; full source is in `examples/howseen-launch`.
  - Techniques: a `seek(t)`-only engine, closed-form springs, "a camera keyed in log space, shared-element handoffs, color floods… masked word-by-word text", subframe motion blur at 60 fps, and SFX "placed by peak", mixed to -14 LUFS. Stack is HTML + Playwright + ffmpeg (no Remotion).
  - 825 stars; flagged "CAUTION" by the awesome list's security grader.
  - [GitHub README](https://github.com/howseen-ai/claude-motion-design)
- **Sunwood-ai-labs / `hyperframes-motion-reel-skill`.** "Showreel-grade motion graphics… beat-synced" on a 120 BPM / 60 fps grid. "Plain fade-in chains are banned."
  - Builds on a paused GSAP timeline plus a pure `render(t)` Canvas/SVG layer, with morphing transitions ("type → line → graph → 3D grid → tunnel → logo"), code-generated WAV SFX, and lint → check → snapshot → render → ffprobe verification.
  - It is a port of an earlier `remotion-motion-reel`.
  - [GitHub README](https://github.com/Sunwood-ai-labs/hyperframes-motion-reel-skill)
- **echris6 / `motion-video-kit`** (1.4k stars). "Premium, launch-style commercials… code-built motion (HTML/GSAP), selective Three.js, and an independent-critic quality loop."
  - Built from "studying 28 professional SaaS launch films" and three sample commercials made "through dozens of rounds of independent critique". One is "a 40 s Three.js product spec ad for a foldable phone in which every frame is code".
  - Includes "deterministic accumulation motion blur", matching "a real device's motion frame by frame", and SFX on "every small move".
  - Note: it also uses AI-generated footage.
  - [GitHub README](https://github.com/echris6/motion-video-kit)
- **kiselas / `every-frame-is-code` (motion-kit).** A one-minute demo film viewable live in the browser, in Canvas 2D / WebGL / Three.js / GLSL / Web Audio. It explicitly targets the default "screensaver" look: "a dark navy background, a neon gradient, particles… everything moving linearly… crossfades as the only transition."
  - [GitHub README](https://github.com/kiselas/every-frame-is-code) · [live demo](https://kiselas.github.io/every-frame-is-code/)
- **Moessif / `code-video-showcase`** (434 stars). "Every frame drawn with HTML/Canvas/SVG/Three.js, every sound synthesized with Python, assembled by FFmpeg… No video, image or music generation models."
  - Structure: an 8 s opening, eleven style segments, an eight-flash montage, 120 BPM.
  - Credits "a prompt by the creator Mixx.ftr".
  - [GitHub README](https://github.com/Moessif/code-video-showcase)
- **Zane-0x5a / `remotion-director`.** Hero film made "by remotion-director on Claude Opus 5.5 from a one-line brief". Human input was "the brief, a slogan, a pick among the three previews, and one comment".
  - Publishes a **blank control** (same model and brief, no plugin) next to it for comparison. That is useful for judging what the skill adds.
  - [GitHub README](https://github.com/Zane-0x5a/remotion-director)

**Creator-led packs with a social audience**
- **Charlie Hills (`charlie947/motion-graphics-skills`, newsletter charliehills.substack.com, "71k readers").** "I make launch videos, animated charts and reels without After Effects or a video generator. Claude Code writes the animation as code… These 15 skills are the workflows I use, with the rules that came out of real rejected drafts."
  - Demos: a 20 s launch film ("deep blue glass, one glow"), a 12 s milestone loop (250,000 LinkedIn followers), and a "Why do we dream?" Vox-style explainer.
  - Skills include `title-sequence-3d`, `reel-export`, `vox-explainer`, `apple-launch-film` and `reference-to-motion`.
  - The look reads as tech/LinkedIn launch polish, not editorial paper.
  - [GitHub README](https://github.com/charlie947/motion-graphics-skills) · [Opus 5.5 edition](https://charliehills.substack.com/p/opus-55-motion-graphics)
- **Mamdouh Abo Ammar (`imMamdouhaboammar/motion-graphics-skills`).** "64 agent skills & studio hierarchy". Shows seven films with original audio, including 1080×1920 Arabic and English promos (26–59 s), the TEOLA product launch, and a 112 s Egyptian satirical cartoon. It ships project sources and "storyboard, motion proofs and QA" evidence. Built on HyperFrames plus Blender MCP.
  - [GitHub README](https://github.com/imMamdouhaboammar/motion-graphics-skills)
- **Louise de Sadeleer (@LouiseDSadeleer, Growth at Tella).** Substack tutorial "How I make custom motion graphics using Claude Code + Remotion" for animating screen recordings and podcasts. She uses FFmpeg to extract frames because Claude can't ingest video, and argues "the skill bottleneck moves from technical ability to taste".
  - On X she described a full edit pipeline: Claude does the rough cut, memes, Remotion motion graphics and SFX. She also shared a cutting skill trained on one of her manually edited videos.
  - Content is talking-head augmentation, not editorial reels. Article not read in full.
  - [Substack](https://louisedesadeleer.substack.com/p/how-i-make-custom-motion-graphics) · [X post](https://x.com/LouiseDSadeleer/status/2056656760769818996)
- **Jonny Burger (@JNYBGR, Remotion creator).** In July 2025 he posted a thread saying "every video you see below was vibe coded by Claude Code". He now edits the Remotion YouTube channel's "What's New" videos with Claude Code; the source has moved to `remotion-dev/remotion → packages/brand/src/announcements/whats-new-in-remotion`.
  - [X](https://x.com/JNYBGR/status/1947746161743564974) · [GitHub](https://github.com/JonnyBurger/whats-new-in-remotion)

**Adjacent but NOT code-driven (do not confuse)**
- **cth9191 / `motion-design`.** Despite the name, it is a Codex/Claude Code skill whose films are "Generate[d] with Higgsfield". The 10 styles include "Kinetic typography" and "Editorial collage". These are generative-video outputs, not code renders. [GitHub README](https://github.com/cth9191/motion-design)

### Inferences
- The editorial-paper look (halftone, collage, newsprint, riso overprint) **has been achieved in code** by jaredcassoutt and bishpls. Separately, three.js/WebGL 3D layers plus kinetic type have been achieved by tuzhechen2005, echris6 and kiselas. I found no single public project combining **halftone-shaded glTF props + serif-italic editorial type + film-gate texture + whip/RGB-split transitions** in one reel. That combination looks like open ground; the user would need to merge techniques from several of these repos.
- Most top examples are **product/SaaS launch films or showreels**, not 9:16 talking-point reels with a psychology/editorial voice. The vertical-reel examples (Mamdouh's promos, Charlie's `reel-export`, paper-reel) skew toward explainer pacing, not earner.co-style punchy editorial.
- Strongest quality signals to prioritise when watching: howseen-ai (5 iterations, source shipped), echris6 (dozens of critique rounds, 28-film study), jaredcassoutt (halftone paper aesthetic closest to the target), and tuzhechen2005 kinetic-reel (WebGL post pass + 3D).

### Gaps
- I couldn't watch videos, so there is no first-hand quality ranking.
- I couldn't access Reddit (r/Remotion, r/motiongraphics, r/AfterEffects) or Instagram/TikTok to find creators publishing reels made this way. No verified Instagram/TikTok creator who openly credits Claude/Remotion for earner.co-level reels was found.
- Star counts come from the awesome list (zhuyansen) or README badges as of this date; I did not cross-check them.

---

## 2. What did the viral "Claude made this animation" / "Remotion + Claude Code" posts actually show? (Remotion official skill and showcases)

### Takeaway
There were two viral waves:
- **January 2026: Remotion Agent Skills launch.** A Remotion X demo with a published prompt history. View counts are disputed (6M to 18.9M). Critics called the generic output "bland… stock-looking".
- **Late September to October 2026: Opus 5.5 "one-prompt showreel" posts.** Mostly self-promotional 15-second showreels rendered by Opus writing one HTML file captured frame by frame. Follow-up threads showed that the polished ones relied on references, brand assets, long briefs and many iterations.

### Cited Findings
- **Remotion launch post, 20 Jan 2026.** "Remotion now has Agent Skills – make videos just with Claude Code! $ npx skills add remotion-dev/skills. This animation was created just by prompting." A follow-up post linked the full prompt history as a gist under Jonny Burger's GitHub. — [Remotion on X](https://x.com/Remotion/status/2013626968386765291); [prompt-history post](https://x.com/Remotion/status/2013628043105890779)
- **Reach claims conflict across secondary sources:**
  - "21,886 likes and about 18.9 million views", "6M+ views… 25k+ installs in the first week", "around 13 million views on X in a week", and "147,000 views within hours". All are unverified secondary reporting.
  - [startuphub.ai](https://www.startuphub.ai/ai-news/general/2026/remotion-ai-video-makes-production-code-from-plain-prompts); [nemovideo guide](https://www.nemovideo.com/blog/remotion-agent-skills-claude-code-guide); [sulat.com](https://ai.sulat.com/remotion-turned-claude-code-into-a-video-production-tool-f83fd761b158)
- **Critical reception.** One widely shared January report called the output "an extremely bland, untasteful, stock-looking video" (as summarised in search results). — [Claude Code + Remotion guide aggregation](https://www.rescroll.ai/blog/claude-code-remotion-motion-graphics-2026) (not read in full)
- **What the official skill actually covers.** `remotion-dev/skills` offers `/remotion-best-practices`, `/remotion-create`, `/remotion-markup` ("compositions, animations, layout, typography, media elements, effects, audio, fonts, timing"), `/remotion-studio`, `/remotion-render`, `/remotion-maps`, `/remotion-captions`, `/remotion-interactivity`, `/remotion-docs`, `/remotion-upgrade` and `/remotion-multimedia`.
  - These are API-correctness and best-practice rules, **not design/taste guidance**.
  - Remotion also documents agent use at remotion.dev/docs/ai/coding-agents.
  - [remotion-dev/skills README](https://github.com/remotion-dev/skills)
- **Jonny Burger's follow-up.** He posted a beginner guide to Remotion + Skills on 26 Jan 2026. — [X](https://x.com/JNYBGR/status/2015708193167479209)
- **Opus 5.5 wave: the viral prompt.** "make a dynamic 15-second motion graphics video that shows what an incredible motion designer you are…"
  - Example one-shot post by Sebastian Röhl.
  - The "prompt" grew to absurd lengths, e.g. klöss's "1.5 minute… motion designer, animator, artist, sound engineer, video editor, and creative director" prompt.
  - X trending pages framed it as "Claude Opus 5.5 Generates Pro-Level Motion Graphics Videos in Minutes".
  - [Sebastian Röhl](https://x.com/SebastianRoehl/status/2103912457836323096); [klöss](https://x.com/kloss_xyz/status/2116612471880610054); [X trending](https://x.com/i/trending/2103646607262863711)
- **What the videos actually were.** "Opus 5.5 reads text and images and returns text. It can't output an MP4"; the videos use "deterministic rendering via code (headless browser plus ffmpeg)". The typical pipeline is "a single index.html rendered frame by frame with Playwright, then encoded with ffmpeg" (per Movez).
  - One test reports Opus "prefers route A with zero dependencies: one index.html, a seek function… Playwright… ffmpeg" and "skipped Remotion and HyperFrames even when available".
  - [pasqualepillitteri.it](https://pasqualepillitteri.it/en/news/19007/opus-5-5-motion-design-video-en); [Movez Substack](https://movez.substack.com/p/how-to-build-motion-design-studio); [search summary of X thread](https://x.com/ridark_eth/status/2106005237190275109)
- **The "one prompt" claim was debunked or nuanced:**
  - **Rexan Wong:** "everyone says they created it with 'one prompt', but my one prompt video looked mid so i went through a bunch of these videos to see how they were actually made." [X](https://x.com/rexan_wong/status/2103707054108299437)
  - **seeco:** "What the Viral 'One-Prompt' Videos Are Hiding." [X](https://x.com/seeconvm/status/2106096193235259564)
  - **Secondary write-ups:** some clips really came from a 30-word prompt, while others came from "a 9,500-character director's brief, a folder of skills, two API keys and a 12-hour autonomous run". A watercolor short took "163 model calls, about 6¾ hours". [cosine.ren](https://blog.cosine.ren/en/post/opus-5-5-motion-video-resources); [99aicreator](https://www.99aicreator.com/en/blog/ai-hot-topics-4/opus-5-5-video-generation-tutorial-224)
- **Cost claim.** A claim that such videos normally take "three to four weeks and cost $8,000 to $10,000" is from a single unverified post (search summary). — [ayautomate](https://www.ayautomate.com/resources/claude-opus-5-5-motion-graphics)
- **Claude Motion (claude.ai, beta from 8 Oct 2026, Team/Enterprise).** It produces short animated explainers exported as MP4. Anthropic's examples are a company-meeting explainer, a board chart and an onboarding tour.
  - Runway, Luma and Higgsfield announced handoff paths.
  - Community galleries (e.g. claude-motion.com) label themselves "unofficial".
  - Charlie Hills' `reference-to-motion` and `motion-prompt-writer` skills output Claude Motion prompts.
  - [bigfive.it](https://bigfive.it/en/claude-motion-motion-graphics-ai/); [artrealmai](https://artrealmai.com/article/claude-motion-beta-code-built-animated-explainers); [claude-motion.com gallery](https://claude-motion.com/gallery); [How-To Geek test](https://www.howtogeek.com/claude-can-create-motion-graphics-now-heres-how-easy-it-is/)
- **HyperFrames (HeyGen, Apache-2.0)** became the main Remotion alternative for agents: HTML/CSS/GSAP rendered via headless Chrome and FFmpeg, installed with `npx skills add heygen-com/hyperframes`.
  - HeyGen's pitch: LLMs have far more HTML than React/Remotion in their training data.
  - HeyGen's own speed comparison against Remotion is a single run.
  - [GitHub](https://github.com/heygen-com/hyperframes); [Medium overview](https://ai-engineering-trend.medium.com/heygens-hyperframes-the-open-source-framework-challenging-remotion-in-html-based-video-creation-c10437f0afca); [aifruit comparison](https://aifruit.app/blog/hyperframes-github)

### Inferences
- The viral clips were overwhelmingly **"look what the AI can do" self-showreels and SaaS launch films**: dark backgrounds, kinetic sans type, particles, UI cards. That genre forgives a lack of narrative and brand. It is a different genre from an editorial reel that carries an argument for 30–60 s with voiceover.
- The official Remotion skill teaches correctness, not taste. A premium look comes from **third-party taste layers** (rules files, references, critique loops), not from the official skill.

### Gaps
- I could not view the Remotion launch animation or the Burger prompt-history gist contents directly.
- Exact view counts for the viral posts remain unverified.

---

## 3. Which approach editorial / kinetic-type / 3D-prop reel quality, which fall short, and why?

### Takeaway
What separates the premium work is not the engine (Remotion, HyperFrames or raw HTML all work) but five things:
1. A reference or style lock.
2. Real brand and design tokens.
3. Audio-locked timing.
4. Deterministic seek(t) rendering with motion blur.
5. An independent render-and-critique loop.

One-shot outputs fall back to a recognisable "AI screensaver" default and read as slideshows.

### Cited Findings
- **Default failure mode, as named by builders:**
  - "a dark navy background, a neon gradient, particles 'for atmosphere', everything moving linearly and all at once, text on top of objects, and crossfades as the only transition." [kiselas/every-frame-is-code](https://github.com/kiselas/every-frame-is-code)
  - "Ask an AI agent for 'a video' and you usually get slides: one section per idea, a title, a photo, a fade between them." [bang-motion](https://github.com/bangtutorial/bang-motion)
  - "No centered title on a purple gradient, no fade-everything, no fake screenshots." [flaviorg/motion-studio](https://github.com/flaviorg/motion-studio)
- **Why it happens.** "Without a reference, Opus 5.5 falls back on the same default choices (centered title, gradient background, everything fading in)" (seeco). "Without that context, opus guesses your colors, your font and what your product even does" (Rexan Wong). Both from search summaries. — [seeco](https://x.com/seeconvm/status/2106096193235259564); [Rexan Wong](https://x.com/rexan_wong/status/2103707054108299437)
- **The prompt is a small part of the result.** "The prompt is maybe 10% of the result. The other 90% is the studio around it — the rules, the real brand, a reference, a plan locked to the beat, sound, and an honest review loop." — [flaviorg/motion-studio](https://github.com/flaviorg/motion-studio)
- **Skills alone may not fix taste.** A vanja.io write-up reportedly found the Remotion skills produced a look "close to the no-skill film" in one test, and quotes HeyGen saying "a single run decides nothing about quality". It names HyperFrames' `motion.md`, `sound.md` and `look.md` as the most precise craft rules it found (search summary; article not read). — [vanja.io](https://vanja.io/motion-graphics-claude-code/)
- **A motion designer's view.** One designer said the output "looks NOTHING like all the 'one-prompt motion graphics' you see on X" without brand assets and references (search summary of the Opus 5.5 discourse; the individual was not identified in the snippet). — [X trending summary](https://x.com/i/trending/2105354035146424453)
- **Where agents are weak.** "Agents are strongest on templated, high-volume output (caption styles, lower thirds, ad variants) and weakest on pacing, music sync, and anything you would normally fix by dragging a clip." — [Motionbox, Aug 2026](https://motionbox.io/blog/remotion-for-coding-agents)
- **Controlled comparison available.** remotion-director publishes a "blank control: same model, same brief, no plugin" next to its plugin output. — [GitHub](https://github.com/Zane-0x5a/remotion-director)
- **Techniques the premium-leaning repos claim that map to the earner.co style:**
  - **Halftone treatment:** jaredcassoutt screens portraits into halftone locally and builds a paper-collage ground. [vox](https://github.com/jaredcassoutt/vox-editorial)
  - **Print / riso texture and kinetic type:** bishpls' four-ink riso overprint, Saul Bass cut-paper. [animation-pipeline](https://github.com/bishpls/animation-pipeline)
  - **3D props / WebGL with post:** tuzhechen2005 kinetic-reel (three.js layers plus a WebGL post pass). echris6's "Three.js patterns: deterministic, seekable scenes; exploded layers with projected callouts… realism checklist". [opus-video-skills](https://github.com/tuzhechen2005/opus-video-skills); [motion-video-kit](https://github.com/echris6/motion-video-kit)
  - **Camera moves and transitions:** howseen-ai's "camera keyed in log space, shared-element handoffs, color floods", and Sunwood's "morphing transitions… instead of cross-fades". [howseen](https://github.com/howseen-ai/claude-motion-design); [Sunwood](https://github.com/Sunwood-ai-labs/hyperframes-motion-reel-skill)
  - **Motion blur:** howseen-ai's subframe blending; echris6's "deterministic accumulation motion blur".
  - **Tight SFX:** SFX "placed by peak" (howseen-ai); "clean sound effects on every small move with the hero moments clearly audible" (echris6); Web Audio SFX synthesized "from the same timing constants as the animation" (flaviorg).
  - **Hand-made feel:** one skill pack suggests motion "on twos… hold each pose for 2 frames at 24fps" (search summary). [vanja.io search summary](https://vanja.io/motion-graphics-claude-code/)
- **Apple-style kinetic type measured from real references.** `IskakovDamir/apple-motion`: "Apple-style kinetic typography recaps in Remotion, built from frame-accurate measurements of Apple recap videos" (listed only). — [awesome list](https://github.com/zhuyansen/awesome-claude-video-skills)

### Inferences
- **Approaching the target:**
  - jaredcassoutt/vox-skill is closest on texture and editorial voice.
  - tuzhechen2005 kinetic-reel is closest on bold type, 3D and WebGL post.
  - howseen-ai and echris6 are closest on camera, motion blur and SFX craft.
- **Falling short:**
  - Generic one-shot "showreels".
  - The official Remotion demo (by critics' account).
  - Most talking-head caption/edit skills, which are functional but not editorial design.
  - Higgsfield-based "kinetic typography" packs, which are generative video, not controllable code.
- **Why they fall short:** no reference, no type system (the model defaults to one sans), no texture/grade layer, crossfade-only transitions, no audio lock, and no critic pass on rendered frames.
- **Elements I saw no explicit claim for in any repo read:** serif-italic + bold-sans **mixed-font editorial pairing**, **film-gate/frame texture**, **RGB-split/whip transitions**, and **glTF model loading with a halftone shader**. They are standard three.js/GLSL techniques, so they are feasible, but no public AI-made example claiming them was found.

### Gaps
- No first-hand viewing to confirm whether any example reaches After Effects-level finish.
- I found no named professional motion designer's published critique (blog or video) of a specific Claude/Remotion piece.
- No Reddit sentiment was available.

---

## 4. What workflows, prompts and skills did they share?

### Takeaway
The converging workflow is:
1. Brand/design-system files (brand.md, MOTION.md, style guide).
2. Reference-video analysis (ffmpeg frames → contact sheets → style guide).
3. A storyboard or beat-grid table approved before code.
4. Build as a pure function of time (seek(t) / Remotion frame).
5. Audio-first timing (VO word boundaries or BPM grid).
6. Render key stills, then score/critique with a fresh "judge" agent, fix the worst issues, repeat.
7. Final render plus loudness/QA checks.

### Cited Findings
- **Design-system files:**
  - Charlie Hills' `brand-intake` "writes `brand.md`… and `MOTION.md` (your colours, type, timing and motion rules), and adds a rule to CLAUDE.md so Claude reads both before it animates anything". [charlie947](https://github.com/charlie947/motion-graphics-skills)
  - flaviorg's "brand.md kit keeps the next one consistent". [motion-studio](https://github.com/flaviorg/motion-studio)
  - A Cursor workflow "begins with a structured markdown prompt file defining brand style". [search summary](https://aigc-web-base.vercel.app/blog/blog-to-video-remotion-cursor-ai-workflow-guide)
- **Reference-video analysis:**
  - flaviorg: "breaks any reference video into contact sheets and scene cuts so Claude can borrow its motion language — never its content". [motion-studio](https://github.com/flaviorg/motion-studio)
  - mrpaidsocial: `reel-style-clone` → `STYLE-GUIDE.md` from a reference reel. [video-editor-agent](https://github.com/mrpaidsocial/mrpaidsocial-video-editor-agent)
  - Charlie Hills: `reference-to-motion` "breaks down a video you admire for its moves". [charlie947](https://github.com/charlie947/motion-graphics-skills)
  - Louise de Sadeleer extracts frames with FFmpeg because Claude can't ingest video. [search summary](https://louisedesadeleer.substack.com/p/how-i-make-custom-motion-graphics)
  - Rexan Wong: ask Opus to match the style of one or two chosen reference videos, feed brand assets and screenshots, and request three storyboard variants. [search summary](https://x.com/rexan_wong/status/2103707054108299437)
- **Plan before code:**
  - flaviorg: "Claude shows you a table of every state on the beat grid before writing code, and waits for your approval". [motion-studio](https://github.com/flaviorg/motion-studio)
  - howseen-ai: "inputs → beat map → 4 stills approved → full render → pop scan → audio → final". [howseen](https://github.com/howseen-ai/claude-motion-design)
  - Kyyzen0 `motion-storyboard`: "frame ranges, reading holds, asset list". [Kyyzen0](https://github.com/Kyyzen0/claude-motion-design-skills)
- **Critique loops:**
  - flaviorg: "Claude renders key frames, scores 8 criteria from 1–10, fixes the three worst, and repeats until everything is ≥ 8". [motion-studio](https://github.com/flaviorg/motion-studio)
  - echris6 "Gauntlet loop": "builder ≠ judge, fresh critics on the actual render, item-by-item verification, and a ledger", with ready-made critic prompts. [motion-video-kit](https://github.com/echris6/motion-video-kit)
  - mrpaidsocial: "verify pixels and dB, not intentions", using one multi-timestamp snapshot, then a vision check, then verifying the rendered file. [video-editor-agent](https://github.com/mrpaidsocial/mrpaidsocial-video-editor-agent)
  - Zane-0x5a: a critic-loop pipeline "judged on its real rendered frames". [remotion-director](https://github.com/Zane-0x5a/remotion-director)
- **Audio as the clock:**
  - jaredcassoutt: "the narration is the clock… every scene length and every animation cue is derived from its word boundaries". [vox](https://github.com/jaredcassoutt/vox-editorial)
  - Sunwood: every cut is `b(n)` on 120 BPM / 60 fps. [Sunwood](https://github.com/Sunwood-ai-labs/hyperframes-motion-reel-skill)
  - bishpls: lyrics print on the sung syllable using ElevenLabs word timestamps. [animation-pipeline](https://github.com/bishpls/animation-pipeline)
- **Director-style notes.** Use specific camera language rather than "make it better", which "get[s] random changes" (Rexan Wong, search summary). Charlie Hills' edit lines include "Slow down the second scene", "Use my brand colours: [hex]", "Make it 1080 x 1350". [charlie947](https://github.com/charlie947/motion-graphics-skills)
- **Shared prompts:**
  - Charlie Hills' starter prompt: "Make a dynamic 15-second motion graphics video that shows what an incredible motion designer you are. Go all out." plus prompt files (`brand-design-system.md`, `briefs.md`, `polish.md`, `effects.md`). [charlie947](https://github.com/charlie947/motion-graphics-skills)
  - Remotion's full launch prompt history (gist). [Remotion X](https://x.com/Remotion/status/2013628043105890779)
- **Engine choice:**
  - Remotion (React; commercial licence needed above a company-size threshold, per Sunwood's note), HyperFrames (Apache-2.0, HTML + GSAP), or raw HTML + Playwright + ffmpeg.
  - Several premium-leaning repos (howseen-ai, tuzhechen2005, kiselas, Moessif) skip Remotion entirely.
  - [Sunwood](https://github.com/Sunwood-ai-labs/hyperframes-motion-reel-skill); [howseen](https://github.com/howseen-ai/claude-motion-design)
- **Ecosystem directories for finding more:**
  - `zhuyansen/awesome-claude-video-skills` ("180 repos by type, each security-graded"). [GitHub](https://github.com/zhuyansen/awesome-claude-video-skills)
  - `wilwaldon/Claude-Code-Video-Toolkit`. [GitHub](https://github.com/wilwaldon/Claude-Code-Video-Toolkit)
  - Movez's "How to build motion design studio with Opus 5.5 (Full-course)". [Substack](https://movez.substack.com/p/how-to-build-motion-design-studio)
  - nicco's "14 repos" thread. [X](https://x.com/0xnicc0/status/2117592218663784631)
- **After Effects bridges (hybrid route):**
  - `Arman-Luthra/aftr` ("Puppeteer for After Effects… with Claude Code").
  - `JUNKDOGE-JOE/after-effects-mcp`.
  - `AnmolChandiok/claude-after-effects-skill` (turns a code-made video into an editable AE project).
  - Listed only. [awesome list](https://github.com/zhuyansen/awesome-claude-video-skills)

### Inferences
- For an earner.co-style reel, the most transferable recipe combines:
  - jaredcassoutt's "narration is the clock" plus local halftone screening;
  - flaviorg/mrpaidsocial reference-reel → style-guide extraction;
  - echris6's builder ≠ judge critique loop;
  - tuzhechen2005/echris6 three.js patterns for props.

  On top of that, the user would add their own rules for the missing pieces: serif-italic/sans pairing, film-gate texture overlay, RGB-split/whip transitions, and glTF + halftone shader.
- An AE-bridge route (code → editable AE project) is a pragmatic fallback where code can't reach AE-level finish.

### Gaps
- I couldn't read the full workflow articles (Louise de Sadeleer's Substack, vanja.io, the seeco article, Movez's course, rescroll.ai) because of network restrictions. Their specific rules are summarised from search snippets only.
- I couldn't retrieve the contents of the Remotion launch prompt-history gist.
