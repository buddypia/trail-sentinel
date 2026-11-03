# Meta Global AI Developer Hackathon Document Archive and Idea Proposals

This directory is a document set compiled through exhaustive research of the main text of the [Meta Global AI Developer Hackathon](https://cerebralvalley.ai/e/meta-ai-developer-hackathon), its sub-links ([Waiver and Official Rules](https://cerebralvalley.ai/e/meta-ai-developer-hackathon/waiver), [Credit Terms PDF](https://cerebralvalley.ai/e/meta-ai-developer-hackathon/waiver), [Meta Developer Portal (`dev.meta.ai`)](https://dev.meta.ai/), [Meta Model API Official Documentation](https://dev.meta.ai/docs/overview), inference partner pages, and more) and the in-page Next.js hydration metadata (including all application questions).

It also contains project ideas and English application drafts combining the core technical assets of [`lottie-motion-studio`](file:///Users/a13973/dev/buddypia/lottie-motion-studio/README.ko.md) (pure curve part decomposition, amodal inpainting, 11-joint 2-segment IK rigging, 7-column verification gate, natural-language motion decision engine) with the hackathon judging criteria and the latest Meta AI model ecosystem.

---

## 📚 Document Structure

| Document File | Summary of Key Contents |
| :--- | :--- |
| **[01-hackathon-overview-and-rules.md](file:///Users/a13973/dev/buddypia/hackathon/MetaGlobalAIDeveloperHackathon/docs/01-hackathon-overview-and-rules.md)** | Hackathon schedule (ET/KST), total prize $1,000,000 breakdown (Indie $400k / Startup $550k / Bonus $50k), judging criteria and weights (Impact 30%, Meta AI Tooling 25%, Demo 25%, Technical Depth 20%), API credit ($150 + partner credits) terms, full specification of all 15 application questions |
| **[02-meta-ai-models-and-tooling.md](file:///Users/a13973/dev/buddypia/hackathon/MetaGlobalAIDeveloperHackathon/docs/02-meta-ai-models-and-tooling.md)** | Detailed analysis of new models and tools confirmed on `dev.meta.ai` and the official documentation: **Muse Wonder / Wonder Full**, **Muse Spark 1.3**, **Muse Spark Open (816B MoE)**, **Muse Glimmer (30B local agent)**, **Muse Image ($0.01 agentic image generation/editing)**, **SAM 3.1 (text-prompt image/video segmentation and tracking)**, **Muse Voice Transcribe (20+ speaker diarization real-time STT)**, **Muse Code CLI** |
| **[03-hackathon-ideas-and-lottie-motion-studio-synergy.md](file:///Users/a13973/dev/buddypia/hackathon/MetaGlobalAIDeveloperHackathon/docs/03-hackathon-ideas-and-lottie-motion-studio-synergy.md)** | In-depth analysis of the `lottie-motion-studio` architecture and hackathon alignment strategy, 3 top core ideas extending `lottie-motion-studio` (MuseMotion Studio 2.0, KineticLottie, MuseCast Live) + 3 standalone/hybrid frontier ideas, 10-day development roadmap |
| **[04-application-guide-and-draft-answers.md](file:///Users/a13973/dev/buddypia/hackathon/MetaGlobalAIDeveloperHackathon/docs/04-application-guide-and-draft-answers.md)** | Strategy tailored to the judging criteria (idea 50% + technical skill 50%) for the application deadline (**12:59 PM, October 26, 2026, Korea time**) and English model draft answers for the key narrative application questions (Q8 hackathon build plan, Q9 technical appeal of a recent AI project based on `lottie-motion-studio`) |

---

## ⚡ Executive Summary

1. **Application deadline approaching (Rolling Basis, first-come 20,000 cap)**:
   - **Application deadline**: 11:59 PM ET, October 25, 2026 (**12:59 PM KST, Monday, October 26, 2026, Korea time**)
   - **Application review criteria**: **Project idea clarity/feasibility/theme fit (50%)** + **technical depth shown in a recently built AI project (50%)** — evaluated solely on application answers, with automatic acceptance up to the first 20,000 applicants once the minimum cutoff is passed.
2. **Hackathon finals judging criteria (confirmed from the Waiver official rules)**:
   - **Impact (30%)**: Real-world potential, beneficiaries, real usability, theme fit
   - **Use of Meta AI Tooling (25%)**: How creatively Meta AI tools are combined beyond a simple API wrapper, and whether unexpected capabilities are drawn out
   - **Demo (25%)**: An impressive working demo that holds up live, and demo video quality
   - **Technical Depth & Execution (20%)**: Engineering polish and sophisticated technical depth
3. **Decisive strengths of `lottie-motion-studio`**:
   - For the application question worth 50% of the evaluation, **"technical skill in a recently built AI project (Q9)"**, the **pure curve outline decomposition (Zero-Box Contours), amodal inpainting, 11-joint 2-segment limb IK and convex joint socket mathematical integrity, ultra-low-latency motion decision engine based on EmbeddingGemma 2, and 7-column automated verification gate** of `lottie-motion-studio` give judges overwhelming engineering confidence.
   - For the finals project as well, combining the solid geometry/rigging/rendering core of `lottie-motion-studio` with **SAM 3.1** (text-prompt-based zero-shot body/prop part segmentation and video motion tracking) + **Muse Image** ($0.01/image agentic amodal inpainting and consistent character generation) + **Muse Voice Transcribe** (real-time multi-speaker voice directing and dialogue sync) + **Muse Wonder / Spark 1.3** (visual audit and autonomous repair agents for the 7-column verification sheets) can target top scores across all four judging criteria (Impact, Meta Tooling, Demo, Technical Depth).
