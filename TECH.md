# Trail Sentinel — 기술 선정 문서

> 근거: 스펙(스코프 동결 2026-10-28), 플랫폼 결정(2026-10-28 Jun 확정: 모바일 웹앱), 현재 코드(`server.py`, `webapp/`, `trail_sentinel/`, `eval/`).
> 상태 표기: **확정/구현됨** vs **미정/리스크**를 분리한다.

## 1. 선정 표

| 영역 | 선정 기술 | 선정 이유 | 검토한 대안과 기각 이유 |
| --- | --- | --- | --- |
| 프론트엔드 | 모바일 웹앱 — vanilla JS + `getUserMedia`(후면 카메라) + Canvas 오버레이 + Web Speech API TTS + `navigator.vibrate` | 설치 없이 폰 브라우저에서 바로 실행; 카메라·음성·진동을 브라우저 표준 API만으로 커버; 데모 영상 화면녹화가 쉬움; 제출이 공개 repo+영상 중심이라 심사위원의 앱 설치를 기대하기 어려움 | 네이티브 앱(Android): 개발량 과다, 심사위원 설치 가능성 낮음 → 기각 (플랫폼 결정에서 확정). CLI 유지: Demo 배점(25%)에서 약함 → 기각. 프레임워크(React 등): 빌드 도구·의존성 대비 이득이 작음 → v1 기각 |
| 백엔드 | Python, 현재 표준 라이브러리 `http.server` (`ThreadingHTTPServer`) | 의존성 제로로 어디서든 `python3 server.py` 실행; 판정 로직(`trail_sentinel/` 패키지)을 그대로 재사용; 일정이 짧아 서버 자체에 시간을 쓰지 않음 | FastAPI/Flask: 현재 미설치, 단일 엔드포인트 규모에선 과함 → 조건부 보류 (아래 전환 조건 참조) |
| 모델 — 분할·추적 | Meta Model API의 **SAM 3.1** (텍스트 프롬프트 개념 세그멘테이션 + 추적, detect+segment+track 단일 호출) | 위장 패턴에 강한 개념 단위 분할; 텍스트 프롬프트만으로 위험 개념 추가(zero-retraining)가 핵심 차별화; API 방식이라 폰에서 추론 불가한 규모(~840M 파라미터) 문제 회피 | 온디바이스 추론: 모델 규모상 폰 실행 불가 → 기각. 일반 객체탐지(YOLO류): 고정 클래스라 커스텀 개념 추가 불가, 위장에 약함 → 기각 |
| 모델 — 우선순위 판정 | **Muse Wonder** (우선순위·거리·방향 표현·오경보 억제) — 단, v1 실시간 경로는 결정적 로직(`triage.py`)으로 구현해 병행 | 심사 배점 "Use of Meta AI Tooling"에서 SAM과의 2-모델 파이프라인이 핵심; 판정 로직을 결정적으로 유지하면 API 상태와 무관하게 데모·eval이 재현 가능 | Wonder 단독 실시간 의존: API 프리뷰 상태라 가용성 리스크 → 로직 폴백 병행 (리스크 절 참조). LLM에 매 프레임 판정 위임: 지연·비용·재현성 문제 → 기각 |
| 모델 — 보조 | Muse Spark (위험 리포트, 종 판별 보조 설명 — 사후 경로), Muse Image (데모·테스트 이미지 보강 — 실시간 경로 제외) | 스펙의 모델 역할 분담 그대로; 실시간 경로를 가볍게 유지 | 실시간 경로에 포함: 지연·비용 증가 → 기각 |
| 음성 | Web Speech API (`speechSynthesis`, ko-KR) | 폰 브라우저 내장, 추가 비용·지연 없음, 오프라인 성분 있음; 경고 문장이 짧아 품질 요구가 낮음 | 서버 TTS 합성: 왕복 지연+비용, 네트워크 의존 → 기각. 백엔드 `alerts.speak()`는 자리표시자(출력만)로 남기고 실제 발화는 브라우저가 담당 |
| 호스팅 | 로컬 실행 (`localhost:8765`) — 폰 프리뷰용 배포는 **미정** (리스크 절) | 현재 단계(스텁 검증)에는 로컬로 충분; 카메라 제약(HTTPS/localhost)을 배포 시점에 해결 | 확정 보류 — 후보와 조건은 리스크 절에 명시 |
| 데이터 | fixture JSON (스텁 응답), eval용 라벨 manifest JSON, 호출 카운터 JSON 파일 | 의존성·DB 없이 버전관리 가능; eval 재현성 확보; 권리 있는 테스트 영상만 쓴다는 룰과 함께 관리 | DB 도입: 이 규모(클립 수십 개, 카운터 1개)에 과함 → 기각 |
| 지출 가드 | 클라이언트 카운터 (`CallBudget`, JSON 파일, 일일 상한 기본 200회) | Meta Billing의 Spend Limit는 알림일 뿐 강제 상한이 없음이 확인됨 → 물리적 차단은 클라이언트 카운터 + 필요 시 저한도 카드가 유일한 수단 | Billing 알림만 신뢰: 강제 차단이 아니라 사고 후 인지 수준 → 단독 채택 기각 (병행은 가능) |
| eval | 로컬 Python 스크립트 (`eval/score.py`) | 클립 라벨(manifest) 대비 감지율·경고 리드타임·오경보율을 자동 계산; 외부 서비스 불필요 | 수동 평가: 재현성·비교 불가 → 기각 |

### FastAPI 전환 조건

아래 중 하나가 필요해지면 표준 라이브러리 서버에서 FastAPI로 전환한다.

- 실제 프레임 이미지 업로드(멀티파트/대용량 base64) 처리가 복잡해질 때
- 동시 접속·비동기 API 호출(SAM/Wonder 병렬)이 병목이 될 때
- 배포 환경이 ASGI 서버를 전제로 할 때

## 2. 확정 사항 (구현 완료 포함)

- **플랫폼**: 모바일 웹앱 (2026-10-28 확정). 폰 브라우저 카메라 → 백엔드 → SAM API → 화면 표시+음성·진동.
- **프론트엔드**: `webapp/index.html`, `app.js`, `style.css` (vanilla). 후면 카메라 전체화면, Canvas에 bbox+라벨 오버레이 (현재 마스크 폴리곤이 아닌 bbox), 경고 배너, ko-KR TTS, 진동 패턴(위험 `[250,100,250]`, 주의 `[150]`), 약 1.2초 스캔 주기, 데모 모드(히어로 fixture 프레임 0..60 재생).
- **백엔드**: `server.py` — `GET /`(웹앱 서빙), `GET /api/status`(모드·호출 카운터·개념 목록), `POST /api/scan`(프레임 1장 판정). 기존 `config.py`/`sam_client.py`/`triage.py`를 재사용하고 프레임 어댑터만 추가.
- **판정 로직**: `triage.py` — 심각도별 경고 거리 {3: 3.0m, 2: 2.5m, 1: 1.0m}, 점수 = 심각도×2×근접도 + 접근속도(상한 2.0) + 신뢰도, 트랙별 쿨다운 30프레임. 경고 문장 규칙 "방향 + 거리 + 대상" (예: "발 앞 3미터, 뱀").
- **SAM 3.1 과금 전제**: 이미지 $2.50 / 1k images, 비디오 프레임 $0.20 / 1k video frames (안내 단가). 프레임 추출 간격이 곧 비용 — 라이브는 스캔 주기를 제한하고, 총 프레임 예산을 먼저 정해 $150 크레딧 안에서 운용한다.
- **지출 가드**: `CallBudget.spend()`가 상한 초과 시 예외, 서버는 캡 도달 시 `daily_call_cap_reached`를 반환하고 스캔을 막는다.
- **Meta connector 상태 (2026-10-31 live 검증)**: base URL `https://api.meta.ai/v1`, `POST /v1/responses` + 모델 `sam-3.1` (제품 페이지 표기 `sam-3-1`과 다름에 주의), stream + `mask_encoding=one_bit`, 개념당 프롬프트 1개. `GET /v1/models`로 인증 확인 (모델 9종, `sam-3.1` 포함). 히어로 스틸 분할 실호출에서 box+mask 1건, 3.0초, $0.0025 (Jun의 $150 credit 내). 좌표는 이미지 픽셀 공간이며 record의 `w`/`h`는 프레임 크기다. 출력에 confidence와 distance가 없다 — confidence는 `None`으로, 거리는 ground-plane 휴리스틱 추정치로 처리한다. 검증 원본과 호출 기록은 `~/workspace/custom-connectors/custom.meta-model-api/API_RESEARCH.md`.
- **폴백 원칙**: API/네트워크 실패 시 캐시 응답 재생 + 화면 표시 의무(라이브인 척 금지), 지연 과다 시 "확인 불가" 표시.
- **라이브 스캔 연결 (2026-10-31, F1)**: 서버는 `TRAIL_SENTINEL_LIVE=1`일 때만 live 모드로 뜬다(기본 스텁 — 우발 지출 방지). 웹앱 카메라 모드는 실제 프레임을 긴 변 ≤1024px JPEG data URL로 캡처해 선택 개념(칩 토글, 기본 전체)과 함께 전송한다. 서버 `LiveScanner`는 개념마다 `SegmentRequest`를 분리해 병렬 실행하므로 `CallBudget`이 개념 콜 단위로 정확히 센다. 서버측 최소 스캔 간격 2.5초, 호출당 타임아웃 10초(transport), 예산 사전 점검(스캔 전체가 캡에 안 들어가면 호출 없이 `daily_call_cap_reached`), 전체 실패 시 `live_scan_failed`를 정직하게 반환한다. 프론트는 첫 실패부터 "확인 불가" 배지를 띄우고 성공할 때까지 유지한다(3회 연속 시 상태줄에 사유 병기). 라이브 접근 속도는 연속 스캔의 벽시계 실측 간격으로 환산한 fps를 `triage.evaluate`에 넘긴다(판정 로직 무변경). 마스크는 `meta-sam-parser`(tools/pylibs에 설치)로 서버에서 디코딩해 심각도 색상의 RGBA PNG(≤256px)로 내려보내고, 실패하면 bbox만 그리는 폴백이다. 실측: 서버 경유 스캔 1회(개념 1개) 지연 6.1초 — PRD 9.2 목표 미달이며, 3.0초 경고 유효 기간 강제는 보류 중(강제 시 라이브 경고 대부분이 버려짐).
- **라이브 비용 구조 (실측 단가 기준)**: 개념 1콜 = 이미지 1장 = $0.0025. 6개념 풀스캔 1회 = **$0.015**. 서버 최소 간격 2.5초를 이론 최대(24스캔/분)로 돌리면 6개념 기준 $21.60/시간까지 갈 수 있지만, 그 전에 일일 캡 200콜이 걸린다 — 200콜 = 풀스캔 약 33회분 = **하루 최대 $0.50**. 프론트 기본 주기(5초 틱 + 동시 요청 1건)에서는 시간당 최대 12스캔($10.80/시간 상당)이지만 역시 캡이 먼저 소진된다. 즉 현재 구조에서 지출의 물리적 상한은 단가가 아니라 `CallBudget` 캡이다.

## 3. 미정 / 리스크

| 항목 | 상태 | 대응 |
| --- | --- | --- |
| Muse Wonder API 가용성 | API 프리뷰 상태, 실제 호출 가능 여부 미확인 | 실시간 판정은 결정적 로직(`triage.py`)으로 이미 동작하게 유지. Wonder 연동이 막히면 판정 표현·리포트 생성에 **Muse Spark로 대체**하고, 그 사실을 제출 자료에 명시 |
| 실제 SAM endpoint·스키마 | **해결 (2026-10-31 live 검증)**: `POST /v1/responses`, 모델 `sam-3.1`, 구조화 텍스트 출력까지 실호출로 확인. 남은 리스크는 스키마 자체가 아니라 운용 — distance가 출력에 없어 휴리스틱 추정치에 의존하고, 개념 프롬프트당 1콜이라 프레임당 비용이 프롬프트 수에 비례 | 거리는 ground-plane estimator로 채우되 "추정치"로 명시하고 실측 사진으로 캘리브레이션한다. 라이브 스캔은 프롬프트 수를 줄이거나 프레임 간격을 넓혀 총콜을 `CallBudget` 안에 둔다. video 경로는 wire 문서만 있고 미실측 — 이미지 예산이 생길 때 별도 검증 |
| 실제 프레임 전송 경로 | **해결 (2026-10-31)**: 웹앱이 실제 프레임(JPEG data URL)을 전송하고 서버 live 모드가 실 SAM으로 응답. base64 JSON 전송으로 충분해 FastAPI 전환은 불필요했음 | 남은 리스크는 지연(스캔 6.1초 실측)과 배포 — 아래 배포 행 참조 |
| 폰 프리뷰용 배포 | 미정. 카메라는 HTTPS 또는 localhost에서만 동작 | 후보: Cloudflare Tunnel(로컬 서버 노출, 빠름), Render 등 PaaS(상시 실행, 콜드스타트 주의). 제출용 공개 repo와 별개로, 데모 촬영 환경을 기준으로 후속 확정 |
| API credential | Jun이 발급했고 Secure Vault의 `custom.meta-model-api` connection에 등록 완료. 2026-10-31에 `models`와 `segment-image` live 검증까지 통과 | project server는 credential을 직접 읽지 않는다. connector helper는 `dynamic_credentials.py`의 `hsurr:` surrogate만 사용하고, project의 live transport는 helper를 subprocess로 부르는 방식으로만 API에 닿는다 |
| 크레딧 반영 | **확인 완료 (2026-10-31)**: Jun이 $150 credit 수령을 확인. 검증 런 실사용 $0.0025 | 이후 실호출도 credit 범위 + `CallBudget` + 작업별 호출 상한 안에서만 운용한다 |
| 테스트 영상 권리 | 히어로 장면(낙엽 속 뱀) 실영상 확보 미완 | 직접 촬영 또는 라이선스 확인된 소스만 사용 (룰: 권리 없는 데이터 사용 시 실격) |

## 4. 아키텍처

```
┌───────────────────────── 폰 브라우저 (webapp/) ─────────────────────────┐
│  getUserMedia 후면 카메라 ──▶ <video> 전체화면                          │
│  스캔 틱 (데모 1.2초 / 라이브 5초) ──▶ POST /api/scan {frame_index | 프레임 이미지 + 개념 목록} │
│  응답 수신 ──▶ Canvas 오버레이 (bbox + "뱀 2.6m" 라벨)                  │
│  경고 시 ──▶ 빨간 배너 + speechSynthesis(ko-KR) + navigator.vibrate     │
│  데모 모드 ──▶ 카메라 없이 히어로 장면 프레임 0..60 재생                 │
└──────────────────────────────┬───────────────────────────────────────────┘
                               │ HTTP (로컬: localhost / 배포 시 HTTPS)
┌──────────────────────────────▼──────────── 백엔드 (server.py, Python) ──┐
│  GET /api/status · POST /api/scan                                       │
│  CallBudget.spend() ── 일일 호출 상한 체크 (JSON 카운터)                 │
│        │                                                                │
│        ▼                                                                │
│  SAMClient.segment()                                                    │
│    ├─ StubSAMClient  (현재: fixtures/*.json canned 응답)                │
│    └─ RealSAMClient (서버 live 모드에서만 생성) ──▶ meta_transport (+ 마스크 디코딩) ──▶ connector helper subprocess ──▶ Meta Model API (api.meta.ai/v1, sam-3.1) │
│        │ Detection[] (개념, 거리, 신뢰도, track_id, bbox)                │
│        ▼                                                                │
│  triage.evaluate() ─ 심각도×근접도+접근속도 점수, 경고 거리, 쿨다운      │
│    (Muse Wonder 역할 — v1은 결정적 로직, Wonder/Spark 연동은 계획)      │
│        │ AlertDecision (최고 위험 1건만)                                 │
│        ▼                                                                │
│  JSON 응답 {detections, alert{text_ko, level}, calls_today, cap}         │
└──────────────────────────────────────────────────────────────────────────┘

  병행 경로 (실시간 아님):
    eval/score.py ── clips_manifest(라벨) + results ──▶ 감지율·리드타임·오경보율
    Muse Spark* ── 위험 리포트 생성 (기록 화면, 계획)
    Muse Image* ── 데모·테스트 이미지 보강 (계획)

  * = 계획/미구현. 무표시는 현재 코드로 동작.
```

## 5. 파일 대응표

| 파일 | 역할 |
| --- | --- |
| `server.py` | 웹 백엔드 (표준 라이브러리 http.server), `/api/scan`·`/api/status`. 스텁 데모 경로 + opt-in 라이브 경로(`LiveScanner`: 개념별 병렬 호출, 최소 간격 2.5초, 예산 사전 점검) |
| `webapp/index.html`, `app.js`, `style.css` | 모바일 웹 프론트엔드 (실프레임 캡처·개념 칩 선택·"확인 불가" 상태·마스크 오버레이) |
| `trail_sentinel/config.py` | 위험 개념 v1(6개), 등록 host 상수, `CallBudget` 지출 가드 (스레드 안전). credential을 읽지 않음 |
| `trail_sentinel/sam_client.py` | `SAMClient` 인터페이스, `StubSAMClient`, 기본 비활성인 주입형 `RealSAMClient` adapter. `Detection`에 마스크 PNG/rect 선택 필드 |
| `trail_sentinel/meta_transport.py` | live SAM transport (connector helper subprocess), 실응답 매핑, ground-plane 거리 추정, `meta-sam-parser` 기반 마스크 디코딩 (best-effort) |
| `tools/pylibs/` | `meta-sam-parser` 설치 위치 (pip --target). 없으면 마스크만 비활성화되고 bbox로 폴백 |
| `tests/test_sam_client.py`, `tests/test_meta_transport.py`, `tests/test_server_live.py` | mock/실응답 fixture/가짜 클라이언트 기반 단위 테스트 (`tests/fixtures/sam_hero_snake_raw.txt`가 실응답 원본) |
| `~/workspace/custom-connectors/custom.meta-model-api/` | connector 문서, surrogate helper, 공식 조사 기록 `API_RESEARCH.md` |
| `trail_sentinel/triage.py` | 우선순위 판정, 경고 문장 생성 |
| `trail_sentinel/pipeline.py` | 녹화 영상 경로 (프레임→SAM→판정→경고, CLI/평가용) |
| `trail_sentinel/alerts.py` | CLI 경로 경고 출력 (브라우저 TTS와 별개의 자리표시자 포함) |
| `fixtures/hero_snake_leaves.json` | 히어로 장면 스텁 응답 |
| `eval/score.py`, `*.example.json` | 평가 하네스와 라벨/결과 포맷 예시 |
| `main.py` | CLI 스텁 데모 |
