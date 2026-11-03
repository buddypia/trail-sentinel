# 04. 참가 지원서 작성 가이드 및 영문 모범 답안 초안 (Application Guide)

> **지원 링크**: <https://cerebralvalley.ai/e/meta-ai-developer-hackathon/apply>
> **지원 마감**: **2026년 10월 25일 11:59 PM ET (한국 시간 2026년 10월 26일 월요일 낮 12:59 KST)**
> *(단, 20,000명 정원이 차면 마감일 이전이라도 즉시 조기 마감되므로 가능한 한 빨리 제출하시는 것을 권장합니다!)*

---

## 1. 지원서 자동 합격(Rolling Acceptance) 전략 요약

메인 페이지 및 메타데이터(`applicationLanguagePreference: "en-US"`)에서 확인된 심사 원칙:
1. **오직 2개 핵심 기준(50% : 50%)으로만 채점**:
   - **Q8 (`What do you want to build for this hackathon?`) — 50%**: 제안하는 프로젝트 아이디어가 얼마나 **명확하고 실현 가능한지(clear and feasible)**, 그리고 **두 가지 프로젝트 테마(`Build for Your World` / `Push the Frontier`) 중 하나에 얼마나 잘 부합하는지**, 또 Meta의 신규 모델들(`Muse Wonder`, `Muse Spark 1.3`, `Muse Image`, `SAM 3.1`, `Muse Voice Transcribe`, `Muse Glimmer`)을 어떻게 구체적으로 활용하는지.
   - **Q9 (`Tell us about an AI project you recently built that showcases your technical skills.`) — 50%**: 최근 직접 만든 AI 프로젝트에서 **무엇을 만들었는지(what you built)**와 **구체적으로 어떤 기술/알고리즘/기법을 사용했는지(the techniques you used)**.
2. **최소 점수 커트라인 통과 시 즉시 합격**:
   - 롤링 베이스로 채점되며, 최소 점수 커트라인을 넘기면 20,000명 한도 내에서 자동 승인됩니다.
   - 따라서 추상적인 미사여구 대신 **모델명, 알고리즘, 파이프라인 구조, 정량적 지표**를 영문으로 명확히 적어주는 것이 핵심입니다.

---

## 2. 문항별 입력 가이드 (Q0 ~ Q14 전체)

| 문항 번호 | 질문 원문 | 권장 입력 내용 |
| :---: | :--- | :--- |
| **Q0** | `What's your LinkedIn?` *(필수)* | 본인 LinkedIn 프로필 URL |
| **Q1** | `What's your Twitter/X?` *(선택)* | 본인 X(Twitter) 프로필 URL (없으면 비워둠) |
| **Q2** | `What's your Github?` *(선택이나 강력 권장)* | 본인 GitHub 프로필 또는 `lottie-motion-studio` 저장소 URL *(심사 기준에 "Links to your GitHub, LinkedIn or a shipped product help us verify your experience and skill" 명시)* |
| **Q3** | `Where do you live (City, State, Country)?` *(필수)* | 예: `Seoul, South Korea` (또는 현재 거주 도시/국가) |
| **Q4** | `Are you applying for the startup track or indie dev track?` *(필수)* | 개인/소규모 빌더 자격이면 **`Indie Dev Track`**, 법인(Buddypia 등) 대표/창업자 자격이면 **`Startup Track`** 선택 *(해커톤 기간 중 언제든 변경 가능)* |
| **Q5** | `Where do you study or work?` *(Indie 선택 시)* | 소속 회사명(예: `Buddypia`) 또는 소속/직함 |
| **Q6** | `What country is your company incorporated in?` *(Startup 선택 시)* | 예: `South Korea` (또는 법인 설립 국가) |
| **Q7** | `What round of funding are you?` *(Startup 선택 시)* | `Bootstrapped`, `Pre-Seed`, `Seed` 등 해당 단계 선택 |
| **Q8** | **`What do you want to build for this hackathon?`** *(필수, 배점 50%)* | **아래 §3의 영문 초안(Option A1 / A2 / A3 중 택1) 복사·활용** |
| **Q9** | **`Tell us about an AI project you recently built that showcases your technical skills.`** *(필수, 배점 50%)* | **아래 §4의 `Lottie Motion Studio` 기술 요약 영문 초안 복사·활용** |
| **Q10** | `Have you used Meta Model API before?` *(필수)* | `Yes` 또는 `No` (솔직하게 선택; 선발 당락과 무관) |
| **Q11** | `How likely are you to build with Meta Model API?` *(필수)* | **`Very likely`** |
| **Q12** | `How would you describe your overall opinion of Meta Model API?` *(필수)* | **`Very favorable`** |
| **Q13** | `How did you hear about this hackathon?` *(필수)* | 예: `Cerebral Valley / Meta AI Developer Portal` |
| **Q14** | `By selecting Yes, you agree to receive marketing...` *(필수)* | `Yes` 또는 `No` |

---

## 3. [Q8 모범 답안 초안] `What do you want to build for this hackathon?`

> 지원서 제출 후에도 실제 해커톤 중에 세부 구현 방향을 발전시킬 수 있으므로, 가장 설득력 있고 구체적인 아키텍처가 드러나는 **Option A1 (MuseMotion Studio 2.0)** 또는 **Option A2 (KineticLottie)**를 추천합니다.

### Option A1 (최우선 추천 — MuseMotion Studio 2.0: 멀티에이전트 2D 캐릭터 생성·분할·60FPS Lottie 컴파일러)

**복사용 영문 초안 (English):**
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

*(한국어 의미 요약: 무거운 MP4 비디오 대신 웹/모바일/Flutter 프로덕션에 즉시 투입 가능한 50KB 미만 60FPS Lottie 애니메이션을 자율 생성하는 `MuseMotion Studio`를 구축합니다. `Muse Image`로 캐릭터 생성 및 가려진 몸통/배경 아모달 인페인팅을 수행하고, `SAM 3.1`로 신체 부위·소품 정밀 분할 및 실사 비디오 모션 리타겟팅을 수행하며, `Muse Wonder / Spark 1.3`가 7컬럼 검증 시트를 시각 감사하여 관절 틈새를 자가 수리하고, `Muse Voice Transcribe`로 실시간 음성 디렉팅을 구현합니다.)*

---

### Option A2 (대안 — KineticLottie: 실사 비디오 동작을 20KB 60FPS 2D Lottie로 변환하는 모션 컴파일러)

**복사용 영문 초안 (English):**
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

## 4. [Q9 모범 답안 초안] `Tell us about an AI project you recently built that showcases your technical skills.`

> **핵심 포인트**: 심사위원이 읽자마자 *"이 지원자는 실제 컴퓨터 비전, 기하학적 수학, 온디바이스 ML, 풀스택 모션 컴파일러를 직접 밑바닥부터 구현하고 출시한 최상급 엔지니어다"*라고 확신할 수 있도록, `lottie-motion-studio`에 실제로 구현되어 있는 핵심 기술과 알고리즘 명칭을 정확히 담았습니다.

**복사용 영문 초안 (English):**
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

*(한국어 의미 요약: 단일 2D 일러스트를 상용 60FPS Lottie JSON 및 Flutter 애니메이션으로 변환하는 `Lottie Motion Studio`를 직접 설계·구축했습니다. ① 적응형 마팅과 외곽선 셀 다수결 기반의 Zero-Box 7레이어 유기적 파츠 분할, ② $\pm 45^\circ$ 회전 시 0px 틈새를 보장하는 볼록 관절 소켓 기하학, FFC/Navier-Stokes 아모달 인페인팅, 전경 소품 `__backfill` 이중 레이어 합성 및 알파 피라미드 디프린징, ③ 골반 허브(`pelvis`) 아래 상완/전완·허벅지/종아리/발목 2단 분할 및 2-Bone IK 보행 역기구학(힐스트라이크~토오프 발 구름, 척추/목 위상 지연 흔들림 보정) Lottie 컴파일러, ④ EmbeddingGemma 2 및 WebGPU 기반 20~45ms 초저지연 자연어 모션 결정 엔진(Choice & Score 프리미티브) 및 래칫 평가 하니스, ⑤ 1920px 7컬럼 검증 컨택트 시트 및 pytest/Flutter 통합 품질 게이트를 구현했습니다.)*
