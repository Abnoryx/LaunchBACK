# Reel reverse engineering: cuts, tracking, layers, archetype matching

Scope: methods for breaking down short-form After-Effects-style motion-graphics reels (1080x1920, 30-60 s, kinetic text, 2.5D camera, 3D props, whip pans, flashes, glitches, lens blur, wipes) on a 4-core Linux CPU container with no GPU.

Research conditions (date 2026-11-20): arxiv.org and github.io project pages **could not be fetched** from this session (DNS blocked by the network allowlist). arXiv facts below come from search-result snippets of arXiv/CVF pages. GitHub READMEs could be fetched. Items marked **[prior knowledge, unverified]** are from my training data and were not re-checked here. Treat them as leads and verify before relying on them. Container facts checked locally: `nproc` = 4; `onnxruntime 1.29.0` is installed; OpenCV (`cv2`), torch and scenedetect are **not** installed.

Sizing used throughout: a 45 s reel at 30 fps is about 1,350 frames. Most models below run on downscaled frames, so 1080x1920 is rarely the working resolution.

## Q1. Shot boundary and transition detection/classification (TransNetV2, AutoShot, PySceneDetect, 2024-2026 models; gradual/stylised transitions)

### Takeaway
TransNetV2 (MIT licence, PyTorch and TF inference) is still the practical CPU default. It has a separate "all-frames" head for gradual transitions. It finds stylised transitions roughly, but places their boundaries poorly and does not classify them. Newer 2026 work (OmniShotCut, TransVLM) targets transition ranges and types, but could not be verified here. For AE-style reels, the most reliable route is to combine TransNetV2 or PySceneDetect candidates with cheap hand-written per-frame signals, each tuned to one transition type in the kit.

### Cited Findings
- TransNetV2 repo: MIT licence; inference provided in both TensorFlow (`inference/`) and PyTorch (`inference-pytorch/`); no training needed to detect shots. F1 from the authors' re-evaluation: ClipShots 77.9, BBC Planet Earth 96.2, RAI 93.9. The README gives no CPU/GPU speed figures. — [GitHub soCzech/TransNetV2](https://github.com/soCzech/TransNetV2)
- TransNetV2 has two outputs: a single-frame prediction for hard cuts and an all-frame prediction for gradual transitions. CineTrans (2025) uses the all-frame head and reports it handles gradual transitions better than PySceneDetect. — [CineTrans arXiv 2508.11484](https://arxiv.org/pdf/2508.11484)
- AutoShot (CVPRW 2023, **older source**): found by neural architecture search on a short-video dataset ("SHOT"); beats TransNetV2 by 4.2% F1 on SHOT. Gradual transitions are about 30% of shots in SHOT and caused 54% of AutoShot's misses, because they have low inter-frame difference. PySceneDetect scores F1 < 0.6 on SHOT. — [AutoShot CVPRW 2023](https://openaccess.thecvf.com/content/CVPR2023W/NAS/papers/Zhu_AutoShot_A_Short_Video_Dataset_and_State-of-the-Art_Shot_Boundary_Detection_CVPRW_2023_paper.pdf); [arXiv 2304.06116](https://arxiv.org/pdf/2304.06116)
- OmniShotCut (2026 preprint): PySceneDetect, TransNetV2 and AutoShot reach range-based F1 of 0.75-0.82, but TransNetV2 and AutoShot "usually choose the start frame in the middle of the dissolve or fading effects". AutoShot scores only 0.252 on the paper's Transition IoU metric. OmniShotCut uses a shot-query transformer (search snippet only; full page blocked). — [OmniShotCut arXiv 2604.24762](https://arxiv.org/html/2604.24762v1)
- TransVLM (2026, project page): a vision-language framework and benchmark for "detecting any shot transition". It compares PySceneDetect, TransNetV2, AutoShot and VLMs using a temporal tolerance of 0-0.5 s, segment F1, frame F1, absolute boundary error and real-time factor (search snippet only; page blocked). — [TransVLM project page](https://chence17.github.io/TransVLM/)
- A 2025 preprint reports "faster than real-time" detection of shot boundaries, sampling structure and dynamic keyframes (snippet only; method details not verified). — [arXiv 2502.09202](https://arxiv.org/pdf/2502.09202)
- [prior knowledge, unverified] TransNetV2 resizes frames to 48x27 and processes 100-frame windows. That makes it cheap on CPU: a 1,350-frame reel likely takes seconds to tens of seconds, mostly spent decoding with ffmpeg. PySceneDetect (BSD-3) offers ContentDetector (HSV delta), AdaptiveDetector, ThresholdDetector (fades to/from black) and HashDetector. It runs at or above real time on CPU, especially with frame downscaling.

### Inferences
- Stylised AE transitions break the assumptions behind every learned shot boundary detector (SBD). Expected behaviour per transition:
  - **Whip pans:** heavy directional blur over 3-8 frames. Usually flagged as a gradual transition. Detectable directly as a spike in mean optical-flow magnitude plus loss of high-frequency energy, with a dominant flow direction.
  - **White flashes:** detectable as a spike in mean luminance toward 1.0 (frame-mean threshold), the same way PySceneDetect's ThresholdDetector handles fades.
  - **Glitches/RGB split:** spikes in the difference between colour channels and in horizontal-band shifts. Learned SBDs often report them as hard cuts.
  - **Lens-blur transitions:** a dip in Laplacian variance (sharpness) that recovers on a new frame.
  - **Wipes:** a moving boundary between two static images. Visible in a per-column or per-row difference map.
  - **Push/slide:** global translation fits a homography or similarity with low residual.
- Recommended CPU pipeline. Total well under 2 minutes per reel on 4 cores; the main cost is decoding at reduced size (e.g. ffmpeg `-vf scale=270:480`).
  1. Run TransNetV2 (PyTorch or ONNX export) for candidate boundaries.
  2. Run PySceneDetect Content and Threshold detectors as a second opinion.
  3. Compute per-frame signals: luminance mean, Laplacian variance, colour-channel misalignment, DIS-flow magnitude/direction, global-motion fit residual, SSIM to the previous frame.
  4. Classify each candidate window with rules or a tiny classifier trained on the transition kit itself.
- The project's own engine can render synthetic training data: every transition in `library/style/` (whip, flash, lens blur, RGB split, wipes) can be rendered between random shots to produce labelled clips. Fine-tuning TransNetV2 or training a small classifier on these clips is a GPU-light task.
- Frame-accurate cut timing matters (the ROADMAP measures cut timing). The OmniShotCut finding that TransNetV2/AutoShot land mid-dissolve means boundary frames from SBD models should be refined with the signal curves, not taken as-is.

### Gaps
- No verified CPU timing for TransNetV2 or AutoShot. Benchmark locally (torch is not installed in the container).
- OmniShotCut and TransVLM code availability, licence, model size and per-type accuracy could not be fetched (arXiv/github.io blocked).
- I found no benchmark that specifically covers motion-graphics/synthetic transitions such as whip, glitch or lens blur.
- AutoShot weights' licence was not verified.

## Q2. CPU optical flow, point tracking, 2D camera fitting, parallax layers, 3D camera solving

### Takeaway
For flat AE layers, classical CPU methods are enough and fast: OpenCV DIS flow or sparse LK/ORB features, then RANSAC fits of a per-frame similarity (pan/zoom/roll) or homography, then clustering of flow residuals into parallax layers. Learned point trackers (CoTracker3, TAPNext, LocoTrack) are benchmarked only on GPU. On CPU they are feasible only for a few hundred points on downscaled frames. Feed-forward 3D solvers (VGGT) need a GPU, and their licences are mostly non-commercial. They add little for 2.5D AE moves, which are better modelled as per-layer 2D transforms plus a z-ordered fake camera.

### Cited Findings
- NeuFlow v2 (2024): over 20 FPS at 512x384 on a Jetson Orin Nano (edge GPU); claims a 10-70x speedup over state-of-the-art methods. No CPU numbers found. — [NeuFlow v2 arXiv 2408.10161](https://arxiv.org/abs/2408.10161); [HF papers](https://huggingface.co/papers/2408.10161)
- SEA-RAFT (2024): latency 70.96 ms (M) and 108.0 ms (L) at Sintel scale. The snippet does not state the hardware (likely a GPU). — [SEA-RAFT arXiv 2405.14793](https://arxiv.org/pdf/2405.14793)
- CoTracker3 (Oct 2024): drops global matching and uses an MLP on correlation features; about 27-30% faster than LocoTrack, the fastest previous tracker (GPU). — [CoTracker3 arXiv 2410.11831](https://arxiv.org/html/2410.11831v1)
- TAPNext (ICCV 2025): tracks per frame (online), whereas CoTracker3 needs at least 8 frames to produce an output and LocoTrack-B needs the whole video. — [TAPNext ICCV 2025](https://www.openaccess.thecvf.com/content/ICCV2025/papers/Zholus_TAPNext_Tracking_Any_Point_TAP_as_Next_Token_Prediction_ICCV_2025_paper.pdf)
- TAPNext++ (2026 preprint) H100 throughput and latency:

  | Model | 256 points | 1024 points |
  |---|---|---|
  | CoTracker3 online | 102 FPS, 80 ms latency | 45 FPS, 177 ms |
  | LocoTrack-B windowed | 452 FPS, 2,210 ms latency | 124 FPS, 8,000 ms |
  | TAPNext per-frame | 189 FPS, 5.3 ms latency | ~182 FPS |

  All GPU figures. — [TAPNext++ arXiv 2604.10582](https://arxiv.org/html/2604.10582v1)
- VGGT (CVPR 2025): feed-forward camera/depth/points; 0.2 s on one H100 for the paper's test, versus about 9 s for MASt3R with 10 frames (global alignment). The camera head is about 5% of runtime. Memory grows with frame count; one secondary source says about 60 frames fit on a 24 GB RTX 4090. — [VGGT CVPR 2025](https://openaccess.thecvf.com/content/CVPR2025/papers/Wang_VGGT_Visual_Geometry_Grounded_Transformer_CVPR_2025_paper.pdf); [toolchain blog (secondary)](https://builderai.tools/blog/gaussian-splatting-and-3d-reconstruction-toolchain)
- Licences (secondary source, verify): DUSt3R and MASt3R are CC BY-NC-SA 4.0. VGGT's repo licence was updated to allow commercial use (excluding military), but only for the `VGGT-1B-Commercial` checkpoint; the original VGGT-1B weights stay non-commercial. — [toolchain blog](https://builderai.tools/blog/gaussian-splatting-and-3d-reconstruction-toolchain)
- MegaSaM combines feed-forward depth with optimisation-based refinement for casual dynamic video. A CVPR 2026 roundup says newer feed-forward 4D models are about 100x faster than MegaSaM. No absolute runtime or licence was found. — [Best of CVPR 2026 (digitalsense)](https://www.digitalsense.ai/blog/best-of-cvpr-2026)
- VGGT-SLAM 2.0 (2026) applies feed-forward reconstruction in real time on GPU. — [arXiv 2601.19887](https://arxiv.org/html/2601.19887v1)
- [prior knowledge, unverified] OpenCV DISOpticalFlow (preset ULTRAFAST/FAST/MEDIUM) runs at hundreds of FPS at low resolution on one CPU core (original DIS paper, ECCV 2016, **older**). Farneback is several times slower. `cv2.estimateAffinePartial2D` (4-DoF similarity) and `cv2.findHomography` with RANSAC/USAC take milliseconds per frame. Licences: OpenCV Apache-2.0; CoTracker code CC-BY-NC 4.0; TAPNext/TAPIR (google-deepmind/tapnet) Apache-2.0; RAFT BSD-3; SEA-RAFT BSD-3; NeuFlow v2 Apache-2.0.

### Inferences
- **2D camera from flat layers (recommended, CPU, about 1-3 min per reel):**
  1. Downscale to about 540x960.
  2. Compute DIS flow (or Shi-Tomasi corners + LK).
  3. Fit a similarity with RANSAC. Decompose it into tx, ty, scale (zoom) and rotation (roll); accumulate within each shot and smooth.
  4. Use a homography only when perspective tilt is visible (2.5D cards rotated in Y).
  5. Fit the result to AE-style keyframes plus easing curves; the library's eases can be matched by least squares.
- **Parallax layers:**
  1. After fitting the dominant (background) motion, compute residual flow.
  2. Cluster per-pixel or per-feature motion with RANSAC multi-model fitting (sequential RANSAC or J-linkage) or k-means on [tx, ty, scale] over superpixels. Each cluster is a layer with its own 2D transform.
  3. Relative parallax ratios approximate z-depth for a 2.5D camera rebuild (ratio of layer translation to camera translation ~ 1/z).
- **Failure modes on graphic content:**
  - Flat colour fills have no texture, so flow is zero or ambiguous inside them and only edges carry signal.
  - Kinetic text animates per character, so it violates the rigid-layer assumption.
  - Heavy motion blur and lens blur break brightness constancy.
  - Flashes break photometric matching.
  - Paper texture and film grain overlays that stay fixed to the screen bias the estimate toward zero motion.
  - Mitigations: mask out known screen-locked overlays; use edge-weighted features (corners on text); exclude transition windows found in Q1; use temporal smoothing and robust losses.
- **Learned trackers on CPU:** CoTracker3 offline at reduced resolution (e.g. 384x512, a few hundred points) is plausibly minutes per short shot on 4 cores. That is acceptable as an occasional check, not as the default.
- **3D solvers:** VGGT, MASt3R and MegaSaM assume a real rigid 3D scene with real perspective. AE 2.5D scenes are flat cards in a perspective camera, and 3D props are rendered separately. Feed-forward solvers can still recover the AE camera roughly when several cards are visible at different depths, but GPU cost and licences make this a low-priority experiment. A 2D-per-layer decomposition is closer to how the scene was authored and maps directly onto AE edit lists.

### Gaps
- No published CPU timings for NeuFlow v2, SEA-RAFT, CoTracker3, TAPNext or LocoTrack. Local benchmarking is needed.
- LocoTrack licence and MegaSaM licence were not verified.
- I found no study of flow or trackers on synthetic motion graphics or text.

## Q3. Layer decomposition and object masks (SAM 2/2.1, EfficientTAM, SAM 3, omnimatte family, video matting)

### Takeaway
SAM 3 shipped in November 2025 and SAM 3.1 in March 2026. Both are GPU models: about 23 s per frame on a 4-thread CPU. SAM 2.1 Tiny/Small and EdgeTAM are the CPU-feasible trackers at about 1-3 s per frame (sam3.cpp, Apple M4 Pro, 4 threads). That is tens of minutes per object for a full reel, so run them at reduced resolution or frame stride. Omnimatte-style RGBA decomposition (Generative Omnimatte, EasyOmnimatte) is diffusion-based and GPU-only. Of the video matting models, RVM is GPL-3.0 and MatAnyone is non-commercial.

### Cited Findings
- SAM 3 was released 19 Nov 2025 (text/concept prompts plus tracking). SAM 3.1 followed on 27 Mar 2026 with Object Multiplex, which Meta says is about 7x faster at 128 objects on one H100. A secondhand figure puts medium-object tracking at about 16 fps (SAM 3) versus 32 fps (SAM 3.1) on H100. — [SAM 3 arXiv 2511.16719](https://arxiv.org/html/2511.16719v2); [LearnOpenCV SAM 3.1](https://learnopencv.com/sam-3-whats-new/); [Labellerr (secondary)](https://www.labellerr.com/blog/sam-3-vs-sam-3-1-performance-comparison/)
- SAM 3 is about 848M parameters, described as a poor fit for CPU/edge; 30 ms per image on an H200 with 100+ objects. — [Medium (secondary)](https://medium.com/@aminfadaeinejad.edu/when-to-use-sam-and-when-not-to-14374cb9c401); [Ultralytics SAM 3 docs](https://docs.ultralytics.com/models/sam-3)
- sam3.cpp (MIT, C/C++ ggml port; supports SAM 3, SAM 2/2.1 Tiny-Large and EdgeTAM; quantised f16/q8/q4). Per-frame tracking times, Apple M4 Pro, 4 threads, 1008x1008:

  | Model | CPU (s/frame) | Metal (s/frame) |
  |---|---|---|
  | SAM 3 full (f16) | 23.8 | 7.7 |
  | SAM 3 visual-only | ~22 | ~6.6 |
  | SAM 2.1 Tiny | ~2.4-2.6 | ~0.9 |
  | SAM 2.1 Small | ~2.7-2.9 | ~0.9 |
  | EdgeTAM | 1.1 | 0.4 |

  — [GitHub PABannier/sam3.cpp](https://github.com/PABannier/sam3.cpp)
- A CPU-optimised SAM 3 community repo exists. — [GitHub Sompote/SAM3_CPU](https://github.com/Sompote/SAM3_CPU)
- EfficientTAM is about 1.6x faster and 2.4x smaller than SAM 2; EdgeTAM runs at 16 FPS on an iPhone 15 Pro Max (blog, secondary). EfficientSAM3 (Nov 2025) distils SAM 1/2/3 for video concept segmentation. Efficient-SAM2 (Feb 2026) speeds up SAM 2 via object-aware encoding and memory retrieval. — [LearnOpenCV](https://learnopencv.com/sam-3-whats-new/); [EfficientSAM3 arXiv 2511.15833](https://arxiv.org/pdf/2511.15833); [Efficient-SAM2 arXiv 2602.08224](https://arxiv.org/pdf/2602.08224)
- Generative Omnimatte (CVPR 2025 highlight): fine-tunes a video inpainting diffusion model to decompose video into RGBA layers including shadows and reflections; code public. — [GitHub gen-omnimatte-public](https://github.com/gen-omnimatte/gen-omnimatte-public); [arXiv 2411.16683](https://arxiv.org/pdf/2411.16683)
- EasyOmnimatte (arXiv Dec 2025, listed at CVPR 2026): end-to-end omnimatte from a fine-tuned inpainting diffusion model. Claims state of the art, and says Gen-Omnimatte suffers colour distortion (authors' own claim). — [arXiv 2512.21865](https://arxiv.org/abs/2512.21865); [CVPR 2026 paper](https://openaccess.thecvf.com/content/CVPR2026/papers/Hu_EasyOmnimatte_Taming_Pretrained_Inpainting_Diffusion_Models_for_End-to-End_Video_Layered_CVPR_2026_paper.pdf)
- LayerFlow (2025): layer-aware video generation (foreground, background, blended). — [arXiv 2506.04228](https://arxiv.org/pdf/2506.04228)
- RobustVideoMatting: GPL-3.0. GPU speed 4K 76 FPS and HD 104 FPS on a GTX 1080 Ti. Has ONNX/TF.js/CoreML exports and was tested on ONNX Runtime CPU, but no CPU figure is given. Designed for human portrait matting (**2021, older**). — [GitHub PeterL1n/RobustVideoMatting](https://github.com/PeterL1n/RobustVideoMatting)
- MatAnyone (CVPR 2025): NTU S-Lab License 1.0, non-commercial only; no CPU figures found. — [MatAnyone LICENSE](https://github.com/pq-yang/MatAnyone/blob/main/LICENSE); [repo](https://github.com/pq-yang/MatAnyone)
- [prior knowledge, unverified] SAM 2/2.1 code and weights are Apache-2.0. Layered Neural Atlases (2021) and the original Omnimatte (2021) are **older** per-video optimisation methods needing GPU hours per clip. EfficientTAM code is Apache-2.0.

### Inferences
- **CPU budget for one tracked object over a 45 s reel (~1,350 frames):**
  - EdgeTAM at about 1.1 s/frame: about 25 min.
  - SAM 2.1 Tiny at about 2.5 s/frame: about 55 min.
  - These are M4 Pro numbers. A 4-vCPU x86 container is likely slower (unverified).
  - Practical options: track at 512 px instead of 1008 (roughly 4x fewer pixels); stride 2-3 and interpolate masks; track only per-shot keyframes.
  - Shots in these reels last 1-4 s, so masks only matter inside a shot (30-120 frames).
- **SAM 3** text prompts ("the phone", "the headline text") would automate prop finding, but cost about 23 s per frame on CPU. Use it on a single keyframe per shot (about 20-40 s per shot) and hand the mask to EdgeTAM/SAM 2.1 for propagation, or run it on a GPU.
- **Graphic content fits poorly with omnimatte and matting.** Those methods target natural video (people, shadows, reflections). AE reels are already composites of flat layers with mostly hard alpha. Cheaper routes:
  - colour-key / flat-region segmentation (k-means in Lab plus connected components);
  - text detection/OCR boxes for kinetic text;
  - a median "clean plate" background per shot after camera stabilisation (Q2);
  - SAM masks for props.
  RVM and MatAnyone are human-centric and licence-encumbered, so skip them.
- **Failure modes:**
  - SAM-family models over-segment text into glyphs, or merge text with a same-colour background.
  - Masks drift during whip-pan blur and flashes.
  - Diffusion omnimatte hallucinates textures and shifts colours; that is fatal for SSIM-based 1:1 matching.

### Gaps
- No official EfficientTAM or EdgeTAM CPU benchmark on x86. No measured RVM CPU FPS.
- Runtimes and VRAM for Generative Omnimatte and EasyOmnimatte could not be fetched. Expect a multi-GB GPU and minutes per clip (unverified).
- SAM 3 / 3.1 licence terms were not verified (Meta's SAM licence; check before commercial use).

## Q4. Shot-type/archetype matching (embeddings, VLM per-shot description, reliability)

### Takeaway
For about 40 archetypes, matching works best as a hybrid. Semantic content comes from frame embeddings: SigLIP 2 or CLIP on 3-5 keyframes per shot, run through ONNX on CPU in seconds per shot. Motion comes from explicit descriptors: the Q2 camera curves, the Q1 transition type, and layer counts. Generic video embeddings are weak on camera motion. On CameraBench, generative VLMs beat embedding baselines for camera-motion retrieval. Small Qwen3-VL (2B/4B GGUF) runs on CPU via llama.cpp with frames passed as images. Reliability for fine motion detail is not established, so use VLM text as a tie-breaker or for labelling, not as ground truth.

### Cited Findings
- SigLIP 2 (Feb 2025): an open encoder family that excels at zero-shot classification, retrieval and feature extraction; improved localisation and dense features. Evaluations are image-focused. — [SigLIP 2 arXiv 2502.14786](https://arxiv.org/pdf/2502.14786)
- CameraBench (NeurIPS 2025 D&B): camera-motion primitive labels used for classification, retrieval, VQA and captioning. For video-text retrieval, generative VLMs (scored with VQAScore) outperform other baselines. — [CameraBench NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/file/c2d7b739f61ffbea729dad2cf9ec8c60-Paper-Datasets_and_Benchmarks_Track.pdf)
- V-JEPA 2 Large: camera-motion information is linearly decodable from intermediate layers (probing study, 2026). Fovea-JEPA (2026 preprint, not peer-reviewed) argues V-JEPA has geometric blind spots and reports 71.47% mAP on CameraBench. — [arXiv 2609.01551](https://arxiv.org/pdf/2609.01551); [Fovea-JEPA arXiv 2610.34033](https://arxiv.org/abs/2610.34033)
- 2026 work on shot-language understanding: "Seeking Universal Shot Language Understanding Solutions" (snippet only). — [arXiv 2603.18448](https://arxiv.org/pdf/2603.18448)
- Qwen3-VL 2B has official GGUF builds (CPU, CUDA, Metal, SYCL), and llama.cpp has supported Qwen3-VL GGUF since 30 Oct 2025. Sizes are about 1.9 GB (2B) and 3.3 GB (4B) at Ollama Q4. — [HF Qwen3-VL-2B-Instruct-GGUF](https://huggingface.co/Qwen/Qwen3-VL-2B-Instruct-GGUF); [Unsloth guide](https://unsloth.ai/docs/models/tutorials/qwen3-how-to-run-and-fine-tune/qwen3-vl-how-to-run-and-fine-tune); [insiderllm guide](https://insiderllm.com/guides/qwen-models-guide/)
- Video via llama.cpp is unclear: one article says native video inference isn't supported for Qwen3.5 in llama.cpp. ComfyUI-QwenVL feeds video as a frame sequence through llama-cpp-python's Qwen3VLChatHandler. A tutorial notes the 4B model struggles with longer video contexts. — [debuggercafe Qwen3.5](https://debuggercafe.com/introduction-to-qwen3-5-overview-vllm-and-llama-cpp/); [ComfyUI-QwenVL](https://github.com/1038lab/ComfyUI-QwenVL); [debuggercafe Qwen3-VL](https://debuggercafe.com/introduction-to-qwen3-vl/)
- [prior knowledge, unverified] SigLIP/SigLIP 2 and OpenAI CLIP weights are Apache-2.0/MIT; ViT-B-scale image encoders take about 50-200 ms per image on a 4-core CPU with ONNX Runtime. VideoMAE (2022, **older**) and InternVideo2 (2024) are action-recognition encoders trained on natural video, with no evidence of value on motion graphics. Gemini 2.x/3 accept native video input via API and are the cheapest "GPU-free" high-quality VLM option, but they are cloud services: uploading third-party reels has privacy and terms implications.

### Inferences
- **Recommended matcher for ~40 archetypes.** Build a per-shot feature vector from:
  - mean and max SigLIP 2 embedding of 3-5 keyframes (layout/content: paper card, phone mock-up, big headline, prop flat-lay);
  - camera-motion descriptor from Q2 (total zoom, pan direction, roll, ease profile, parallax layer count);
  - shot duration and in/out transition types from Q1;
  - text-area fraction and character count (OCR).
  Then do k-NN or logistic regression against the labelled library. With so few classes, a hand-weighted distance or small linear model on these features should beat pure embedding k-NN; validate with leave-one-reel-out.
- Embedding k-NN alone will confuse archetypes that look alike but move differently, e.g. "push-in on headline" versus "pan across headline". CLIP-style encoders see single frames and CameraBench shows embedding baselines lag on motion.
- **CPU cost:**
  - SigLIP 2 B/16 on about 100 keyframes per reel: well under a minute.
  - Qwen3-VL-2B/4B Q4 on CPU: plausibly tens of seconds to a few minutes per shot with 4-8 frames, given prefill of several hundred vision tokens per frame (unverified). Usable for offline library labelling, slow for every shot of every reel.
- **VLM failure modes on graphic content:** hallucinated camera moves (static zoom described as a pan); misread stylised fonts; transitions described generically ("the scene changes"); counting errors on layers. Constrain output with JSON schemas listing the archetype names and ask for multiple-choice answers rather than free description.
- **Cheapest occasional GPU:** serverless per-second billing is best for bursty jobs (SAM 3 keyframes, VGGT, omnimatte experiments, Qwen3-VL-8B). Modal rates (Nov 2026):

  | GPU | Per second | Per hour |
  |---|---|---|
  | T4 | $0.000164 | $0.59 |
  | L4 | $0.000222 | ~$0.80 |
  | A10 | $0.000306 | ~$1.10 |

  CPU and memory are billed extra and GPU functions are preemptible. A 10-minute L4 job costs about $0.13 plus cold start. — [Modal A10G article](https://modal.com/blog/nvidia-a10g-price-article); [computeprices](https://computeprices.com/blog/modal-gpu-pricing-per-second-billing-explained); [spheron](https://www.spheron.network/blog/modal-gpu-pricing-2026-per-second-billing/)
  - Caveat: this container's network allowlist would need the provider's hosts allowed.
  - RunPod/Vast-style hourly rentals or Colab are alternatives (not researched here).

### Gaps
- No published accuracy of CLIP/SigLIP k-NN on motion-graphics shot archetypes. It must be measured on the r1-r6 library.
- No measured CPU latency for Qwen3-VL-2B/4B on video frames, and no reliability study on synthetic/graphic content.
- Gemini pricing, video limits and reliability on motion graphics were not researched (out of tool budget).
- InternVideo2.5 / VideoMAE v2 CPU feasibility was not checked.

---

### Overall CPU-only budget sketch (4 cores, 45 s reel; inference, not measured)
| Stage | Method | Approx. time | GPU needed? |
|---|---|---|---|
| Decode + downscale | ffmpeg | < 30 s | no |
| Cuts | TransNetV2 + PySceneDetect + signal rules | ~1 min | no |
| Camera per shot | DIS flow + RANSAC similarity/homography | 1-3 min | no |
| Parallax layers | residual-flow clustering | 1-2 min | no |
| Prop masks | SAM 3 on keyframes + EdgeTAM/SAM2.1-T propagation at 512 px, stride 2 | ~10-30 min per object | optional |
| Archetype match | SigLIP 2 keyframes + motion features k-NN | < 1 min | no |
| VLM labels | Qwen3-VL-2B/4B GGUF, few frames per shot | ~minutes per shot | optional |
| RGBA omnimatte | Gen-Omnimatte / EasyOmnimatte | n/a on CPU | yes |
| 3D camera | VGGT / MegaSaM | n/a on CPU (practically) | yes |
