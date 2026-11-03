# Meta Global AI Developer Hackathon 문서 아카이브 및 아이디어 제안서

이 디렉토리는 [Meta Global AI Developer Hackathon](https://cerebralvalley.ai/e/meta-ai-developer-hackathon)의 본문, 하위 링크([Waiver 및 공식 규칙](https://cerebralvalley.ai/e/meta-ai-developer-hackathon/waiver), [Credit Terms PDF](https://cerebralvalley.ai/e/meta-ai-developer-hackathon/waiver), [Meta Developer Portal (`dev.meta.ai`)](https://dev.meta.ai/), [Meta Model API 공식 문서](https://dev.meta.ai/docs/overview), 추론 파트너 페이지 등)와 페이지 내부 Next.js 하이드레이션 메타데이터(지원서 전체 문항 포함)를 전수 조사하여 정리한 문서 세트입니다.

또한 기존에 보유하고 계신 [`lottie-motion-studio`](file:///Users/a13973/dev/buddypia/lottie-motion-studio/README.ko.md)의 핵심 기술 자산(순수 곡선 파츠 분해, 아모달 인페인팅, 11관절 2세그먼트 IK 리깅, 7컬럼 검증 게이트, 자연어 모션 결정 엔진)을 해커톤 심사 기준과 최신 Meta AI 모델 생태계에 결합한 프로젝트 아이디어 및 영문 지원서 초안을 함께 수록했습니다.

---

## 📚 문서 구성

| 문서 파일 | 핵심 내용 요약 |
| :--- | :--- |
| **[01-hackathon-overview-and-rules.md](file:///Users/a13973/dev/buddypia/hackathon/MetaGlobalAIDeveloperHackathon/docs/01-hackathon-overview-and-rules.md)** | 해커톤 일정(EST/KST 병기), 총상금 $1,000,000 상세 배분표(Indie $400k / Startup $550k / Bonus $50k), 심사 기준 및 배점(Impact 30%, Meta AI Tooling 25%, Demo 25%, Technical Depth 20%), API 크레딧($150 + 파트너 크레딧) 약관, 지원서 15개 전체 질문 명세 |
| **[02-meta-ai-models-and-tooling.md](file:///Users/a13973/dev/buddypia/hackathon/MetaGlobalAIDeveloperHackathon/docs/02-meta-ai-models-and-tooling.md)** | `dev.meta.ai` 및 공식 문서에서 확인한 신규 모델 및 도구 상세 분석: **Muse Wonder / Wonder Full**, **Muse Spark 1.3**, **Muse Spark Open (816B MoE)**, **Muse Glimmer (30B 로컬 에이전트)**, **Muse Image ($0.01 에이전틱 이미지 생성/편집)**, **SAM 3.1 (텍스트 프롬프트 이미지/비디오 분할·추적)**, **Muse Voice Transcribe (20+ 화자 분리 실시간 STT)**, **Muse Code CLI** |
| **[03-hackathon-ideas-and-lottie-motion-studio-synergy.md](file:///Users/a13973/dev/buddypia/hackathon/MetaGlobalAIDeveloperHackathon/docs/03-hackathon-ideas-and-lottie-motion-studio-synergy.md)** | `lottie-motion-studio` 아키텍처 정밀 분석 및 해커톤 연계 전략, `lottie-motion-studio` 확장형 핵심 아이디어 3선(MuseMotion Studio 2.0, KineticLottie, MuseCast Live) + 독립/하이브리드 프론티어 아이디어 3선, 10일 개발 로드맵 |
| **[04-application-guide-and-draft-answers.md](file:///Users/a13973/dev/buddypia/hackathon/MetaGlobalAIDeveloperHackathon/docs/04-application-guide-and-draft-answers.md)** | 지원 마감(한국 시간 **2026년 10월 26일 낮 12:59**) 대비 심사 기준(아이디어 50% + 기술력 50%) 맞춤 전략 및 지원서 핵심 서술형 문항(Q8 해커톤 구현 계획, Q9 `lottie-motion-studio` 기반 최근 AI 프로젝트 기술 어필) 영문 모범 답안 초안 |

---

## ⚡ 핵심 요약 (Executive Summary)

1. **지원 마감 임박 (Rolling Basis, 선착순 20,000명 캡)**:
   - **지원 마감**: 2026년 10월 25일 오후 11:59 ET (**한국 시간 2026년 10월 26일 월요일 낮 12:59 KST**)
   - **지원 심사 기준**: **프로젝트 아이디어 명확성/실현가능성/테마 적합성(50%)** + **최근 구축한 AI 프로젝트에 나타난 기술적 깊이(50%)** — 오직 지원서 답변만으로 평가하며, 최소 커트라인 통과 시 선착순 20,000명까지 자동 승인됩니다.
2. **해커톤 본선 심사 기준 (Waiver 공식 규칙 원문 확인)**:
   - **Impact (30%)**: 실제 세계에서의 잠재력, 수혜 대상, 실사용 가능성, 테마 부합도
   - **Use of Meta AI Tooling (25%)**: 단순 API 래퍼를 넘어 Meta AI 도구들을 얼마나 창의적으로 조합하고 예상치 못한 역량을 끌어냈는가
   - **Demo (25%)**: 라이브에서도 흔들리지 않는 인상적인 작동 데모 및 데모 영상 퀄리티
   - **Technical Depth & Execution (20%)**: 엔지니어링 완성도와 정교한 기술적 깊이
3. **`lottie-motion-studio`가 갖는 결정적 강점**:
   - 지원서 평가의 50%를 차지하는 **"최근 직접 구축한 AI 프로젝트 기술력(Q9)"** 문항에서 `lottie-motion-studio`의 **순수 곡선 외곽선 분해(Zero-Box Contours), 아모달 인페인팅(Amodal Inpainting), 11관절 2세그먼트 사지 IK 및 볼록 소켓(Convex Joint Socket) 수학적 무결성, EmbeddingGemma 2 기반 초저지연 모션 결정 엔진, 7컬럼 자동 검증 게이트**는 심사위원에게 압도적인 엔지니어링 신뢰도를 제공합니다.
   - 본선 프로젝트에서도 `lottie-motion-studio`의 탄탄한 기하/리깅/렌더링 코어 위에 **SAM 3.1**(텍스트 프롬프트 기반 제로샷 신체/소품 파츠 분할 및 비디오 모션 추적) + **Muse Image**($0.01/장 에이전틱 아모달 인페인팅 및 일관된 캐릭터 생성) + **Muse Voice Transcribe**(실시간 다화자 음성 디렉팅 및 대사 동기화) + **Muse Wonder / Spark 1.3**(7컬럼 검증 시트 시각 감사 및 자율 수리 에이전트)를 결합하면 4대 심사 기준(Impact, Meta Tooling, Demo, Technical Depth) 모두에서 최상위 점수를 노릴 수 있습니다.
