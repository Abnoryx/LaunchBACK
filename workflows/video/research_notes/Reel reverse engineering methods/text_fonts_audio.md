# Text, font and audio extraction for reverse-engineering kinetic-typography reels (CPU-only)

Scope: 4-CPU Linux container, no GPU, Python. Target clip: a 30-60 s Instagram/TikTok reel with kinetic type, a voice-over (VO), a music bed and SFX.

Access note (affects confidence): in this session arxiv.org, huggingface.co and paddlepaddle.github.io could not be fetched (DNS blocked by the sandbox network policy). Claims about the arXiv paper, HF model cards and PaddleOCR docs come from search-engine snippets, not full-text reads. GitHub READMEs were read in full. Every runtime below is either a published benchmark on different hardware or an extrapolation (marked as such). Nothing was benchmarked locally.

## Q1. Best CPU choice for each task, with expected runtime for a 30-60 s reel on 4 cores

### Takeaway
A workable all-CPU stack: **RapidOCR (PP-OCRv5 ONNX) with `return_word_box=True`** for per-word boxes per frame, sampled only on frames that change; **DINOv2-LoRA font classifier (dchen0 / GoogleFontsBench)** plus **storia font-classify (EfficientNet-B3, ~3,000 Google Fonts)** for font candidates, followed by render-and-compare against the glyph mask; **faster-whisper int8 (+ WhisperX alignment if you need tighter word edges)** for VO words; **audio-separator (BS-RoFormer) or Demucs htdemucs** for VO/music split; **beat_this** for beats/downbeats; **PANNs Cnn14_DecisionLevelMax or LAION-CLAP** for SFX tagging. Expected total for a 60 s reel on 4 cores: roughly 5-15 minutes, dominated by stem separation and per-frame OCR (extrapolated).

### Cited Findings

**(1) Scene-text OCR on frames**
- RapidOCR: Apache-2.0 code. Models are converted from PaddleOCR and also distributed under Apache 2.0. Engines: ONNX Runtime, OpenVINO, MNN, Paddle, TensorRT, PyTorch. Install with `pip install rapidocr onnxruntime`. — [RapidOCR GitHub](https://github.com/RapidAI/RapidOCR)
- RapidOCR word boxes: `return_word_box=True` (off by default) adds per-word/char boxes in `word_results` as (text, conf, box). `return_single_char_box=True` forces per-character boxes for English too. Usage from the v3.2.0 release note: `engine(img, return_word_box=True, return_single_char_box=True)`. — [RapidOCR v3.2.0 release](https://newreleases.io/project/github/RapidAI/RapidOCR/release/v3.2.0); [DeepWiki: word box calculation](https://deepwiki.com/RapidAI/RapidOCR/3.4-word-box-calculation); [RapidOCR params docs](https://rapidai.github.io/RapidOCRDocs/main/install_usage/rapidocr/parameters)
- Version caveat: the official docs say that in rapidocr_onnxruntime 1.4.0 English got word boxes, and from 1.4.1 English got per-letter boxes. Check the behaviour of the installed version. — [RapidOCR params docs](https://rapidai.github.io/RapidOCRDocs/main/install_usage/rapidocr/parameters)
- Word/char boxes are computed from the recognizer's CTC column positions inside the detected line box, not by a separate detector. So they are approximate and assume a straight line of text (inference from the DeepWiki description of the word-box step). — [DeepWiki: word-level info](https://deepwiki.com/RapidAI/RapidOCR/6.3-word-level-information)
- RapidOCR CPU speed (unnamed CPU): on a 300x400 mixed-language image with 21 boxes, detection took ~126 ms, recognition ~64 ms per box, and end to end was ~242 ms. A May 2026 Windows test (Core Ultra 9 285K, 60 images at 1180x92, PP-OCRv5) took ~18 s with RapidOCR 3.8.1 + OpenVINO and ~9.2 s with the C# ONNX Runtime port. Both are secondary sources. — [search summary of RapidOCR NPU page / cnblogs post](https://www.cnblogs.com/luoht/p/20026520)
- PP-OCRv5 ONNX exports exist on HF (e.g. `PaddlePaddle/PP-OCRv5_server_det_onnx`, `monkt/paddleocr-onnx`). One card claims ~100-300 ms per image on CPU but gives no hardware details. — [HF PP-OCRv5_server_det_onnx](https://huggingface.co/PaddlePaddle/PP-OCRv5_server_det_onnx); [HF monkt/paddleocr-onnx](https://huggingface.co/monkt/paddleocr-onnx). A CVPR 2026 paper on PP-OCRv5 exists. — [CVPR 2026 supplemental](https://openaccess.thecvf.com/content/CVPR2026/supplemental/Cui_PP-OCRv5_A_Specialized_CVPR_2026_supplemental.pdf)
- Florence-2: MIT licence, which permits commercial use. `<OCR_WITH_REGION>` returns text plus quad boxes in one pass. Roboflow says it can run on CPU but to "expect inferences to take several seconds". On a T4 GPU an OCR call takes ~1 s. — [Roboflow Florence-2 OCR](https://blog.roboflow.com/florence-2-ocr); [Roboflow Florence-2 overview](https://blog.roboflow.com/florence-2/); [HF Florence-2-base PR adding MIT LICENSE](https://huggingface.co/microsoft/Florence-2-base/discussions/1/files)
- Kinetic-typography prior work that does reveal tracking: the `stroke-reveal` repo rebuilt a "Hello!" animation frame-accurately from a reference video. The author identified the typeface by scoring candidate fonts against the video's glyph mask, and tracked stroke timing and reveal direction frame by frame. — [Sama-ndari/stroke-reveal](https://github.com/Sama-ndari/stroke-reveal)

**(2) Font identification**
- arXiv 2602.13889, "Parameter-Efficient Fine-Tuning of DINOv2 for Large-Scale Font Classification" (Chen, Zinn, Lowe). GoogleFontsBench has 394 font variants (≈31-32 families × weights/styles) and ~226K synthetic images, about 575 training images per variant. LoRA trains about 1% of the 87.2M parameters. v1 (Feb 2026) reported ~86% top-1; v2 (Apr 2026) reports 99.0% top-1 and a severity metric (SWER) with errors about 140× less severe than random. The authors say the benchmark, models and pipeline are released. — [arXiv html v2](https://arxiv.org/html/2602.13889v2); [arXiv html v1](https://arxiv.org/html/2602.13889v1). (Read from search snippets only; arxiv.org was blocked.)
- Weights: HF `dchen0/font_classifier_v4` (also `dchen0/font-classifier-v3` and `dchen0/font-classifier`). The base is listed as `facebook/dinov2-base-imagenet1k-1-layer`, with 394 labels. Pad-to-square and ImageNet normalisation are built in. The LoRA adapters are merged into the base weights, so only HF Transformers is needed. A server-side-preprocessing variant is `AnythingAI/font-classifier-v4`. — [HF dchen0/font_classifier_v4](https://huggingface.co/dchen0/font_classifier_v4); [HF AnythingAI/font-classifier-v4](https://huggingface.co/AnythingAI/font-classifier-v4); [training script](https://huggingface.co/dchen0/font_classifier_v4/blob/main/train_model.py)
- Label confusion: the model card calls the 394 labels "families", but the paper calls them variants (31 or 32 families). — same sources as above
- Possible defect: a Confect-io pull request says the v4 ONNX may have been exported at a resolution it was never trained on, which could silently lower accuracy. Verify the input size before trusting outputs. — [Confect-io/google-font-classifier PR #1](https://github.com/Confect-io/google-font-classifier/pull/1) (repo now returns 404 on direct fetch)
- storia-ai/font-classify: an EfficientNet-B3 fine-tuned on synthetic Google Fonts. The checkpoint covers about 3,000 Google Fonts and is published as ONNX at `storia/font-classify-onnx`. Includes `google_fonts_mapping.tsv` to map names to the Google Fonts API. — [HF storia/font-classify-onnx](https://huggingface.co/storia/font-classify-onnx); [ecosyste.ms entry](https://awesome.ecosyste.ms/projects/github.com%2Fstoria-ai%2Ffont-classify)
- `gaborcselle/font-identifier`: a ResNet-18 fine-tune covering only 48 standard fonts. A toy for this use. — [HF gaborcselle/font-identifier](https://huggingface.co/gaborcselle/font-identifier)
- VLMs are poor font recognisers: "Texture or Semantics? Vision-Language Models Get Lost in Font Recognition" (2025). — [arXiv 2503.23768](https://arxiv.org/html/2503.23768v2)
- WhatTheFont: a MyFonts/Monotype consumer tool (web, iOS, Android). No public API or developer terms were found. Monotype's separate Fonts API needs its own terms to be accepted. — [MyFonts about](https://www.myfonts.com/pages/about); [Monotype Fonts API](https://www.monotype.com/fonts-api)

**(3) Kinetic-typography prior work** (mostly generation, not recovery)
- Kinetic Typography Diffusion Model (ECCV 2024, arXiv 2407.10476) generates text animations. Its ~600K training videos come from 584 templates with varied letter position, glyph and size. Flagged as 2024. — [arXiv 2407.10476](https://arxiv.org/abs/2407.10476)
- TextAlive: an authoring tool that syncs kinetic text to music or speech. Older work. — [ResearchGate TextAlive](https://www.researchgate.net/publication/275715951_TextAlive_Integrated_Design_Environment_for_Kinetic_Typography)
- Kinetic Typography Engine (CMU): an extensible system for animating expressive text. Pre-2010. — [ResearchGate](https://www.researchgate.net/publication/220877173_The_kinetic_typography_engine_an_extensible_system_for_animating_expressive_text)
- Differentiable Variable Fonts (arXiv 2510.07638) could fit weight/width axes by optimisation. — [arXiv 2510.07638](https://arxiv.org/pdf/2510.07638)
- No academic paper on recovering kinetic-typography parameters from video was found. stroke-reveal (above) is the closest practical precedent. — [stroke-reveal](https://github.com/Sama-ndari/stroke-reveal)

**(4) Audio**
- faster-whisper: MIT licence. Use `word_timestamps=True`; each segment then has `.words` with start, end and word. `vad_filter=True` uses Silero VAD. CPU benchmark on **13 min of audio**, `small` model, i7-12700K, 8 threads, beam 5:

  | Setup | Time | RAM |
  |---|---|---|
  | fp32 | 2m37s | 2257 MB |
  | int8 | 1m42s | 1477 MB |
  | int8, `batch_size=8` | 51s | 3608 MB |
  | whisper.cpp fp32 | 2m05s | 1049 MB |
  | whisper.cpp OpenVINO | 1m45s | 1642 MB |
  | openai/whisper fp32 | 6m58s | 2335 MB |

  The benchmark does not measure the overhead of word timestamps. — [faster-whisper README](https://github.com/SYSTRAN/faster-whisper)
- faster-whisper threads: don't use more threads than physical cores. — [faster-whisper issue (CPU perf)](https://github.com/SYSTRAN/faster-whisper/issues/279)
- WhisperX: BSD-2-Clause. It runs on CPU with `--compute_type int8 --device cpu` and uses faster-whisper for transcription plus wav2vec2 forced alignment for word timestamps. Words with characters outside the aligner's dictionary (e.g. "2014.", "£13.60") get no timing. Numba speeds up alignment by up to 30-100×. Diarization (pyannote, CC-BY-4.0, needs an HF token) is optional. — [WhisperX GitHub](https://github.com/m-bain/whisperX)
- audio-separator: MIT licence. It asks that you credit UVR and its developers. Supports MDX, VR, Demucs and MDXC/RoFormer models, CPU-only supported, `pip install "audio-separator[cpu]"`. Vocal SDR by model:

  | Model | Vocal SDR | Other stems |
  |---|---|---|
  | `model_bs_roformer_ep_317_sdr_12.9755.ckpt` (CLI default) | 12.9 | instrumental 17.0 |
  | `vocals_mel_band_roformer.ckpt` | 12.6 | |
  | `melband_roformer_big_beta4` | 12.5 | |
  | `htdemucs_ft` | 10.8 | drums 10.1, bass 11.9 |

  No CPU timings are given. — [python-audio-separator GitHub](https://github.com/nomadkaraoke/python-audio-separator)
- RoFormer models are tuned for GPU. A GitHub issue reports high CPU use and poor latency on CPU-only setups. Overlap-add with small hops can multiply inference time by about 6×. — [Mel-Band-Roformer issue #3](https://forgejo.us2.navan.dev/github/Mel-Band-Roformer-Vocal-Model/issues/3); [BSRNN replication, arXiv 2603.09187](https://arxiv.org/pdf/2603.09187)
- htdemucs CPU times (inconsistent, secondary sources):
  - M4 Max, PyTorch CPU: 7 min track in ~2m15s, about 19 s per minute of audio. — [Medium MLX port write-up](https://medium.com/@andradeolivier/i-ported-demucs-to-apple-silicon-it-separates-a-7-minute-song-in-12-seconds-6c4e5cffb5c3)
  - Intel laptops: i7 ~8 min and i5 ~15 min for a 4 min track (unbenchmarked guide estimates). — [stemsplit Demucs setup guide](https://stemsplit.io/blog/demucs-local-setup-guide)
- beat_this (CPJKU): MIT licence for code and weights. Outputs beats and downbeats through `file2beats()`. CPU fallback with `--gpu=-1`. Small models are ~8.1 MB vs ~78 MB for `final`. The default runs without a DBN; `dbn=True` needs madmom from GitHub. No CPU timings are given. — [beat_this GitHub](https://github.com/CPJKU/beat_this)
- madmom: BSD source code, but **model and data files are CC BY-NC-SA 4.0**. Commercial use needs contacting Gerhard Widmer. — [madmom GitHub](https://github.com/CPJKU/madmom)
- PANNs: MIT licence. AudioSet mAP: `Cnn14` 0.431, `Cnn14_16k` 0.438, `Cnn14_DecisionLevelMax` 0.385. The decision-level models give frame-wise sound event detection. Inference with `pip install panns_inference`. — [audioset_tagging_cnn GitHub](https://github.com/qiuqiangkong/audioset_tagging_cnn)
- LAION-CLAP: repo licence CC0-1.0. Checkpoints `630k-audioset-best.pt` (under 10 s) and `630k-audioset-fusion-best.pt` (variable length), plus music/speech checkpoints. Zero-shot prompt: "This is a sound of <class>". The training data is mostly copyright-restricted, and the music/speech checkpoints are a "temporary release… take your own risk". — [LAION-AI/CLAP GitHub](https://github.com/LAION-AI/CLAP)
- MS-CLAP zero-shot ESC-50 is 82.6%, above the 81% human figure. No whoosh/riser-specific benchmarks were found. — [CLAP paper arXiv 2206.04769](https://ar5iv.labs.arxiv.org/html/2206.04769)

### Inferences
- **VO words, 60 s, 4 cores:** scaling the `small` int8 result (13 min in 102 s on 8 threads, ≈7.6× realtime) gives ~8 s per 60 s on 8 threads and roughly 12-20 s on 4 cores, plus model load. `medium` or `large-v3-turbo` int8 would likely take ~1-3 min. A known script (on-screen text) can also serve as the transcript and be force-aligned, which avoids ASR errors.
- **Stems, 60 s:** htdemucs probably takes ~1.5-4 min on 4 x86 cores. BS-RoFormer via audio-separator is likely similar or slower, given its CPU-latency complaints. Use one model, low overlap, and run it once, caching the result.
- **OCR per frame:** a 1080×1920 frame with a few words probably costs ~0.3-1 s through RapidOCR on CPU (extrapolated from the ~242 ms / 300×400 figure; detection scales with pixel count). Running all 1,800 frames of a 60 s/30 fps reel is too slow, at roughly 10-30 min. Instead, take frames on a pixel-difference trigger: run OCR when the frame changes plus every 3-5 frames during motion, and track boxes between OCR frames with template matching or optical flow. That brings it to ~2-5 min.
- **Reveal style** (blur-in, per-letter, type-on) needs no OCR on every frame. Once a word's final box is known, measure the following inside that box across frames:
  - per-char alpha/coverage from the glyph mask, which separates per-letter from whole-word reveals;
  - Laplacian variance, which shows blur-in;
  - bbox scale and offset, which show pop or slide.
- **Font ID:** use the classifier only to shortlist. Then render the shortlisted Google Fonts with Pillow or Skia at the measured size and score IoU or chamfer distance against the binarised glyph mask (the method stroke-reveal used). This also recovers weight and size.
- **Measurements from boxes:**
  - cap height and x-height come from per-char box heights;
  - tracking is the inter-glyph gap minus the font's advance-width prediction;
  - leading is the baseline-to-baseline distance;
  - convert to pt with the font's unitsPerEm and capHeight from fontTools.
- **SFX:** onsets on the separated residual (music minus beat-aligned hits) with librosa `onset_detect`, then classify each 1 s window with CLAP using prompts like "whoosh", "impact hit", "riser", "pop", "camera shutter". Expect it to be fast: seconds per reel (inference).
- **From prior knowledge, not verified this session:**
  - Demucs is MIT-licensed, with a v4 htdemucs checkpoint.
  - pyloudnorm (MIT) gives integrated LUFS (BS.1770).
  - ffmpeg `-af ebur128` / `loudnorm` gives LUFS/LRA/true peak. Reels typically sit around -14 LUFS.
  - librosa is ISC-licensed.

### Gaps
- No direct CPU benchmark of PP-OCRv5 on 1080p frames on a 4-core x86. Should be measured locally.
- No CPU timings for BS-RoFormer/MelBand-RoFormer, beat_this, PANNs or CLAP. No published benchmark of whisper.cpp vs faster-whisper with word timestamps on 4 cores.
- GOT-OCR 2.0, docTR, EasyOCR and small VLMs (Qwen2.5-VL-3B, SmolVLM, moondream) were not researched within the tool budget. No sourced CPU or accuracy figures for them.
- Sources for pyloudnorm, ffmpeg ebur128 and librosa onsets were not fetched (see the inference above).

## Q2. Accuracy caveats on heavily stylised graphic text

### Takeaway
All the pieces are trained mostly on clean or synthetic data. Expect OCR to miss or garble motion-blurred, outlined, very large display or rotated text, and expect word/char boxes to be approximate. Font classifiers are reliable only inside their label set (394 variants for DINOv2-LoRA; ~3,000 Google Fonts for storia) and on clean, horizontal crops. Plan on render-and-compare verification and a human check.

### Cited Findings
- RapidOCR word/char boxes come from the recognizer's CTC output inside a line box. They depend on the detected line and change between versions (word vs letter boxes for English). — [DeepWiki word box calc](https://deepwiki.com/RapidAI/RapidOCR/3.4-word-box-calculation); [RapidOCR params docs](https://rapidai.github.io/RapidOCRDocs/main/install_usage/rapidocr/parameters)
- GoogleFontsBench is synthetic and covers only 31-32 families. The 99% figure (v2) is on that synthetic test set, and v1 reported 86% for the same 394 classes. — [arXiv 2602.13889 v2](https://arxiv.org/html/2602.13889v2); [v1](https://arxiv.org/html/2602.13889v1)
- The v4 export may run at an untrained resolution and lose accuracy silently. — [Confect-io PR #1](https://github.com/Confect-io/google-font-classifier/pull/1)
- VLMs perform poorly on font recognition and lean on texture/semantics. — [arXiv 2503.23768](https://arxiv.org/html/2503.23768v2)
- WhisperX gives no timing for tokens like numbers or currency that fall outside the aligner's dictionary. — [WhisperX GitHub](https://github.com/m-bain/whisperX)
- Standard Whisper timestamps can be off by several seconds without alignment (WhisperX claim). — [WhisperX GitHub](https://github.com/m-bain/whisperX)

### Inferences
- OCR preprocessing for stylised text:
  - Take frames from the settled end of each reveal (max-sharpness frame per word), not mid-animation.
  - Upscale small text 2×.
  - Run OCR on an inverted copy as well for light-on-dark or outlined text.
  - Deskew rotated lines with the det quad before recognition. PP-OCR's angle classifier only handles 0/180°.
  - Use the known script or the VO transcript to fix OCR text by fuzzy matching. Since the VO usually says the on-screen words, ASR words can be aligned to OCR words, which gives the "word appears when spoken" timing too.
- Font classifier inputs: tightly cropped, upright, single-colour glyphs on a plain background. Outlines, gradients, drop shadows and motion blur should be removed or skipped. Mixed serif/sans lines should be split per word before classification.
- A heavily customised or paid display font (common in AE templates) will not be in either label set. The closest free Google Font is the realistic target.

### Gaps
- No benchmark measures OCR accuracy on stylised kinetic text in short-form video. PP-OCRv5 per-scenario accuracy (artistic text, rotated) could not be read because the PaddleOCR docs were blocked.
- No measured accuracy of the font classifiers on real-world crops from video.

## Q3. Licences (commercial use OK?)

### Takeaway
Most of the stack is commercially usable: Apache-2.0, MIT, BSD, CC0 code. Exceptions:
- **madmom model files are CC BY-NC-SA 4.0** (non-commercial). Use beat_this (MIT) without the madmom DBN, and librosa onsets instead of madmom's CNN onset models.
- **LAION-CLAP checkpoints** carry training-data caveats.
- **pyannote** (CC-BY-4.0, gated) is only needed for diarization.
- **WhatTheFont** has no public API terms, so treat it as manual or off-limits for automation.
- The DINOv2 font classifier weights' licence was not confirmed (HF blocked).

### Cited Findings
- RapidOCR: Apache-2.0 code, and its PaddleOCR-derived models are Apache 2.0. — [RapidOCR](https://github.com/RapidAI/RapidOCR)
- Florence-2: MIT, commercial use permitted. — [Roboflow](https://blog.roboflow.com/florence-2/)
- faster-whisper: MIT. — [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- WhisperX: BSD-2-Clause. Its pyannote diarization model is CC-BY-4.0. — [WhisperX](https://github.com/m-bain/whisperX)
- audio-separator: MIT, with a request to credit UVR. It does not state separate weight licences. — [audio-separator](https://github.com/nomadkaraoke/python-audio-separator)
- beat_this: MIT for code and weights. Some training data is copyrighted or under limited CC licences, and users must judge that themselves. — [beat_this](https://github.com/CPJKU/beat_this)
- madmom: BSD code, but CC BY-NC-SA 4.0 for models/data. Commercial use needs contacting the owner. — [madmom](https://github.com/CPJKU/madmom)
- PANNs: MIT. — [audioset_tagging_cnn](https://github.com/qiuqiangkong/audioset_tagging_cnn)
- LAION-CLAP: CC0-1.0 repo. Training data is copyright-restricted, and the music/speech checkpoints are "use at your own risk". — [LAION-AI/CLAP](https://github.com/LAION-AI/CLAP)
- arXiv 2602.13889 paper text is CC BY 4.0. That is the paper, not necessarily the weights. — [arXiv html](https://arxiv.org/html/2602.13889)
- WhatTheFont: no public API terms found. Monotype's Fonts API has its own terms. — [Monotype Fonts API](https://www.monotype.com/fonts-api)

### Inferences
- These are analysis tools; none of their outputs ship in the final video. So even the non-commercial madmom models would only affect internal analysis. The project rule to measure the reel but not copy its assets still applies, and the cleanest path is to avoid NC components altogether.
- Google Fonts matched by the classifiers are almost all OFL or Apache. Check each font's licence file before adding it to the library.
- DINOv2 itself was relicensed to Apache-2.0 by Meta (prior knowledge, not verified here). The dchen0 fine-tune's licence must be checked on its HF card.

### Gaps
- Licence of `dchen0/font_classifier_v4` and `storia/font-classify-onnx` weights (HF unreachable).
- Licence of individual UVR/RoFormer checkpoints downloaded by audio-separator.
- Whether a WhatTheFont/MyFonts API exists for partners and on what terms.
