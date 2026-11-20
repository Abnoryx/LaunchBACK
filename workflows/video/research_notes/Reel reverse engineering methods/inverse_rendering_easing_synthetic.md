# Inverse rendering, easing recovery and synthetic data for motion-graphics reels

Research notes, 2026-11-20. Method note: arxiv.org and centre-borelli.github.io (ruptures docs) could not be fetched from this container, because they are not on the network allowlist. Paper details below therefore come from search-result snippets, GitHub READMEs and conference pages, not full-text reads. Statements marked "(inference)" are my own reasoning or background knowledge, not sourced.

## Q1. Differentiable renderers and image losses: what runs on CPU and what needs a GPU?

### Takeaway
Mature differentiable 2D vector renderers (DiffVG and the newer Bézier Splatting) are designed for CUDA and benchmarked on GPUs. Because our WebGL engine is non-differentiable, a differentiable renderer could only act as a *proxy* that mirrors our layer/transform model. For a transform-only layer model (sprite plus affine plus opacity), a plain PyTorch affine-warp compositor, as used by CyberAgent's sprite decomposition, is a simpler and CPU-capable proxy.

### Cited Findings
- **Bézier Splatting** (Liu, Zhou, Zhao, Huang; Clemson and Adobe; NeurIPS 2025) places 2D Gaussians along Bézier curves and rasterises them by Gaussian splatting. The authors report 30x faster forward and 150x faster backward rasterisation than DiffVG for open curves, and more than 10x total training speedup on an A100. It exports SVG. Closed curves are constrained to be convex via a Xing loss, a limitation. — [arXiv 2503.16424](https://arxiv.org/html/2503.16424v4); [NeurIPS 2025 poster](https://neurips.cc/virtual/2025/poster/117178)
- NURBS Splatting (2026) extends the splatting idea into a unified differentiable vector framework. I saw the title only, not the details. — [arXiv 2606.31764](https://arxiv.org/pdf/2606.31764)
- **DiffVG** (2020, older) is hard to install. Its CMake has `DIFFVG_CUDA` ON by default and falls back to a non-CUDA build that requires Thrust, so a CPU build is possible, but I found no maintained CPU guide. PyTorch-SVGRender wraps DiffVG and several methods built on it, and describes itself as under active development. — [LIVE setup / diffvg CMake](https://huggingface.co/spaces/CVPR/LIVE/blob/main/setup.py); [PyTorch-SVGRender](https://github.com/ximinng/PyTorch-SVGRender); [dpy5 note on install difficulty](https://pypi.org/project/dpy5/)
- **DiffBMP** (a differentiable renderer with bitmap primitives) requires Linux x86_64 and an NVIDIA GPU with compute capability 8.6 or higher. Not usable on CPU. — [pydiffbmp on PyPI](https://pypi.org/project/pydiffbmp/)
- **nvdiffrast** relies on GPU hardware rasterisation (OpenGL/CUDA). Treat it as GPU-only. It is also a 3D-mesh tool, not something needed for 2D layers. — [nvdiffrast README](https://raw.githubusercontent.com/NVlabs/nvdiffrast/253ac4fcea7de5f396371124af597e6cc957bfae/README.md); [paper](https://arxiv.org/pdf/2011.03277)
- **PyTorch3D** does have a CPU mesh-rasterisation path. A third-party paper reports its own renderer as 5x faster forward and 30x faster backward than PyTorch3D on CPU, which implies PyTorch3D's CPU path is slow. — [Approximate Differentiable Rendering with Algebraic Surfaces](https://arxiv.org/pdf/2207.10606)
- **CyberAgent sprite-decompose** (ECCV 2024, MIT licence) parameterises each sprite as a static texture plus "affine matrices and opacity", fitted to the raster video by gradient optimisation. The example config runs 60,000 iterations. `device` accepts `cuda` or `cpu`, but the tested setup is CUDA 11.3. — [GitHub](https://github.com/CyberAgentAILab/sprite-decompose)

### Inferences
- (inference) For After Effects-style layers whose shapes are mostly static and whose transforms are animated, the most useful differentiable proxy is `torch.nn.functional.affine_grid` plus `grid_sample` per layer, with alpha "over" compositing. This is differentiable, runs on CPU at 360p, and maps one to one onto position/scale/rotation/opacity keyframes. Fit on the proxy, then confirm against the WebGL render.
- (inference) Image losses: LPIPS (VGG/AlexNet backbone), DISTS and SSIM are all plain PyTorch nets or ops and run on CPU. At 360p, a few hundred ms per frame pair on 4 cores is plausible for LPIPS-Alex. SSIM, L1 and edge losses are far cheaper. For black-box fitting, cheap losses (masked L1/L2 on downscaled frames, IoU of alpha masks, centroid/bbox distance) are usually enough. LPIPS adds little when the renderer and target share the same assets. I found no benchmark of LPIPS/DISTS CPU speed, so this needs measuring.

### Gaps
- I found no maintained, documented CPU build of DiffVG, and no CPU timings for Bézier Splatting. Its code is CUDA, as far as the search snippets showed.
- I found no CPU throughput numbers for LPIPS, DISTS or the piq library.

## Q2. Gradient-free fitting for a black-box renderer: optimisers, evaluation budgets, coarse-to-fine, masked losses

### Takeaway
CMA-ES (pycma, or via nevergrad/Optuna) is the standard choice for black-box inverse rendering of up to about 100 parameters. Published budget guidance runs from about 10·D to 1000·D evaluations. With our 0.5-5 s/frame renderer, that only works if parameters are fitted per layer and per segment (D roughly 2-10), on a few sampled frames and at low resolution, or against a cheap proxy renderer.

### Cited Findings
- **FIDE** (Feature-Guided Diffusion for Non-Differentiable Inverse Rendering, 2026 preprint) treats the renderer as a black box and pairs a feature-conditioned diffusion prior with CMA-ES to refine the search space. Because of CMA-ES's quadratic memory complexity, the authors note it is best for small-to-medium problems, up to about 100 parameters. — [arXiv 2607.17411](https://arxiv.org/html/2607.17411v1)
- Nevergrad's docs say CMA is excellent when noise is low and the budget is large, for example 1000 x the dimension. NGOpt is the default "wizard" optimiser. — [nevergrad docs](https://facebookresearch.github.io/nevergrad/optimization.html)
- At low budgets on BBOB, NGOpt mainly uses CMA, Cobyla and (1+1)-type sampling with metamodels in sequential, low-dimensional, noise-free settings. — [Optimizing with Low Budgets, arXiv 2310.00077](https://arxiv.org/pdf/2310.00077)
- A 2026 benchmark compared pycma IPOP-CMA-ES and NGOpt at budgets from 10·D to 1000·D, in dimensions 4/7/15/30. It also notes that nevergrad 1.0.12's CmaFmin2 calls pycma without a seed, so results are not reproducible unless the seed is pinned. — [Adaptive Multi Mode, arXiv 2611.06879](https://arxiv.org/pdf/2611.06879v1)
- Prior inverse-procedural pipelines with non-differentiable generators used: Powell (SciPy) for continuous parameters plus GP Bayesian optimisation (GPyOpt) for discrete ones (SVBRDF, 2022, older); genetic algorithms for non-differentiable tree generators (2023-2024); or a learned differentiable neural proxy of the non-differentiable procedure (2022, older). — [Inverse Procedural SVBRDF, ACM](https://dl.acm.org/doi/10.1145/3502431); [arXiv 2310.13373](https://arxiv.org/pdf/2310.13373); [Node Graph Optimization Using Differentiable Proxies, arXiv 2207.07684](https://arxiv.org/pdf/2207.07684)
- Sprite decomposition speeds up its (gradient) optimisation by initialising sprite parameters from a pre-trained video object segmentation model, plus user annotation on single frames, and by assuming static textures. Good initialisation is the main lever on cost. — [ECCV 2024 paper](https://www.ecva.net/papers/eccv_2024/papers_ECCV/papers/08402.pdf); [arXiv 2408.03923](https://arxiv.org/abs/2408.03923)

### Inferences
- (inference) Budget arithmetic: one CMA-ES fit of D=6 (e.g. x, y, scale, rotation, opacity, timing offset) at 100·D = 600 evaluations. At 1 s per frame, scoring 3 frames per candidate takes about 30 min per fit. That is too slow per keyframe segment. Recommended decomposition:
  1. **Measure, don't search, where possible.** Track each layer (mask/centroid/bbox, optical flow, or template matching with OpenCV) in the target video to get per-frame transform estimates directly. This needs no rendering.
  2. **Fit keyframes and eases from those 1D tracks** (Q3), which is pure numerics and takes milliseconds.
  3. **Use the renderer only for verification and residual refinement:** render the candidate once, compute a per-layer masked loss, and run CMA-ES or Nelder-Mead only on the few parameters with large residuals. Warm-start from the measured values with small sigma, at 10-30·D evaluations.
  4. **Batch evaluations.** pycma's ask/tell gives population-size (about 4 + 3 ln D, so about 9 for D=6) candidates per generation. Render them in parallel across 4 Chromium tabs or workers.
  5. **Coarse to fine:** fit at 90p-180p on keyframe-adjacent frames, then confirm at 360p. For timing, search on a frame-index grid first, then refine continuously.
- (inference) Optuna's TPE or CMA sampler and nevergrad's NGOpt both wrap the same ideas. pycma directly gives the most control (bounds, ask/tell, seeding). Bayesian optimisation (GP/TPE) is attractive when D ≤ about 10 and each evaluation is expensive (more than 1 s), because it needs fewer evaluations (often 50-200) than CMA-ES.
- (inference) Per-element masked losses: compute the loss only inside the union of the target layer mask and the rendered layer mask (dilated), with other layers hidden in the candidate render where the engine allows. This turns a joint D·L problem into L independent D problems.

### Gaps
- I found no published evaluation counts specifically for fitting 2D layer transforms or keyframes against a black-box motion-graphics renderer. The numbers above are generic BBOB-style guidance.
- I could not read the FIDE paper for its actual evaluation counts (arXiv was blocked).

## Q3. Prior work on reverse-engineering motion graphics, vector animation and UI animation from video

### Takeaway
The closest prior art is **Motion Vectorization** (SIGGRAPH Asia 2023: video to SVG motion program), **Fast Sprite Decomposition** (ECCV 2024: video to sprites with affine and opacity per frame, MIT code, Crello Animation dataset), and **OmniLottie** (CVPR 2026: a 4B VLM that includes a video-to-Lottie task, Apache-2.0 code but non-commercial data). VLM-to-code benchmarks from 2025-2026 (Animation2Code) find that current VLMs reproduce appearance well but temporal dynamics poorly. Timing and easing therefore need classical tracking and fitting, not just an LLM.

### Cited Findings
- **Editing Motion Graphics Video via Motion Vectorization and Transformation** (Zhang, Ma, Wu, Ritchie, Agrawala; ACM TOG / SIGGRAPH Asia 2023, older). A pipeline converts motion-graphics video into an SVG motion program that renders in browsers and is editable in SVG editors. A program-transformation API supports retiming to music beats, motion textures and collision-preserving appearance changes. — [Roblox publication page](https://about.roblox.com/publications/editing-motion-graphics-video-via-motion-vectorization-and-transformation); [arXiv 2309.14642](https://arxiv.org/pdf/2309.14642); [SIGGRAPH Asia 2023 entry](https://asia.siggraph.org/2023/index.html%3Fpost_type=page&p=14494&id=papers_207&sess=sess152.html)
- **Fast Sprite Decomposition from Animated Graphics** (Suzuki, Kikuchi, Yamaguchi; CyberAgent; ECCV 2024). Optimisation-based fitting of sprite parameters to raster video, with static textures and a texture prior. Initialisation comes from video object segmentation plus single-frame user annotations. The authors introduce the **Crello Animation** dataset and sprite-quality metrics. Code is MIT, the dataset is on Hugging Face as `cyberagent/crello-animation`, and output is a texture PNG plus affine matrices and opacity per sprite. — [project page](https://cyberagentailab.github.io/sprite-decompose/); [GitHub](https://github.com/CyberAgentAILab/sprite-decompose); [ECCV paper](https://www.ecva.net/papers/eccv_2024/papers_ECCV/papers/08402.pdf)
- **MG-Gen: Single Image to Motion Graphics Generation** (2025, the same CyberAgent line) appeared in the same search. I saw the title only. — [arXiv 2504.02361](https://arxiv.org/pdf/2504.02361)
- **OmniLottie** (OpenVGLab, CVPR 2026) is a multimodal generator that outputs Lottie JSON via parameterised Lottie tokens. Tasks include video-to-Lottie: MMLottieBench has 150 video-to-Lottie samples per split (real and synthetic). The model is 4B parameters (about 8.5 GB), needs about 15.2 GB of GPU memory at inference, and takes about 8-133 s per generation. Weights were released 2026-03-03. The code is Apache-2.0, but the MMLottie-2M dataset is CC BY-NC-SA 4.0 (non-commercial). — [GitHub](https://github.com/OpenVGLab/OmniLottie); [HF dataset](https://huggingface.co/datasets/OmniLottie/MMLottie-2M); [HF model](https://huggingface.co/OmniLottie/OmniLottie)
- In OmniLottie's comparisons on video-to-Lottie, Qwen2.5-VL and Gemini reportedly fail to produce valid outputs, and GPT-5 gives occasional low-quality conversions. This is from a search summary of the paper; I could not verify the numbers. — [arXiv 2603.02138](https://arxiv.org/html/2603.02138v1); [paper notes](https://en.papernotes.org/CVPR2026/video_generation/omnilottie_generating_vector_animations_via_parameterized_lottie_tokens/)
- **LottieGPT** (2026) tokenises vector animation for autoregressive generation, using the LottieAnimation-660K dataset. It is generative, not reconstruction from video. — [arXiv 2604.11792](https://arxiv.org/html/2604.11792v1)
- **VAnim** (ICML 2026) is text-to-SVG animation, modelling animation as sparse state updates on a persistent SVG DOM, with the SVGAnim-134k benchmark. It is generative, not from video. — [arXiv 2605.01517](https://arxiv.org/abs/2605.01517)
- **Animation2Code** (Ji, Mudunuri, Chan, Suhr; UC Berkeley; NeurIPS 2026) has 1,069 web-animation videos paired with HTML/CSS/JS. VLMs reach up to 100% execution and up to 0.84 appearance similarity, but temporal fidelity is the weak point. — [NeurIPS poster](https://neurips.cc/virtual/2026/poster/138932); [project](https://anya-ji.github.io/animation2code-website); [arXiv 2606.28593](https://arxiv.org/abs/2606.28593)
- Related video-to-webpage benchmarks: IWR-Bench (ICLR 2026, interactive webpage reconstruction from interaction video) and WebVR (2026, MLLM judge comparing the render against the reference video). — [IWR-Bench](https://arxiv.org/html/2509.24709v3); [WebVR](https://arxiv.org/html/2603.13391)
- Commercial "video to Lottie" converters such as EasyLottie produce image-sequence Lotties (raster frames plus timing JSON), not editable layers or keyframes. — [EasyLottie blog](https://www.easylottie.com/en/blog/videos-to-lottie); [AnyGen](https://www.anygen.io/showcase/mp4-to-lottie/index.html)
- Older video-layering background: Deformable Sprites (2022) and MarioNette (2021). — [arXiv 2204.07151](https://arxiv.org/pdf/2204.07151); [arXiv 2104.14553](https://arxiv.org/pdf/2104.14553)

### Inferences
- (inference) Best fit for our pipeline: sprite-decompose's representation (static texture plus per-frame affine and opacity) is effectively an After Effects precomp layer with baked transforms. Running it, or our own cheaper tracker, gives per-frame transform tracks that Q3-style keyframe and ease fitting turns into an AE-like keyframe list. Motion Vectorization is the same idea with an SVG program output.
- (inference) OmniLottie could serve as an optional GPU-rented "first guess" for layer structure. However, its non-commercial dataset licence, its 15 GB GPU requirement, and the weak temporal fidelity reported for VLMs make it unsuitable as the core of a CPU pipeline.
- (inference) An LLM/VLM is useful for semantic labelling (what this layer is, which template it maps to). Numbers such as timing and eases should come from tracking plus fitting, which Animation2Code supports.

### Gaps
- **"Tutrace 2025" could not be found** under that name in two searches. It may be misspelled or unindexed. The caller should supply a link.
- I found no 2025 paper specifically on kinetic-typography reverse engineering.
- I found no numeric video-to-Lottie results for OmniLottie, because arXiv full text was blocked.

## Q4. Easing and keyframe recovery from tracked 1D/2D trajectories

### Takeaway
Use a two-stage approach: (1) segment each tracked channel into motion and hold intervals with change-point detection (ruptures: Pelt/Dynp with a piecewise-linear or slope cost) or Ramer-Douglas-Peucker; (2) normalise each segment to [0,1]x[0,1], fit a CSS/AE-style cubic Bézier ease by least squares, then snap it to the nearest named ease when the error is under tolerance. The y-control points are linear in the least-squares problem once t is solved per sample by Newton iteration.

### Cited Findings
- **ruptures** (BSD-2-Clause, maintained badge, news through 2024) provides exact and approximate offline change-point detection for parametric and non-parametric models, e.g. `rpt.Pelt(model="rbf").fit(signal).predict(pen=10)`. — [GitHub](https://github.com/deepcharles/ruptures)
- For cubic-Bézier fitting, the inner control points' vertical coordinates enter linearly, so they can be solved by one linear least-squares step. Mapping each sample x back to curve parameter t (x is cubic in t) is done well with Newton-Raphson. — [Physics Forums thread](https://www.physicsforums.com/threads/data-fitting-with-bezier-curve.166391/); [MATLAB Cubic Bezier LSQ](https://fr.mathworks.com/matlabcentral/fileexchange/15542-cubic-bezier-least-square-fitting)
- A worked example: easeOutCubic fits as `cubic-bezier(0.33, 1, 0.67, 1)` within 0.5%, with a worst gap of 0.2 points of travel. Standard Penner eases are well approximated by CSS cubic-beziers. — [vawe.dev easeOutCubic](https://vawe.dev/easing/ease-out-cubic)
- Keyframe-sampled data at evenly spaced times keeps least-squares (B-spline) systems well conditioned with uniform knots. — [Geometric Tools, B-spline LSQ fit](https://www.geometrictools.com/Documentation/BSplineCurveLeastSquaresFit.pdf)

### Inferences
- (inference) Recommended algorithm per channel (x, y, scale, rotation, opacity), taken from my background knowledge, not sources:
  1. Smooth lightly (Savitzky-Golay, window 5) and compute velocity. Mark holds where |v| < ε for 2 or more frames. Segment the rest with ruptures Dynp/Pelt (`model="linear"` or `"clinear"` on a time regressor, or `"l2"` on velocity), with a BIC-like penalty; or with RDP on (t, value) at tolerance about 0.5-1 px.
  2. Per segment, normalise time u=(t−t0)/(t1−t0) and progress p=(v−v0)/(v1−v0). Fit `cubic-bezier(x1,y1,x2,y2)` by minimising Σ(p_i − B_y(t(u_i)))² over (x1,x2) on a grid in [0,1]² and solve y1,y2 linearly, or use scipy `least_squares` on all four. Allow y outside [0,1] for overshoot/back eases.
  3. Snap: compare the RMSE of the free fit against a library (linear, AE "Easy Ease" ≈ 33% influence, CSS ease/ease-in/ease-out/ease-in-out = (0.25,0.1,0.25,1)/(0.42,0,1,1)/(0,0,0.58,1)/(0.42,0,0.58,1), Penner quad/cubic/quart/quint/expo/back/elastic/bounce). Pick the named ease if its RMSE is within about 1.2x the free fit and under an absolute threshold. Elastic and bounce are not single Béziers: detect them by velocity sign changes and multiple local extrema.
  4. Keyframe reduction: merge adjacent segments when a single ease fits both within tolerance (bottom-up merging, as in ruptures BottomUp).
  5. 2D motion paths: fit the spatial path (AE spatial Bézier) separately from the temporal ease (speed graph) by reparameterising on arc length.
- (inference) Accuracy at 30 fps: a 10-frame (0.33 s) segment gives about 9 interior samples, enough to separate ease-in from ease-out and linear robustly, but marginal for separating cubic from quart, or AE influence values within about 10%. Keyframe times can only be resolved to ±0.5 frame unless sub-frame interpolation of the change point is done, e.g. by intersecting fitted segments. Motion blur in the source helps velocity estimation. Codec and scaling noise of 0.25-0.5 px matters mainly for slow segments.
- (inference) The synthetic-template loop (Q5) is the right way to measure this accuracy empirically: render known eases at 30 fps through our engine, then run the extractor and report confusion matrices.

### Gaps
- I could not read the ruptures docs (host blocked), so the exact cost names (`CostLinear`/`CostCLinear`) and complexity notes are unconfirmed here. From background knowledge, Dynp is O(K·n²) exact and Pelt is about O(n) on average.
- I found no published study of easing-classification accuracy versus frame rate. This needs our own synthetic benchmark.
- I found no maintained Python library dedicated to fitting animation easing curves. It appears to be bespoke code (about 100 lines with numpy/scipy).

## Q5. Synthetic labelled data from parameterised templates

### Takeaway
Domain randomisation from procedural templates is an established way to train detectors and classifiers without hand labels. In the graphics domain the clearest analogues are document-layout synthesis (DocLayout-YOLO's DocSynth-300K, RanLayNet, Document Domain Randomization) and CyberAgent's Crello-derived animation data. Our own template engine is an ideal generator: every render carries exact layer, transform, keyframe, ease and transition labels for free.

### Cited Findings
- **DocLayout-YOLO** (2024) pretrains on the synthetic DocSynth-300K, generated by treating document synthesis as 2D bin packing. The code was released in October 2024. — [GitHub](https://github.com/opendatalab/DocLayout-YOLO)
- **RanLayNet** (2024) is a synthetic layout dataset with automatically generated labels. The authors report that models trained on it excel at domain adaptation and generalisation. — [arXiv 2404.09530](https://arxiv.org/abs/2404.09530v2)
- **Document Domain Randomization** (2021, older) randomises page appearance and content to train layout extraction without hand annotation, borrowing robotics-style domain randomisation. — [arXiv 2105.14931](https://arxiv.org/html/2105.14931)
- A stochastic-template generator, whose templates vary distributional parameters to capture commonality across document types, is the closest match to "procedural templates" (2021, older). — [arXiv 2111.06016](https://arxiv.org/pdf/2111.06016v1)
- **Crello Animation** (CyberAgent, 2024) is a dataset of animated designs from an online design service, used to evaluate sprite decomposition. It is a candidate real-ish validation set for our extractors. — [GitHub](https://github.com/CyberAgentAILab/sprite-decompose); [project page](https://cyberagentailab.github.io/sprite-decompose/)
- **OmniLottie MMLottie-2M** includes rendered-video/Lottie pairs, with real and synthetic splits. It is useful for research evaluation only, given CC BY-NC-SA. — [HF dataset](https://huggingface.co/datasets/OmniLottie/MMLottie-2M)

### Inferences
- (inference) Generator design: sample template, layer count, assets (fonts/colours/images), per-layer keyframe count, keyframe times, ease class (from the snap library above, plus random free Béziers), transition type, and camera/shot params. Render at 360p and 30 fps through the real WebGL engine (so the domain gap is zero for our own style). Augment with re-encoding (H.264 at various CRF), rescaling, frame-rate conversion (24/25/60 to 30), slight blur and colour shift, to mimic downloaded reels.
- (inference) CPU budget: at 0.5-5 s/frame, 4 workers produce roughly 3,000-30,000 frames per hour. For ease classification, train on *trajectories*, not pixels: render once, track, and store the 1D curves. Better still, generate the curves analytically with simulated tracking noise (Gaussian jitter of 0.2-0.5 px, quantisation, dropped frames), giving millions of examples in seconds. Use renders only to calibrate the noise model.
- (inference) Small CPU classifiers: a 1D-CNN or gradient-boosted trees (LightGBM) on resampled normalised progress curves (e.g. 32 samples) plus velocity features is ample for ease class. For shot type and transition type, use frozen small image backbones (MobileNetV3, or CLIP ViT-B/32 embeddings computed on CPU) with a logistic-regression or MLP head, trained on synthetic clips and validated on a small hand-labelled real set.
- (inference) The same generator gives a closed-loop benchmark for Q2-Q4: render with known params, run the extractor and fitter, and report keyframe-time error (frames), ease-class accuracy, and transform RMSE.

### Gaps
- I found no 2024-2026 paper on synthetic data specifically for shot-type, transition-type or easing classifiers in motion graphics. The search returned only document-layout examples.
- My search found no UI-screenshot synthetic-data examples. A follow-up search would be needed.
