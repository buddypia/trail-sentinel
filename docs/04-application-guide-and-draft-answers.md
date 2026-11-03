# 04. Application Guide and Draft Model Answers (Application Guide)

> **Application link**: <https://cerebralvalley.ai/e/meta-ai-developer-hackathon/apply>
> **Application deadline**: **11:59 PM ET, October 25, 2026 (12:59 PM KST, Monday, October 26, 2026)**
> *(However, applications close immediately once the 20,000-applicant cap is reached, even before the deadline — so submitting as early as possible is strongly recommended!)*

---

## 1. Auto-Acceptance (Rolling Acceptance) Strategy Summary

Judging principles confirmed from the main page and metadata (`applicationLanguagePreference: "en-US"`):
1. **Scored on only 2 core criteria (50% : 50%)**:
   - **Q8 (`What do you want to build for this hackathon?`) — 50%**: how **clear and feasible** the proposed project idea is, how well it fits one of the two project themes (`Build for Your World` / `Push the Frontier`), and how specifically it uses Meta's new models (`Muse Wonder`, `Muse Spark 1.3`, `Muse Image`, `SAM 3.1`, `Muse Voice Transcribe`, `Muse Glimmer`).
   - **Q9 (`Tell us about an AI project you recently built that showcases your technical skills.`) — 50%**: **what you built** in a recent AI project you made yourself and **the specific techniques you used**.
2. **Instant acceptance once the minimum score cutoff is passed**:
   - Scored on a rolling basis; applicants above the minimum score cutoff are automatically accepted within the 20,000-applicant limit.
   - So instead of abstract embellishments, the key is to clearly write **model names, algorithms, pipeline structure, and quantitative metrics** in English.

---

## 2. Per-Question Input Guide (All of Q0–Q14)

| Question No. | Original Question | Recommended Input |
| :---: | :--- | :--- |
| **Q0** | `What's your LinkedIn?` *(required)* | Your LinkedIn profile URL |
| **Q1** | `What's your Twitter/X?` *(optional)* | Your X (Twitter) profile URL (leave blank if none) |
| **Q2** | `What's your Github?` *(optional but strongly recommended)* | Your GitHub profile or the `lottie-motion-studio` repository URL *(the judging criteria state: "Links to your GitHub, LinkedIn or a shipped product help us verify your experience and skill")* |
| **Q3** | `Where do you live (City, State, Country)?` *(required)* | E.g., `Seoul, South Korea` (or your current city/country of residence) |
| **Q4** | `Are you applying for the startup track or indie dev track?` *(required)* | Choose **`Indie Dev Track`** if applying as an individual/small builder, or **`Startup Track`** if applying as a corporate (e.g., Buddypia) founder/representative *(changeable at any time during the hackathon)* |
| **Q5** | `Where do you study or work?` *(if Indie selected)* | Company name (e.g., `Buddypia`) or affiliation/title |
| **Q6** | `What country is your company incorporated in?` *(if Startup selected)* | E.g., `South Korea` (or country of incorporation) |
| **Q7** | `What round of funding are you?` *(if Startup selected)* | Select the applicable stage: `Bootstrapped`, `Pre-Seed`, `Seed`, etc. |
| **Q8** | **`What do you want to build for this hackathon?`** *(required, 50% of score)* | **Copy and use the English draft below in §3 (choose one of Option A1 / A2 / A3)** |
| **Q9** | **`Tell us about an AI project you recently built that showcases your technical skills.`** *(required, 50% of score)* | **Copy and use the `Lottie Motion Studio` technical summary English draft below in §4** |
| **Q10** | `Have you used Meta Model API before?` *(required)* | `Yes` or `No` (answer honestly; does not affect selection) |
| **Q11** | `How likely are you to build with Meta Model API?` *(required)* | **`Very likely`** |
| **Q12** | `How would you describe your overall opinion of Meta Model API?` *(required)* | **`Very favorable`** |
| **Q13** | `How did you hear about this hackathon?` *(required)* | E.g., `Cerebral Valley / Meta AI Developer Portal` |
| **Q14** | `By selecting Yes, you agree to receive marketing...` *(required)* | `Yes` or `No` |

---

## 3. [Q8 Model Answer Draft] `What do you want to build for this hackathon?`

> Since implementation details can still evolve during the actual hackathon after submitting the application, **Option A1 (MuseMotion Studio 2.0)** or **Option A2 (KineticLottie)** — which reveal the most convincing and concrete architecture — is recommended.

### Option A1 (Top recommendation — MuseMotion Studio 2.0: multi-agent 2D character generation, segmentation, and 60FPS Lottie compiler)

**Copy-ready English draft (English):**
```text
Theme: Build for Your World & Push the Frontier

I am building MuseMotion Studio, an autonomous multi-agent 2D animation pipeline that transforms a text prompt, voice direction, or single flat illustration into a production-ready, 60FPS interactive Lottie (Bodymovin JSON) animation in under 15 seconds.

While generative video models output heavy, non-interactive MP4s (10-50MB) with opaque backgrounds, real-world web and mobile apps (iOS, Android, Flutter) require lightweight (<50KB), transparent, 60FPS skeletal vector/raster animations. Currently, creating a single rigged Lottie asset requires hours of manual part slicing, occlusion painting, and keyframing in After Effects.

How I will build it using Meta's newest models:
1. Character Generation & Amodal Occlusion Inpainting (Muse Image - muse-image-1.0): Use Muse Image's Anchored Composition to generate rig-friendly 2D characters and props, and use its reasoning-driven precise editing (/v1/images/edits) to perform true semantic amodal completion—restoring occluded torso textures behind swinging arms and healing clean background plates without blurring.
2. Zero-Shot Semantic Part & Video Motion Tracking (SAM 3.1 - sam-3.1): Prompt SAM 3.1 with anatomical and prop noun phrases ("head", "torso", "left arm", "right arm", "left leg", "right leg", "handheld prop") to extract pixel-accurate masks as priors for our graph-cut pixel ownership solver and convex joint-socket generator. We also use SAM 3.1 video tracking to retarget real human movements from short video clips onto 2D character rigs.
3. Autonomous Visual QA & Self-Healing Rigging Agent (Muse Wonder / Muse Spark 1.3): After compiling an 11-joint, 2-segment inverse-kinematics (IK) Lottie rig, the pipeline renders a 7-column verification contact sheet across extreme motion phases. Muse Spark 1.3 inspects the contact sheet via multimodal tool calling to detect joint gaps, background bleed, or foot sliding, autonomously adjusting joint pivots and masks until all geometric invariants pass.
4. Real-Time Voice Directing (Muse Voice Transcribe - muse-voice-transcribe-1.0): Stream live voice commands and multi-speaker dialogue over WebSocket (wss://api.meta.ai/v1/asr/realtime) with speaker diarization and turn timestamps to choreograph multi-character Lottie scenes and lip/gesture sync in real time.
5. On-Device Agentic Fallback (Muse Glimmer 30B): Run Muse Glimmer locally alongside WebGPU inference for zero-latency offline motion timeline synthesis.
```

*(Meaning summary: building `MuseMotion Studio`, which autonomously generates sub-50KB 60FPS Lottie animations ready for immediate production use in web/mobile/Flutter instead of heavy MP4 video. `Muse Image` performs character generation and occluded-torso/background amodal inpainting, `SAM 3.1` performs precise body-part/prop segmentation and real-video motion retargeting, `Muse Wonder / Spark 1.3` visually audits the 7-column verification sheet to self-heal joint gaps, and `Muse Voice Transcribe` implements realtime voice directing.)*

---

### Option A2 (Alternative — KineticLottie: motion compiler converting real-video motion into 20KB 60FPS 2D Lottie)

**Copy-ready English draft (English):**
```text
Theme: Push the Frontier & Build for Your World

I want to build KineticLottie, a video-to-vector motion compiler that turns any 5-second smartphone video of a human action into a 20KB, 60FPS rigged 2D Lottie animation ready for Web, iOS, Android, and Flutter.

How it works with Meta Model API:
1. SAM 3.1 Video Segmentation & Tracking (sam-3.1): Given a raw video clip of a person walking, waving, or interacting with an object, SAM 3.1 segments and tracks individual anatomical limbs ("head", "torso", "left upper arm", "forearm", "thigh", "shin", "handheld prop") across frames with preserved identity.
2. Muse Spark 1.3 Kinematic Fitting: Muse Spark 1.3 processes the frame-by-frame mask trajectories and solves a 2-segment inverse kinematics (IK) optimization problem—extracting clean sinusoidal gait cycles, foot heel-strike/toe-off pitch angles, spine counter-sway, and phase-delayed forearm inertia into a compact Bodymovin JSON keyframe spec.
3. Muse Image Styled Rig Synthesis (muse-image-1.0): Using Anchored Composition and precise multi-turn editing, Muse Image transforms the subject into a clean, stylized 2D character with amodally completed limb plates and convex joint sockets so the character can rotate +/-45 degrees with zero seam tearing.
4. Muse Wonder Visual Verification Loop: Muse Wonder inspects rendered extreme-pose contact sheets and autonomously refines joint pivots and socket radii until the exported Lottie animation passes all geometric quality gates.
```

---

## 4. [Q9 Model Answer Draft] `Tell us about an AI project you recently built that showcases your technical skills.`

> **Key point**: written with the exact names of the core technologies and algorithms actually implemented in `lottie-motion-studio`, so that judges instantly conclude *"this applicant is a top-tier engineer who built and shipped real computer vision, geometric math, on-device ML, and a full-stack motion compiler from the ground up."*

**Copy-ready English draft (English):**
```text
I built Lottie Motion Studio, an end-to-end AI character decomposition, skeletal rigging, and procedural animation workbench that converts a single static 2D illustration into a production-ready 60FPS Bodymovin Lottie JSON and cross-platform Flutter animation.

Key techniques and engineering systems I designed and implemented:
1. Zero-Box Organic Morphological Part Segmentation & Ownership Solver:
   - Replaced coarse bounding-box cropping with an anatomic partitioning pipeline combining adaptive perimeter-sampled foreground matting, color/outline cell majority voting, and connected-component topology analysis to decompose characters into 7 hierarchical RGBA plates (bg, torso, head, arm_left, arm_right, leg_left, leg_right, plus handheld props).
2. Deep Amodal Occlusion Inpainting & Convex Joint Socket Geometry:
   - To prevent hollow cavities or paper-doll seam tearing under +/-45 deg joint rotations, I implemented automatic occlusion cavity detection around neck, shoulder, and hip joints, paired with Fast Fourier Convolution (FFC) / Navier-Stokes amodal inpainting and Lvmin Zhang alpha pyramid bleeding (defringing).
   - For foreground props (e.g., cross-body bags occluded by swinging arms), I engineered an automated dual-layer <layer>__backfill synthesis algorithm using distance-transform color binning so the rest pose matches the original pixel-for-pixel while arm swings reveal a seamlessly reconstructed prop.
3. 11-Joint 2-Segment Inverse Kinematics (IK) & Pelvis Hub Compiler:
   - Built a custom Python-to-Lottie compiler that splits limbs across elbow, knee, and ankle cross-sections under a null pelvis hub. It solves 2-bone IK for stride vs. front-facing gaits, computing heel-strike to toe-off foot roll, spine/neck counter-rotation with frame lag, and carried-prop arm swing suppression, sampling exact linear keyframes into Bodymovin JSON.
4. Ultra-Low-Latency Semantic Motion Decision Engine & Hillclimb Eval:
   - Built a zero-decoding semantic router using local EmbeddingGemma 2 (and WebGPU / ONNX Runtime Web client inference) that maps natural language motion prompts in 20-45ms into discrete motion intents (Choice) and continuous intensity/tempo scalars (Score) via temperature-scaled softmax expectation, governed by an automated ratchet evaluation harness.
5. Automated 7-Column Visual QA Gate:
   - Engineered a deterministic verification pipeline that renders a 1920px 7-column contact sheet auditing background ghost leaks, joint socket integrity, and grounded foot anchors across extreme motion phases, backed by an automated pytest + Flutter byte-parsing quality gate.
```

*(Meaning summary: designed and built `Lottie Motion Studio` from scratch, which converts a single 2D illustration into commercial 60FPS Lottie JSON and Flutter animations. Implemented: ① Zero-Box 7-layer organic part segmentation based on adaptive matting and outline-cell majority voting, ② convex joint-socket geometry guaranteeing 0px gaps under $\pm 45^\circ$ rotation, FFC/Navier-Stokes amodal inpainting, foreground-prop `__backfill` dual-layer compositing, and alpha-pyramid defringing, ③ a Lottie compiler with upper-arm/forearm and thigh/shin/ankle 2-segment splits under a `pelvis` hub plus 2-bone IK walking kinematics (heel-strike-to-toe-off foot roll, phase-lagged spine/neck sway correction), ④ a 20–45ms ultra-low-latency natural-language motion decision engine (Choice & Score primitives) based on EmbeddingGemma 2 and WebGPU plus a ratchet evaluation harness, and ⑤ a 1920px 7-column verification contact sheet with a pytest/Flutter integration quality gate.)*
