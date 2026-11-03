# 02. Meta AI Latest Models and Developer Tools Detailed Reference (`dev.meta.ai`)

> **Source Links**:
> - Meta AI developer portal home: <https://dev.meta.ai/>
> - Meta Model API official documentation overview: <https://dev.meta.ai/docs/overview>
> - Per-model detail pages:
>   - Muse Wonder: <https://dev.meta.ai/models/muse-wonder>
>   - Muse Spark 1.3: <https://dev.meta.ai/models/muse-spark>
>   - Muse Spark Open: <https://dev.meta.ai/models/muse-spark-open>
>   - Muse Glimmer: <https://dev.meta.ai/models/muse-glimmer>
>   - Muse Image: <https://dev.meta.ai/models/muse-image>
>   - Muse Voice Transcribe: <https://dev.meta.ai/models/muse-voice-transcribe>
>   - SAM 3.1: <https://dev.meta.ai/models/sam-3-1>
> - Geographic Use Policy: <https://dev.meta.ai/legal/geographic-use-policy>

**25% of the hackathon finals judging criteria is "Use of Meta AI Tooling"** (how creatively Meta AI tools are combined beyond simple integration, and whether unexpected capabilities are drawn out). It is therefore essential to understand exactly the full model lineup and endpoint specifications provided by the Meta Model API and to design a **multimodal, multi-model pipeline**.

---

## 1. Meta Model API Architecture and Common Specifications

- **Base URL**: `https://api.meta.ai/v1`
- **Authentication**: `Authorization: Bearer $MODEL_API_KEY`
- **Supported protocols (3 fully compatible)**:
  1. **Responses API (`POST /v1/responses`)**: Agentic multi-step workflows, reasoning replay, server-side state management, SAM 3.1 segmentation and Muse Image multi-turn image editing support
  2. **Chat Completions API (`POST /v1/chat/completions`)**: Immediately usable from existing **OpenAI SDK** clients by swapping only the Base URL and API key
  3. **Messages API (`POST /v1/messages`)**: Endpoint compatible with existing **Anthropic SDK** clients
- **Key agent capabilities (Capabilities)**:
  - Parallel Tool Calling and Streamed Tool-Call Arguments
  - Tool Search — loads only needed tools on demand to save tokens
  - Search Grounding — real-time cited responses without building a separate RAG pipeline
  - Structured Output — 100% JSON Schema compliance
  - Prompt Caching and reasoning effort control (`reasoning: { "effort": "high" }`)

---

## 2. Full Lineup Comparison Table of Hackathon Core Models

| Model Name | API Model ID | Type | Context / Input | Key Specialized Capabilities | Official Pricing (Standard / Contributor) |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **Muse Wonder** | `muse-wonder-1.0` | Hosted API | **1M** (`1,048,576`) | Frontier coding, long-running autonomous agents, subagent delegation, advanced Computer Use | Input **$4.00/M** (cached **$0.20/M**) / Output **$20.00/M** |
| **Muse Wonder Full** | `muse-wonder-full-1.0` | Muse Code only | **1M** (`1,048,576`) | Meta's highest-performance SOTA model (DeepSWE 79.0, SWE-Marathon 57.5, ranked 1st) | Included in Muse Code subscription ($50/mo Power, $200/mo Max) |
| **Muse Spark 1.3** | `muse-spark-1.3` / `muse-spark-1.3-contributor` | Hosted API | **1M** (`1,048,576`) | High-speed, high-efficiency agentic coding, native multimodal (video, image, document) visual reasoning | Standard: Input **$1.25/M** (cached $0.15) / Output **$4.25/M**<br>**Contributor: Input $0.10/M (cached $0.002) / Output $0.20/M** |
| **Muse Image** | `muse-image-1.0` | Hosted API | Text + reference images | Agentic image generation/editing that plans, executes code, and self-corrects before rendering | **$0.01 / image** (search grounding + reasoning included) |
| **SAM 3.1** | `sam-3.1` | Hosted API & open-weight | Text prompt + image/video | Object detection (Box), pixel-precise segmentation (Mask), and video ID tracking from short noun-phrase prompts | Image **$2.50 / 1,000 images** ($0.0025/image)<br>Video **$0.20 / 1,000 frames** |
| **Muse Voice Transcribe** | `muse-voice-transcribe-1.0` | Hosted API (REST & WSS) | Audio stream / file | Real-time diarization for 20+ speakers, end-of-turn detection, contextual vocabulary biasing | **$0.18 / hour** ($3.00 / 1,000 minutes) |
| **Muse Spark Open** | Open-weight (816B MoE, 42B active) | Self/partner GPU hosting | Text, image, audio, video | Highest-performance US-lab open-weight model, supports a separate intent narration (Commentary) channel | Use Baseten ($100), Modal ($100), Fireworks ($25) credits |
| **Muse Glimmer** | Open-weight (30B, Apache 2.0) | Local/edge execution | Multimodal + text | Local agent that runs continuously on a single consumer GPU or Mac (Apple Silicon) | Free (local `llama.cpp`, `vLLM`, `Ollama`, `ExecuTorch`) |

---

## 3. In-Depth Analysis per Model and Hackathon Usage Points

### 3.1 Muse Wonder (`muse-wonder-1.0`) & Muse Wonder Full
- **Features**: A flagship model designed for complex large-repository engineering and long-horizon agent tasks that run uninterrupted for hours.
- **Benchmarks**: `Muse Wonder Full` records OSWorld V2.1 (computer use) 78.4, MemoryBench 85.5, DeepSWE 1.1 79.0, and SWE-Marathon 57.5, showing frontier performance.
- **Hackathon use**: Place it as the upper planner (Orchestrator) for complex system architecture design, multi-file refactoring, and subagent orchestration (4-profile agentic team, isolated git worktree fan-out).

### 3.2 Muse Spark 1.3 (`muse-spark-1.3` / `muse-spark-1.3-contributor`)
- **Features**: The flagship model optimized for agentic workflows and multimodal visual reasoning. It takes screenshots or video clips as input and performs visual reasoning through the actual execution environment rather than scripted steps.
- **Cost-performance tip**: Using `muse-spark-1.3-contributor` mode costs **$0.10** per 1M input tokens, **$0.002** for cached input, and **$0.20** for output, so **hundreds of millions to billions of tokens** can be called with the **$150** base hackathon credit alone!

### 3.3 SAM 3.1 (`sam-3.1`) — Segment Anything Model 3.1
- **Endpoint**: `POST https://api.meta.ai/v1/responses` (file upload: `POST /v1/files`)
- **Features**:
  - Unlike SAM 1/2, which required Point or Box prompts or returned only unlabeled masks, **SAM 3.1, on a dedicated DETR-architecture inference engine, performs object detection (Bounding Box), pixel-precise segmentation (Segmentation Mask), and ID-preserving tracking (Tracking) across video frames in a single call from only short text noun-phrase prompts (short noun phrase)**.
  - It works zero-shot immediately with no separate server hosting or fine-tuning, and is very cheap at $2.50 per 1,000 images ($0.0025/image) and $0.20 per 1,000 video frames.
- **Synergy with `lottie-motion-studio`**:
  - From a single character illustration, anatomical parts and props can be separated instantly with text prompts such as `"head"`, `"torso"`, `"left arm"`, `"right arm"`, `"left leg"`, `"right leg"`, `"handheld passport"`, `"rolling suitcase"`.
  - It can serve as the core visual sensor of a pipeline that tracks body parts frame by frame from real human motion videos (walking, dancing, greeting) and retargets them into Lottie keyframes for a 2D character.

### 3.4 Muse Image (`muse-image-1.0`)
- **Endpoints**:
  - Single generation: `POST https://api.meta.ai/v1/images/generations`
  - Precise editing: `POST https://api.meta.ai/v1/images/edits`
  - Multi-turn conversational editing: `POST https://api.meta.ai/v1/responses`
- **Features**:
  - *"An image model that reasons before it renders."* — instead of rendering pixels immediately, it first makes a plan, searches the web for real references (Search Grounding), generates and executes code directly where precision is needed, and self-verifies (Self-correction) before returning the result.
  - **3 core primitives**:
    1. **Image Generation**: High-quality image generation from text descriptions ($0.01/image)
    2. **Reasoning-Driven Precise Editing**: Precise editing that modifies only the specified area/element and leaves the remaining pixels untouched
    3. **Anchored Composition**: Using a few reference images as anchors, perfectly preserves character/style consistency across many subsequent image generations
- **Synergy with `lottie-motion-studio`**:
  - When restoring the torso area behind an arm or prop or the background plate (`bg.png`) after removing a character, **Muse Image's Reasoning-Driven Edit** can perfectly restore clothing folds and background details via amodal inpainting, instead of the legacy OpenCV `INPAINT_TELEA` or solid-color patches.
  - Also, from text input alone, **Muse Image** can generate rigging-friendly character illustrations and various expression/prop variations (Anchored Composition) and immediately convert them into Lottie animations.
- **Note**: Under the Geographic Use Policy, `Muse Image` availability is restricted for end users in India (Korea, the US, and global use are available normally).

### 3.5 Muse Voice Transcribe (`muse-voice-transcribe-1.0`)
- **Endpoints**:
  - Real-time streaming: `wss://api.meta.ai/v1/asr/realtime`
  - Audio file batch: `POST https://api.meta.ai/v1/asr/transcribe`
- **Features**:
  - An ultra-low-cost streaming speech recognition model at **$0.18** per hour ($0.003 per minute).
  - It natively returns **live speaker diarization for 20+ speakers**, **turn detection / endpointing**, **contextual & keyword biasing**, **25 languages and code-switching (e.g., Korean-English mix)**, and **turn-level timing** with no separate post-processing pipeline.

### 3.6 Muse Glimmer (30B Open-Weight) & Muse Spark Open (816B MoE)
- **Muse Glimmer (30B, Apache 2.0)**:
  - A multimodal local agent model distilled from `Muse Spark` that **runs continuously on a single consumer GPU or Mac (`llama.cpp`, `Ollama`, `LM Studio`, `vLLM`, `ExecuTorch`)**.
  - It boasts best-in-30B-class agent, coding, and multimodal performance, including MCP Atlas 75.5, SWE-Bench Verified 76.0, and AIME 2026 94.7.
  - A local agent brain that perfectly matches the `lottie-motion-studio` philosophy of **"Zero-Cost Client / Local Inference"**!
- **Muse Spark Open (816B MoE / 42B Active)**:
  - An extra-large open-weight model that understands text, image, audio, and video, supporting a separate `commentary` channel that states its intent before acting. It can be hosted and fine-tuned with hackathon partner credits from **Baseten ($100), Modal ($100), and Fireworks ($25)**.

### 3.7 Muse Code (`muse` CLI)
- **Install command**: `curl -fsSL https://dev.meta.ai/install.sh | sh` (run: `muse`)
- **Features**: Meta's official multi-agent coding agent that runs in terminal and CI environments, with a built-in OS sandbox, session rewind, and subagent worktree fan-out (Agent fan-out). Using `Muse Code` in the hackathon development process itself can secure additional storytelling points for the **"Use of Meta AI Tooling (25%)"** judging criterion.
