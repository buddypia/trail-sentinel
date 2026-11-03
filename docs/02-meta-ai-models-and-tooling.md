# 02. Meta AI 최신 모델 및 개발 도구 상세 레퍼런스 (`dev.meta.ai`)

> **출처 링크**:
> - Meta AI 개발자 포털 홈: <https://dev.meta.ai/>
> - Meta Model API 공식 문서 개요: <https://dev.meta.ai/docs/overview>
> - 모델별 상세 페이지:
>   - Muse Wonder: <https://dev.meta.ai/models/muse-wonder>
>   - Muse Spark 1.3: <https://dev.meta.ai/models/muse-spark>
>   - Muse Spark Open: <https://dev.meta.ai/models/muse-spark-open>
>   - Muse Glimmer: <https://dev.meta.ai/models/muse-glimmer>
>   - Muse Image: <https://dev.meta.ai/models/muse-image>
>   - Muse Voice Transcribe: <https://dev.meta.ai/models/muse-voice-transcribe>
>   - SAM 3.1: <https://dev.meta.ai/models/sam-3-1>
> - 지리적 이용 정책(Geographic Use Policy): <https://dev.meta.ai/legal/geographic-use-policy>

해커톤 본선 심사 기준의 **25%가 "Use of Meta AI Tooling"**(단순 연동을 넘어 Meta AI 도구들을 얼마나 창의적으로 조합하고 예상치 못한 역량을 끌어냈는가)에 배정되어 있습니다. 따라서 Meta Model API가 제공하는 전체 모델 라인업과 엔드포인트 규격을 정확히 이해하고 **멀티모달·멀티모델 파이프라인**으로 설계하는 것이 핵심입니다.

---

## 1. Meta Model API 아키텍처 및 공통 규격

- **Base URL**: `https://api.meta.ai/v1`
- **인증 방식**: `Authorization: Bearer $MODEL_API_KEY`
- **지원 프로토콜 (3종 완벽 호환)**:
  1. **Responses API (`POST /v1/responses`)**: 에이전틱 다단계 워크플로우, 추론 리플레이(reasoning replay), 서버 상태 관리, SAM 3.1 분할 및 Muse Image 멀티턴 이미지 편집 지원
  2. **Chat Completions API (`POST /v1/chat/completions`)**: 기존 **OpenAI SDK** 클라이언트에서 Base URL과 API 키만 교체하여 즉시 사용 가능
  3. **Messages API (`POST /v1/messages`)**: 기존 **Anthropic SDK** 클라이언트와 호환되는 엔드포인트
- **핵심 에이전트 기능(Capabilities)**:
  - 병렬 도구 호출(Parallel Tool Calling) 및 스트리밍 도구 인자(Streamed Tool-Call Arguments)
  - 지연 도구 탐색(Tool Search — 필요한 도구만 온디맨드로 로드해 토큰 절약)
  - 실시간 웹 검색 그라운딩(Search Grounding — 별도 RAG 구축 없이 실시간 인용 응답)
  - 구조화된 출력(Structured Output — JSON Schema 100% 준수)
  - 프롬프트 캐싱(Prompt Caching) 및 추론 강도 조절(`reasoning: { "effort": "high" }`)

---

## 2. 해커톤 핵심 모델 전체 라인업 비교표

| 모델명 | API 모델 ID | 구분 | 컨텍스트 / 입력 | 핵심 특화 역량 | 공식 가격 (Standard / Contributor) |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **Muse Wonder** | `muse-wonder-1.0` | 호스티드 API | **1M** (`1,048,576`) | 프론티어 코딩, 장시간 자율 에이전트, 서브에이전트 위임, 고급 Computer Use | 입력 **$4.00/M** (캐시 **$0.20/M**) / 출력 **$20.00/M** |
| **Muse Wonder Full** | `muse-wonder-full-1.0` | Muse Code 전용 | **1M** (`1,048,576`) | Meta 최고 성능 SOTA 모델 (DeepSWE 79.0, SWE-Marathon 57.5 1위) | Muse Code 구독 포함 ($50/월 Power, $200/월 Max) |
| **Muse Spark 1.3** | `muse-spark-1.3` / `muse-spark-1.3-contributor` | 호스티드 API | **1M** (`1,048,576`) | 고속·고효율 에이전틱 코딩, 네이티브 멀티모달(비디오·이미지·문서) 시각 추론 | Standard: 입력 **$1.25/M** (캐시 $0.15) / 출력 **$4.25/M**<br>**Contributor: 입력 $0.10/M (캐시 $0.002) / 출력 $0.20/M** |
| **Muse Image** | `muse-image-1.0` | 호스티드 API | 텍스트 + 참조 이미지 | 렌더링 전 계획·코드 실행·자기교정을 수행하는 에이전틱 이미지 생성/편집 | **$0.01 / image** (검색 그라운딩 + 추론 포함) |
| **SAM 3.1** | `sam-3.1` | 호스티드 API & 오픈웨이트 | 텍스트 프롬프트 + 이미지/비디오 | 짧은 명사구 프롬프트로 객체 검출(Box), 픽셀 정밀 분할(Mask), 비디오 ID 추적 | 이미지 **$2.50 / 1,000장** ($0.0025/장)<br>비디오 **$0.20 / 1,000프레임** |
| **Muse Voice Transcribe** | `muse-voice-transcribe-1.0` | 호스티드 API (REST & WSS) | 오디오 스트림 / 파일 | 20명 이상 실시간 화자 분리(Diarization), 발화 종료 감지, 문맥 어휘 바이어싱 | **$0.18 / 시간** ($3.00 / 1,000분) |
| **Muse Spark Open** | 오픈웨이트 (816B MoE, 42B 활성) | 자체/파트너 GPU 호스팅 | 텍스트·이미지·오디오·비디오 | 미국 연구소 최고 성능 오픈웨이트 모델, 별도 의도 해설(Commentary) 채널 지원 | Baseten($100), Modal($100), Fireworks($25) 크레딧 활용 |
| **Muse Glimmer** | 오픈웨이트 (30B, Apache 2.0) | 로컬/엣지 실행 | 멀티모달 + 텍스트 | 단일 소비자용 GPU 또는 Mac(Apple Silicon)에서 상시 구동 가능한 로컬 에이전트 | 무료 (로컬 `llama.cpp`, `vLLM`, `Ollama`, `ExecuTorch`) |

---

## 3. 모델별 심층 분석 및 해커톤 활용 포인트

### 3.1 Muse Wonder (`muse-wonder-1.0`) & Muse Wonder Full
- **특징**: 복잡한 대규모 리포지토리 엔지니어링과 수 시간 동안 중단 없이 실행되는 장기(Long-horizon) 에이전트 작업을 위해 설계된 플래그십 모델입니다.
- **벤치마크**: `Muse Wonder Full`은 OSWorld V2.1(컴퓨터 사용) 78.4, MemoryBench 85.5, DeepSWE 1.1 79.0, SWE-Marathon 57.5를 기록하며 프론티어 성능을 보입니다.
- **해커톤 활용**: 복잡한 시스템 아키텍처 설계, 멀티파일 리팩터링, 서브에이전트 오케스트레이션(4-profile agentic team, isolated git worktree fan-out)의 상위 플래너(Orchestrator)로 배치합니다.

### 3.2 Muse Spark 1.3 (`muse-spark-1.3` / `muse-spark-1.3-contributor`)
- **특징**: 에이전틱 워크플로우와 멀티모달 시각 추론에 최적화된 주력 모델입니다. 스크린샷이나 비디오 클립을 입력받아 스크립트된 단계가 아닌 실제 실행 환경을 통해 시각적 추론을 수행합니다.
- **초가성비 팁**: `muse-spark-1.3-contributor` 모드를 사용하면 입력 1M 토큰당 **$0.10**, 캐시 입력 **$0.002**, 출력 **$0.20**으로 해커톤 기본 제공 크레딧 **$150만으로도 수억~수십억 토큰**을 호출할 수 있습니다!

### 3.3 SAM 3.1 (`sam-3.1`) — Segment Anything Model 3.1
- **엔드포인트**: `POST https://api.meta.ai/v1/responses` (파일 업로드는 `POST /v1/files`)
- **특징**:
  - 기존 SAM 1/2가 점(Point)이나 박스(Box) 프롬프트를 요구하거나 레이블 없는 마스크만 반환했던 것과 달리, **SAM 3.1은 DETR 아키텍처 기반 전용 추론 엔진 위에서 짧은 텍스트 명사구 프롬프트(short noun phrase)만으로 이미지 및 비디오 내 객체를 검출(Bounding Box), 픽셀 단위로 정밀 분할(Segmentation Mask), 그리고 비디오 프레임 간 ID 유지 추적(Tracking)까지 단일 호출로 수행**합니다.
  - 별도 서버 호스팅이나 파인튜닝 없이 제로샷으로 즉시 동작하며, 이미지 1,000장당 $2.50(장당 0.25센트), 비디오 1,000프레임당 $0.20으로 매우 저렴합니다.
- **`lottie-motion-studio`와의 시너지**:
  - 단일 캐릭터 일러스트에서 `"head"`, `"torso"`, `"left arm"`, `"right arm"`, `"left leg"`, `"right leg"`, `"handheld passport"`, `"rolling suitcase"` 등 해부학적 파츠와 소품을 텍스트 프롬프트로 즉시 분리해 낼 수 있습니다.
  - 실제 사람의 동작 영상(걷기, 춤추기, 인사하기)에서 신체 부위를 프레임별로 추적해 2D 캐릭터의 Lottie 키프레임으로 리타겟팅하는 파이프라인의 핵심 시각 센서로 쓸 수 있습니다.

### 3.4 Muse Image (`muse-image-1.0`)
- **엔드포인트**:
  - 단일 생성: `POST https://api.meta.ai/v1/images/generations`
  - 정밀 편집: `POST https://api.meta.ai/v1/images/edits`
  - 멀티턴 대화형 편집: `POST https://api.meta.ai/v1/responses`
- **특징**:
  - *"An image model that reasons before it renders."* — 곧바로 픽셀을 찍어내는 대신 먼저 계획을 세우고, 웹에서 실제 레퍼런스를 검색(Search Grounding)하며, 정밀도가 필요한 곳에서는 직접 코드를 생성·실행하고, 결과를 스스로 검증(Self-correction)한 뒤 반환합니다.
  - **3대 핵심 프리미티브**:
    1. **Image Generation**: 텍스트 설명으로부터 고품질 이미지 생성 ($0.01/장)
    2. **Reasoning-Driven Precise Editing**: 지정한 영역/요소만 정확히 수정하고 나머지 픽셀은 건드리지 않는 정밀 편집
    3. **Anchored Composition**: 소수의 레퍼런스 이미지를 앵커로 삼아 여러 장의 후속 이미지 생성 시 캐릭터/스타일 일관성을 완벽히 유지
- **`lottie-motion-studio`와의 시너지**:
  - 팔이나 소품에 가려진 몸통(Torso) 뒤쪽 영역이나 캐릭터를 떼어낸 배경 판(`bg.png`)을 복원할 때, 기존 OpenCV `INPAINT_TELEA`나 단색 패치 대신 **Muse Image의 Reasoning-Driven Edit**으로 옷 주름과 배경 디테일까지 완벽히 아모달 복원(Amodal Inpainting)할 수 있습니다.
  - 또한 사용자가 텍스트만 입력해도 **Muse Image**로 리깅 친화적인 캐릭터 일러스트와 다양한 표정/소품 바리에이션(Anchored Composition)을 생성한 뒤 즉시 Lottie 애니메이션으로 변환할 수 있습니다.
- **주의사항**: Geographic Use Policy상 `Muse Image`는 인도(India) 지역 엔드유저에게는 제공이 제한됩니다(한국·미국·글로벌은 정상 사용 가능).

### 3.5 Muse Voice Transcribe (`muse-voice-transcribe-1.0`)
- **엔드포인트**:
  - 실시간 스트리밍: `wss://api.meta.ai/v1/asr/realtime`
  - 오디오 파일 배치: `POST https://api.meta.ai/v1/asr/transcribe`
- **특징**:
  - 시간당 **$0.18**(분당 $0.003)의 초저비용 스트리밍 음성 인식 모델입니다.
  - 별도 후처리 파이프라인 없이 모델 내부에서 **20명 이상의 실시간 화자 분리(Live Speaker Diarization)**와 **발화 종료 감지(Turn Detection / Endpointing)**, **문맥 및 키워드 바이어싱(Contextual & Keyword Biasing)**, **25개 언어 및 코드스위칭(한영 혼용 등)**, **턴 단위 타임스탬프(Turn-level timing)**를 기본 반환합니다.

### 3.6 Muse Glimmer (30B Open-Weight) & Muse Spark Open (816B MoE)
- **Muse Glimmer (30B, Apache 2.0)**:
  - `Muse Spark`로부터 증류(distilled)된 멀티모달 로컬 에이전트 모델로, **단일 소비자용 GPU나 Mac(`llama.cpp`, `Ollama`, `LM Studio`, `vLLM`, `ExecuTorch`)에서 상시 실행**됩니다.
  - MCP Atlas 75.5, SWE-Bench Verified 76.0, AIME 2026 94.7 등 30B급 최고 수준의 에이전트·코딩·멀티모달 성능을 자랑합니다.
  - `lottie-motion-studio`의 철학인 **"Zero-Cost Client / Local Inference"**와 완벽하게 부합하는 로컬 에이전트 두뇌입니다!
- **Muse Spark Open (816B MoE / 42B Active)**:
  - 텍스트·이미지·오디오·비디오를 모두 이해하는 초대형 오픈웨이트 모델로, 행동하기 전에 의도를 먼저 밝히는 별도의 `commentary` 채널을 지원합니다. 해커톤 파트너인 **Baseten($100), Modal($100), Fireworks($25)** 크레딧으로 호스팅 및 파인튜닝할 수 있습니다.

### 3.7 Muse Code (`muse` CLI)
- **설치 명령어**: `curl -fsSL https://dev.meta.ai/install.sh | sh` (실행: `muse`)
- **특징**: 터미널 및 CI 환경에서 동작하는 Meta의 공식 멀티에이전트 코딩 에이전트로, OS 샌드박스, 세션 리와인드, 서브에이전트 워크트리 팬아웃(Agent fan-out) 기능을 내장하고 있습니다. 해커톤 개발 과정 자체에 `Muse Code`를 활용하면 **"Use of Meta AI Tooling (25%)"** 심사 항목에서 추가적인 스토리텔링 포인트를 확보할 수 있습니다.
