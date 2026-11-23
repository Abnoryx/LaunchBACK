# AI-driven After Effects (and pro motion tools) + motion designers using AI in editorial reel workflows

Research date: 2026-11-15. Method: web search snippets. WebFetch could only reach GitHub; YouTube, earnera.co, videohighlight.com and other non-GitHub hosts failed DNS in this sandbox. Anything taken only from a search snippet (not opened) is marked **(reported)**. No video was watched, so all quality judgments about outputs are second-hand.

---

## Q1. Who has publicly shown Claude/ChatGPT/agents driving After Effects (AE MCP servers, scripts) to produce polished animation? What did the results look like?

### Takeaway
There are many open-source AE MCP servers (2025–2026) plus two big commercial and vendor routes: Higgsfield's "AI Motion Designer" (GPT-6 Astra / Codex, also Claude via MCP) and Adobe's own After Effects AI Assistant (beta, Aug 2026). None of the GitHub repos shows polished showcase renders. The only hands-on agency review found (Motion The Agency, Oct 2026) says output is native and editable but needed a second pass for timing and easing. No one is publicly documented producing earner/earnedits-level editorial reels end-to-end by agent. The credible pattern is AI building or automating the comp, with a human doing art direction and polish.

### Cited Findings

**Open-source AE MCP servers (GitHub, verified by fetch where noted)**
- ishu86/after-effects-mcp: 70+ tools (comps, layers, keyframes, expressions, effects), plus templates for lower thirds, title cards, transitions, logo reveals and text animators, spring/physics presets, about 20 expression templates and effect presets ("cinematic", "vhsRetro", "neonGlow"). Needs AE 2024+. 49 stars, 11 forks, 11 commits. It has **no demo renders**, only example prompts. — [GitHub (fetched)](https://github.com/ishu86/after-effects-mcp)
- solomondivyananth/aftereffects-mcp: 50 tools via a CEP panel. Has a **render-frame feedback loop**: `ae_render_frame` sends frames back to the model, and `ae_review_motion` returns a motion contact sheet, so the model "renders a real frame, makes a real edit, then re-renders to check its own work". Also a sandbox guard, one undo step per call, `ae_proof` (41 checks) and 22 skills. The only showcased output is a welcome animation GIF/MP4. 89 stars. The README admits the authoring and render tools have had little real-world use, and it contradicts itself on tests/CI. — [GitHub (fetched)](https://github.com/solomondivyananth/aftereffects-mcp)
- Others found via search **(reported, not opened)**:
  - Miinwan/mcp-after-effects (kinetic text, PSD-to-animation, transitions; macOS, AE 2026). It returned 404 when fetched, so it may be deleted or private.
  - LiamcKerr/after-effects-mcp (CEP, preview frames, render progress)
  - a-y-ibrahim/after-effects-mcp (47 tools, ExtendScript, Arabic/RTL)
  - kumoproductions/mcp-aftereffects (TypeScript, AE 2024–2026, no panel)
  - JUNKDOGE-JOE/after-effects-mcp (30 `ae.*` tools; works with Codex and Cursor)
  - Sources: [ishu86 search result](https://github.com/ishu86/after-effects-mcp), [Miinwan](https://github.com/Miinwan/mcp-after-effects), [LiamcKerr](https://github.com/LiamcKerr/after-effects-mcp), [a-y-ibrahim](https://github.com/a-y-ibrahim/after-effects-mcp), [kumoproductions](https://github.com/kumoproductions/mcp-aftereffects), [JUNKDOGE-JOE](https://github.com/JUNKDOGE-JOE/after-effects-mcp)
- A commercial "AE-MCP Pro" exists (p10q/ae-mcp on Glama) with tiered plans. Its landing page makes broad claims, and I found no independent reviews **(reported)**. — [Glama](https://glama.ai/mcp/servers/p10q/ae-mcp)
- LobzyJay/motion-design-with-claude-and-codex: Claude Code / Codex **skills** for motion designers, not a server. It has four skills: motion-design principles and easing taxonomy, aftereffects-motion (live MCP mode vs JSX script mode), blender-motion, and motion-design-critique (QA). It points at TheLlamainator/after-effects-mcp. It targets senior motion designers and shows **no example renders**. 41 stars. — [GitHub (fetched)](https://github.com/LobzyJay/motion-design-with-claude)

**Vendor / commercial agents inside AE**
- **Higgsfield "AI Motion Designer"**: an agent that builds titles, transitions, logo reveals and product promos inside the open AE comp from a ChatGPT/Codex prompt (`@Higgsfield` then `/use-after-effects`). It is marketed as powered by GPT-6 Astra, and Higgsfield pages also mention Claude and Cursor access via its MCP. Layers stay native and editable. It requires Higgsfield, GPT and AE subscriptions, and AE 2024+ **(reported; vendor)**. — [Higgsfield product page](https://higgsfield.ai/ai-motion-designer), [Higgsfield blog](https://higgsfield.ai/blog/ai-motion-designer-after-effects-gpt), [Higgsfield MCP use-after-effects](https://higgsfield.ai/mcp/use-after-effects)
- AlphaSignal headline: "Higgsfield Lets Claude Build Fully Editable After Effects Projects" **(reported)**. — [AlphaSignal](https://alphasignal.ai/news/higgsfield-lets-claude-build-fully-editable-after-effects-projects)
- **Independent hands-on review, Motion The Agency (Oct 7, 2026)**: two motion designers ran three tests on a real project via the Higgsfield connector (a UI rebuild and a seven-frame storyboard animated end to end). Output was native AE layers. The **first attempt needed rework, and the second had "visibly better timing and easing"**. Astra gave each word its own layer and precomp instead of using AE text animators, a structural smell a pro would refactor. Full verdict not visible in snippets **(reported)**. — [Motion The Agency](https://www.motiontheagency.com/blog/gpt-6-astra-honest-review)
- Runtimewire questions whether the time saved justifies the three-subscription stack if designers spend much of their time fixing output **(reported)**. — [Runtimewire](https://runtimewire.com/article/higgsfield-chatgpt-after-effects-ai-motion-designer-astra)
- The AI Tribe's review says the agent's capability list (title animation, logo reveal, transitions, product promo) is "modest relative to the language around it". A human still has to decide "that the logo comes in half a second later, that the movement is too stiff" **(reported)**. — [theaitribe.com](https://theaitribe.com/en/mag/motion-designer-agent)
- **Adobe After Effects AI Assistant**:
  - Private beta at the June 18, 2026 announcement; an Adobe community beta post on Aug 6, 2026; described as a public beta at IBC 2026.
  - Does natural-language project organisation, writes and debugs expressions, generates images/video with Firefly, and can read a whole project.
  - Free in beta with daily and weekly limits. Adobe says it plans **MCP support** for third-party agents.
  - Not in the shipping AE 26.5 (Sept 2026). **(reported)**
  - Sources: [Adobe HelpX overview](https://helpx.adobe.com/after-effects/desktop/work-with-after-effects-ai-assistant/after-effects-ai-assistant-overview.html), [Adobe community beta post](https://community.adobe.com/announcements-532/new-in-after-effects-beta-after-effects-ai-assistant-1635658), [RedShark IBC2026](https://www.redsharknews.com/after-effects-ai-assistant-ibc2026), [Adobe newsroom June 2026](https://news.adobe.com/news/2026/06/adobe-unveils-major-expansion)
- School of Motion "Motion Mondays", Aug 10, 2026: "After Effects' AI Agent is HERE". AE "can now take spoken instructions and build an editable rig" **(reported)**. — [School of Motion](https://schoolofmotion.com/blog/motion-mondays-august-10-2026)
- School of Motion, May 4, 2026: "Anthropic released Claude connectors for Blender and 50+ Adobe tools" and joined the Blender Development Fund. The same episode featured a vibe-coded browser animation app ("AE clone") built by a Buck animator **(reported)**. — [School of Motion May 4 2026](https://www.schoolofmotion.com/blog/motion-mondays-may-4-2026)
- Filmit MCP: 35 AE actions including keyframes, effects and frame rendering so Claude can check its work **(reported; vendor)**. — [Filmit.io](https://filmit.io/blog/how-to-use-claude-in-after-effects)

**Public demos and creators (videos not watched)**
- YouTube "How I Make Motion Graphics with Claude + After Effects (Full Setup)". The creator reportedly says every motion graphic was built by Claude inside AE: "I directed every single one, but I didn't keyframe any of them." Channel name not visible in snippets **(reported)**. — [YouTube](https://www.youtube.com/watch?v=3AIZ4FT61aw)
- YouTube "Claude Code + After Effects MCP: The Future of Motion Design": setup, a sunrise animation, and Claude writing expressions live **(reported)**. — [videohighlight summary of YouTube YTOwQj-n7ME](https://videohighlight.com/v/YTOwQj-n7ME)
- **Mitchel Dumlao**: YouTube "I Replaced My Entire After Effects Workflow With Claude Code | AI Motion Graphics". A companion description says he has 10+ years as a professional motion designer. Only seen via low-quality aggregator pages, so the claims are unverified **(reported)**. — [aggregator page](https://sales.communityimpact.com/i-replaced-my-entire-after-effects-workflow-with-claude-code-ai-motion-graphics-mitchel-dumlao.html)
- **J.B. Hattori** (note.com, Japanese): hands-on "Exploring the Potential of Claude × After Effects". Concluded it "cannot be used for projects right now, but it shows promise" **(reported)**. — [note.com](https://note.com/alive_swan7139/n/n892cc3b4b7db?hl=en)
- RapidEye launch video: a non-motion-designer had Claude Code design each scene as a webpage, captured transparent 4K ProRes 4444 frames, then **composited and added titles and music in After Effects**. This hybrid is code-generated plates plus AE finishing **(reported)**. — [RapidEye blog](https://rapideye-seo-tools.pages.dev/blog/building-our-launch-video-with-claude/)
- mndr.ai argues Claude is weak at direct AE keyframing, so it builds motion graphics as code instead (GSAP/Remotion), testing 36 ad and social styles **(reported)**. — [mndr.ai](https://mndr.ai/blog/motion-graphics-with-claude/)
- Showcase aggregators say hundreds of Claude-made kinetic-type and showreel videos appeared on X after the Opus 5.5 release (Sept 22, 2026). createmotion.io claims 4,423 indexed videos linking to original posts. These are secondary sites with unverified counts, and most of the work is code-rendered (HTML/Remotion), not AE **(reported)**. — [createmotion.io](https://createmotion.io/), [claudevideo.org](https://claudevideo.org/)
- A Medium post claims an Anthropic "Claude Motion" beta launched on Oct 8, 2026. No Anthropic corroboration was found, so treat it as unverified. — [Medium](https://medium.com/@rohanmistry231/claude-motion-anthropic-just-turned-claude-into-a-motion-designer-079f4d561471)
- Open-source "claude-after-effects-skill" aims to turn code-made video into an editable AE project; howseen-ai/claude-motion-design renders HTML with Playwright and ffmpeg and skips AE entirely **(reported)**. — [awesome-claude-video-skills](https://github.com/zhuyansen/awesome-claude-video-skills), [howseen-ai/claude-motion-design](https://github.com/howseen-ai/claude-motion-design)

**Other pro tools**
- **Blender**: ahujasid/blender-mcp, MIT. A Blender add-on socket server plus a Python MCP server. The official demos are modelling and scene work (low-poly dungeon, beach with Poly Haven assets, scene from a reference image), not motion graphics. Star counts across sources range from 12k to 19k **(reported)**. — [GitHub](https://github.com/ahujasid/blender-mcp)
- **Jitter**: launched a "Jitter MCP" in beta to create or edit animations from Claude/ChatGPT **(reported; launch email)**. — [Sequenzy email archive](https://www.sequenzy.com/api/email-examples/p8vv9ks85853w7mb2lz8qxjj/html)
- **Rive**: an MCP server with 24 bidirectional tools and an AI coding agent in early access **(reported; LottieFiles comparison)**. — [LottieFiles](https://lottiefiles.com/blog/design-guides-and-tips/best-motion-design-tools-ranked-by-use-case)
- **Cavalry**: only community MCP bridges, "not affiliated with Scene Group". Cavalry has reportedly been free for individuals since April 2026 **(reported)**. — [Glama Cavalry Bridge](https://glama.ai/mcp/servers/ew8n22jpan), [Creators Toolbox](https://creatorstoolbox.beehiiv.com/p/canva-makes-cavalry-free-for-everyone)
- **Template automation** (nexrender, Plainly, Templater): rule-based, data-driven rendering of existing AE templates. Nexrender is open-source and CLI on aerender. Plainly is hosted, with an API, CSV/API-driven variants, AE 2026 support, and reported pricing of $69–$649/mo. No source documented an LLM feeding script data into them, though it is technically trivial via their APIs. — [Plainly nexrender review](https://plainlyvideos.com/blog/nexrender-review), [Plainly changelog](https://help.plainlyvideos.com/docs/changelog)

### Inferences
- The tooling to have Claude drive AE exists and is plentiful. Repos with a render-and-look loop (solomondivyananth, Filmit) are the ones most likely to reach premium polish, because the model can see its frames.
- Every credible account (Motion The Agency, AI Tribe, Hattori, mndr.ai) says first-pass agent output is structurally right but weak on timing, easing and taste, so it needs iteration or human polish. "Premium editorial" quality comes from direction and iteration, not one prompt.
- For an earner/earnedits-style reel, the most practical AI-in-AE pipeline is to start from an existing premium AEP template and have Claude, via MCP or ExtendScript, swap text, retime to VO and drive the template (essentially nexrender-style automation with an LLM). Building such reels from scratch by agent is not publicly demonstrated.

### Gaps
- No video was watched. The visual quality of the YouTube demos, Mitchel Dumlao's work and the Higgsfield showcases is unverified.
- Could not identify the channel behind YouTube 3AIZ4FT61aw.
- No public example was found of an agent producing a full editorial reel with 3D props, halftone, paper texture and whip/RGB-split transitions in AE.

---

## Q2. Which motion designers in the editorial/kinetic-type reel niche (Instagram/YouTube/TikTok) use AI tools, and how?

### Takeaway
I found few named, verifiable professional editorial-reel designers who openly document AI-driven AE production. Most visible "Claude motion graphics" creators are developers or marketers rendering via code (Remotion, HyperFrames, HTML), not AE. The named pros and semi-pros with links are below. Social-platform search was not possible from this environment, so this list is thin.

### Cited Findings
- **EarnEdits** (see Q3) sells a "Claude + After Effects — Building Motion Graphics With AI" tutorial in the same subscription library as its viral psychology-edit AEPs. Stated focus: AI-assisted design, expression writing and troubleshooting, and typography and effects in AE. No syllabus or reviews found **(reported)**. — [earnedits product page](https://earnedits.com/product/claude-after-effects-building-motion-graphics-with-ai/), [earnedits AI+AE category](https://earnedits.com/product-category/ai-ae/)
- **Jake in Motion** (Jake Bartlett, a well-known AE educator): his Motion Lab site includes a Claude workflow for "motion designers curious about building their own tools". This is AI for tool-building, not full generation **(reported)**. — [jakeinmotion.com/motion-lab](https://www.jakeinmotion.com/motion-lab)
- **Mitchel Dumlao** (YouTube): claims to have replaced his AE workflow with Claude Code (see Q1) **(reported, unverified)**.
- **Buck animator**: vibe-coded a browser animation app, featured on School of Motion in May 2026 **(reported)**. — [School of Motion](https://www.schoolofmotion.com/blog/motion-mondays-may-4-2026)
- **Motion The Agency**: a pro studio that tested Higgsfield/Astra on a real project (Q1). — [Motion The Agency](https://www.motiontheagency.com/blog/gpt-6-astra-honest-review)
- HyperFrames author (claudecodeformarketers.com): says they never used AE for shippable work, Claude gets graphics "structurally close on the first render", and later work is small tweaks. This is code-rendered, not AE **(reported)**. — [claudecodeformarketers.com](https://claudecodeformarketers.com/blog/motion-graphics-with-hyperframes/)
- Typical AI uses in faceless reel production per vendor guides: AI script, AI voiceover, AI images and characters, auto-captioning. Brand consistency comes from a fixed palette, type and motion style. These are vendor blogs, so treat them as marketing **(reported)**. — [ltx.io](https://ltx.io/blog/faceless-marketing), [framesail.com](https://framesail.com/blog/faceless-reels)

### Inferences
- In this niche, AI is most commonly used upstream (script, VO, image/3D asset generation) and for AE scripting and expressions. The premium look itself still comes from human-built or purchased AE templates.
- The EarnEdits pairing of premium psychology-edit AEPs with a Claude+AE tutorial is the closest match to the user's goal and is worth buying or inspecting.

### Gaps
- Instagram, TikTok, Behance and X could not be searched directly. No verifiable handles were found for editorial-reel designers who openly share AI-in-AE breakdowns, so this needs manual platform search (e.g., #aftereffects plus #claude on IG/X, createmotion.io source links).
- The AI vs human share for any named creator is unknown.

---

## Q3. Who is earner / earnera.co, and which similar creators or template sellers exist? Do they use AI?

### Takeaway
"earnera.co" is a generic PLR/MRR resell-rights digital-products store (5,000+ products) with no evidence of making AE templates. The actual seller of a "Psychology Trick" AE project appears to be **EarnEdits (earnedits.com)**, an AE project-file and tutorial subscription library. The user likely conflated the two names; this should be confirmed against the user's source link. EarnEdits also sells a Claude+AE course, so the seller openly engages with AI. Whether the Psychology Trick edit itself was AI-made is unknown.

### Cited Findings
- **earnera.co**: "Buy Master Resell PLR Digital Products With Resell Rights". Sells 5,000+ MRR/PLR digital products through a one-time "Earning Bundle". No AE reel templates are evident. Unrelated businesses share the "Earnera" name (an Indian magnetic-bracelet biotech, a Zimbabwe gold-mining page). — [earnera.co (search result)](https://www.earnera.co/), [businessabc.net (promotional)](https://businessabc.net/earnera-co-the-ultimate-platform-for-online-earners)
- **EarnEdits**:
  - "A subscription library of After Effects project files, tutorials, and editing resources". AEPs are fully open, not locked templates.
  - Has a Patreon ("EARNEDITS — After Effects Project Files + Tutorials"), X @EarnEdits_com and YouTube @earnedits-com. — [Patreon](https://www.patreon.com/cw/EARNEDITS), [X](https://x.com/EarnEdits_com), [YouTube](https://www.youtube.com/@earnedits-com)
  - **"Psychology Trick" AE project**: "a full timeline built around attention, emotion, and engagement", positioned as a learning tool to reverse-engineer professional edits. Needs specific fonts and effects installed **(reported)**. — [earnedits.com](https://earnedits.com/?p=7223)
  - A pirated "the-psychology-trick.rar" (220.9 MB) appears on GFxtra in an "EarnEdits All Files" repost, which corroborates EarnEdits as the source. Do not use the pirated copy. — [GFxtra listing](https://www.gfxtra31.com/free-video-template-download/adobe-after-effects/2495031-earnedits-all-files.html)
  - A sibling product is "Sales Isn't Logic — It's Psychology (Viral Edit AEP)", an open AE project with editable layers. — [earnedits product](https://earnedits.com/product/sales-isnt-logic-its-psychology-viral-edit-aep/?v=0b3b97fa6688)
  - **AI**: sells the "Claude + After Effects — Building Motion Graphics With AI" tutorial and has an "AI + AE" category. — [earnedits](https://earnedits.com/product/claude-after-effects-building-motion-graphics-with-ai/), [category](https://earnedits.com/product-category/ai-ae/)
  - Third-party "reviews" exist (toughestblogger.com, onlinepreviews.net) but look like affiliate content. No founder identity was found. — [toughestblogger](https://toughestblogger.com/picks/earnedits/), [onlinepreviews](https://onlinepreviews.net/earnedits-review/)
- **Similar AE reel template sellers**:
  - **ena (ena.supply)**: Reel Bundle 01 at $99 (five reels; 1080x1350, 1080x1920 and 1920x1080; no plug-ins), single reels at $29, and a "Grid" loop series at $49 on Awwwards Market. No AI claims found **(reported)**. — [ena.supply Reel Bundle 01](https://ena.supply/motion/reel-bundle-01), [Reel 03](https://ena.supply/motion/reel-03)
  - SupplyMob (Petar Matić, formerly MotionKit): AE showreel templates **(reported)**. — [Contra](https://contra.com/p/R32NMWZB-supply-mob-after-effects-showreel-templates)
  - Generic marketplaces (VideoHive, Motion Array, Envato) have psychology and kinetic-type reel templates, mostly lower-end slideshow styles. — [VideoHive psychology](https://videohive.net/category/after-effects-project-files?term=psychology)
  - Resell-rights reel bundles on Etsy and Scribd are the same PLR ecosystem as earnera.co and low quality. — [Etsy MRR bundle](https://www.etsy.com/listing/4394502713/after-effects-assets-5000-mega-bundle)
  - YouTube tutorials on "minimal faceless reels in After Effects" exist (channels not identified) **(reported)**. — [YouTube](https://www.youtube.com/watch?v=I_-yjFESYAM)

### Inferences
- The "premium psychology reel" look the user wants is most likely the EarnEdits Psychology Trick AEP. Buying the legitimate subscription gives an open project that Claude could drive via an AE MCP (text and VO retiming), which is the fastest route to "exact style".
- earnera.co is probably a red herring, or a reseller of others' products.

### Gaps
- Could not confirm the identity of "earner" or the EarnEdits founder, or whether the Psychology Trick edit was made with AI.
- No named faceless psychology/marketing explainer accounts with premium AE motion were verifiable via search snippets. This needs manual IG/TikTok browsing.

---

## Q4. What do professional motion designers (Reddit, X) say about AI reaching premium motion design quality in 2025–2026?

### Takeaway
No Reddit (r/AfterEffects, r/motiondesign) or X threads surfaced in search, so direct community sentiment is a gap. Trade and press commentary is consistent: AI agents in AE are useful for setup, expressions and simple pieces (titles, logo reveals, transitions), still weak on timing, easing and taste, and need human direction for premium work. Vague prompts produce "slop", while tightly specified short pieces can be publishable.

### Cited Findings
- Visionlabs (2026): "Asking it for 'a 30-second brand video that explains our mission' is still asking for slop. Asking it for 'a 4-second logo bumper that scales from 20% to 100% with a soft overshoot' produces something publishable." **(reported)** — [visionlabs.studio](https://www.visionlabs.studio/blog/ai-motion-design-state-of-the-art)
- A motion design agent-skill defines motion "AI slop" as a matter of "*frequency* and *uniformity*" (the same eases and effects everywhere), not any single effect **(reported)**. — [aiuxplayground](https://aiuxplayground.com/skills/design-motion-principles)
- The AI Tribe: human judgment is still needed on timing ("too stiff", "not good enough") **(reported)**. — [theaitribe.com](https://theaitribe.com/en/mag/motion-designer-agent)
- Motion The Agency: the first pass needed rework, and the second had better timing and easing **(reported)**. — [motiontheagency.com](https://www.motiontheagency.com/blog/gpt-6-astra-honest-review)
- J.B. Hattori: "cannot be used for projects right now, but shows promise" **(reported)**. — [note.com](https://note.com/alive_swan7139/n/n892cc3b4b7db?hl=en)
- A LinkedIn post (via aggregator): the code/Claude approach suits mid-complexity animation; "beyond that, After Effects remains the superior tool" **(reported)**. — [LinkedIn](https://vn.linkedin.com/in/minhtrang0211)
- A guide states that Claude Code "is not a replacement for After Effects or for motion-design judgment" **(reported)**. — [claudecodeguides.com](https://claudecodeguides.com/claude-code-after-effects-extendscript-2026/)
- ProVideo Coalition's After Effects Portal (Aug 2026) rounds up community coverage of the AE AI Assistant and Claude-based motion workflows **(reported)**. — [ProVideo Coalition](https://www.provideocoalition.com/after-effects-portal-august-2026/)

### Inferences
- The industry consensus in late 2026 is "AI as a junior assistant inside AE". Premium editorial quality still depends on a designer's taste, references and iteration, or on starting from a premium human-made template.
- To get close to earner/earnedits quality with AI, give the agent tight specs (exact eases, timings, type pairings, transition recipes), use a render-and-review loop, and vary motion to avoid uniform "slop".

### Gaps
- No Reddit or X threads were retrievable, so direct pro sentiment, upvoted opinions and named practitioners are missing. Manual Reddit and X search is recommended (e.g., "after effects mcp" on r/AfterEffects, "Higgsfield after effects" on X).
- No quantitative data (adoption rates, client acceptance) was found.
