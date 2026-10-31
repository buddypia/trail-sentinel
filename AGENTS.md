# AGENTS.md — Trail Sentinel

> 이 repo에서 작업하는 AI 에이전트·개발자용 진입점. 상세는 아래 문서 지도를 따라가라. 이 파일은 포인터와 현재 상태만 담는다.

**한 줄 요약**: 폰 카메라로 등산로를 스캔해 SAM 3.1(텍스트 프롬프트 개념 분할)이 위험을 찾고, 우선순위 판정이 위험할 때만 음성+진동으로 경고하는 개인용 야외 위험 센티넬. Meta Global AI Developer Hackathon, Indie 트랙, Push the Frontier. 제출 마감 **2026-11-05 11:00 JST (Nov 4 21:00 ET)**.

**현재 단계**: 스텁 파이프라인 + 모바일 웹앱 동작. Meta Model API는 2026-10-31 live 검증 완료 — `GET /v1/models`에서 `sam-3.1` 확인, 히어로 카퍼헤드 스틸에 prompt `snake`로 분할 호출 성공 (box+mask 1건, 3.0초, $0.0025, Jun의 $150 credit 내). `trail_sentinel/meta_transport.py`가 connector helper subprocess 경유 live transport와 실응답 기반 매핑·거리 추정(추정치)을 제공하고, `RealSAMClient`는 기본 비활성·`CallBudget` 필수인 채로 그대로다. **F1 연결 완료 (2026-10-31)**: 웹앱이 실제 카메라 프레임을 전송하고, 서버는 `TRAIL_SENTINEL_LIVE=1`일 때만 live 모드로 실 SAM을 호출한다 (기본값 스텁). 서버 경유 실호출로 히어로 스틸에서 뱀 감지+경고+마스크까지 확인 (스캔 지연 6.1초 실측 — PRD 목표 미달). 서버는 아직 이 VM에서만 실행되며 폰 배포는 미완. 요구의 기준은 `PRD.md` (v0.4).

## 먼저 읽을 문서 지도

| 질문 | 파일 |
| --- | --- |
| 무엇을·왜 만드는가 (범위, 기능 F1–F11, 수용 기준, SLO) | `PRD.md` |
| 어떻게 만드는가 (기술 선정, 아키텍처, 미정·리스크) | `TECH.md` |
| 동결된 범위 원본 (2026-10-28 결정 기록) | `../files/meta-hackathon-trail-sentinel-spec/meta-hackathon-trail-sentinel-spec.md` |
| 실격 방지 (룰 전문) | `../files/meta-hackathon-rules.md` |
| 실행법 | `README.md`, 아래 "실행·검증 명령" |

충돌 시 우선순위: 룰 > PRD > 스펙 > TECH (근거는 PRD 0.3절).

## 아키텍처 요약

폰 브라우저(`webapp/`: getUserMedia 카메라 + Canvas 오버레이 + ko-KR TTS + 진동)가 스캔 틱(데모 1.2초 / 라이브 5초)마다 `POST /api/scan`을 보낸다. 백엔드(`server.py`, Python 표준 라이브러리)는 데모 요청에는 `StubSAMClient`를, 이미지 요청에는 live 모드(`TRAIL_SENTINEL_LIVE=1`)에서만 `LiveScanner`를 쓰며, 양쪽 다 `CallBudget` 지출 가드를 거치고 `triage.evaluate()`가 심각도×근접도+접근속도로 최고 위험 1건만 골라 경고 문장("발 앞 3미터, 뱀")을 만든다. `LiveScanner`는 개념마다 요청을 분리해 병렬 호출하므로 예산은 개념 콜 단위로 센다. live transport(`meta_transport.MetaSAMTransport`)는 connector helper를 subprocess로 불러 Meta API에 닿고 (credential은 project에 들어오지 않음), SAM이 confidence·distance를 주지 않으므로 confidence는 `None`, 거리는 ground-plane 휴리스틱 추정치로 채운다. 마스크는 `meta-sam-parser`(tools/pylibs)로 디코딩해 PNG 오버레이로 내려보낸다 (실패 시 bbox 폴백). eval은 `eval/score.py`가 라벨 manifest 대비 감지율·리드타임·오경보율을 계산한다.

## 핵심 파일 인덱스

| 파일 | 역할 |
| --- | --- |
| `PRD.md` / `TECH.md` | 요구사항 / 기술 선정 (현행 기준 문서) |
| `server.py` | 웹 백엔드 — `GET /`, `GET /api/status`, `POST /api/scan`. 데모 프레임 어댑터 + 라이브 `LiveScanner`(개념별 병렬 호출·최소 간격 2.5초·예산 사전 점검)와 쿨다운 상태 보유. 라이브는 `TRAIL_SENTINEL_LIVE=1` opt-in |
| `webapp/index.html`, `app.js`, `style.css` | 모바일 웹 프론트엔드 (카메라·오버레이·배너·TTS·진동·데모 모드) |
| `trail_sentinel/config.py` | 위험 개념 v1 6개(`HAZARDS`), 등록 host 상수, `CallBudget` 지출 가드. credential을 읽지 않는다 |
| `trail_sentinel/sam_client.py` | `SAMClient` 인터페이스, `Detection`, `StubSAMClient`, 기본 비활성인 주입형 `RealSAMClient` adapter |
| `trail_sentinel/meta_transport.py` | live SAM transport — connector helper subprocess 호출, 실응답 record→정규화 매핑, ground-plane 거리 추정(추정치), 마스크 디코딩(`tools/pylibs`의 `meta-sam-parser`, best-effort) |
| `tests/test_sam_client.py`, `tests/test_meta_transport.py`, `tests/test_server_live.py` | mock/recorded/가짜 클라이언트 기반 단위 테스트 (네트워크·실호출 없음). 실응답 fixture는 `tests/fixtures/sam_hero_snake_raw.txt` |
| `~/workspace/custom-connectors/custom.meta-model-api/` | Meta Model API connector 문서·helper·조사 기록. `models`와 `segment-image`는 2026-10-31 live 검증 완료, `segment-video`는 비활성 |
| `trail_sentinel/triage.py` | 우선순위 점수·경고 거리·쿨다운 상수, 경고 문장 생성 (Wonder 역할의 결정적 로직) |
| `trail_sentinel/pipeline.py` | 녹화 영상·CLI 경로 파이프라인 (프레임→SAM→판정→경고) |
| `trail_sentinel/alerts.py` | CLI 경로 경고 출력 (TTS/진동은 자리표시자 — 실제 발화는 브라우저 담당) |
| `main.py` | CLI 스텁 데모 진입점 |
| `fixtures/hero_snake_leaves.json` | 히어로 장면 스텁 응답 (뱀 6.0m→1.6m 접근) |
| `eval/score.py`, `eval/*.example.json` | 평가 하네스와 라벨/결과 포맷 예시 |
| `eval/data/` | 수집된 테스트 사진·영상. **출처 기록(`SOURCES.md`) 정리 전에는 제출 자료에 쓰지 말 것** |

## 현재 상태 (솔직한 표)

| 영역 | 상태 | 사실 |
| --- | --- | --- |
| 판정 로직 (F4), 경고 출력 (F5), 데모 모드 (F6), 지출 가드 (F8) | 구현됨 | 웹·CLI 양쪽에서 동작. 경고는 최고 위험 1건, 쿨다운·문장 중복 억제 적용 |
| SAM 분할 (F2) | 구현됨 (이미지) | live 검증 완료 (2026-10-31): models 목록에서 `sam-3.1` 확인, 히어로 스틸 분할에서 box+mask 1건 반환. `meta_transport`가 helper subprocess 경유 live transport + 실응답 파서 기반 매핑 + 마스크 디코딩을 제공하고, 서버 live 경로에 연결됨. SAM 출력에 confidence·distance가 없어 confidence는 `None`, 거리는 추정치. 비디오 경로는 미실측 |
| 라이브 스캔 (F1) | 구현됨 (서버 로컬) | 웹앱이 실제 프레임을 캡처·전송하고 서버 live 모드(`TRAIL_SENTINEL_LIVE=1`)가 개념별 병렬 실호출 후 판정·경고 반환. 서버 경유 실호출 검증 완료 (뱀 감지, 스캔 지연 6.1초 실측). 최소 간격 2.5초·호출당 10초 타임아웃·예산 사전 점검·"확인 불가" 표시 포함. 단 서버는 이 VM에서만 실행 — 폰 배포(HTTPS)는 미완이라 폰 실기 검증은 안 됨 |
| 추적·거리 (F3) | 부분 | fixture 거리 보간(스텁). 라이브 접근 속도는 연속 스캔의 벽시계 실측 간격으로 환산 (2026-10-31 해소). 거리는 여전히 ground-plane 추정치로 미캘리브레이션 |
| 화면 표시 | 구현됨 | live 감지는 마스크 PNG 오버레이 + bbox를 함께 그림 (마스크 디코딩 실패·스텁은 bbox만) |
| 개념 추가 (F7), 기억 (F10), 리포트 (F11) | 계획 | 동적 추가 API/UI 없음. 개념은 `config.HAZARDS` 고정 6개 |
| 캐시 폴백 | 계획 | 재생 로직 없음. 현재 스텁 fixture가 사실상 그 역할을 대신함. 데모 배지만 구현 |
| 지연 계측 | 부분 | 서버가 live 스캔마다 `latency_ms`를 반환하고 프론트가 상태줄에 표시 (실측 6.1초/개념 1개 — PRD 9.2 목표 미달). 캡처→경고 전 구간 분해 계측과 3.0초 경고 유효 기간 강제는 미구현 (강제 시 라이브 경고 대부분이 버려져 보류, PRD 9.2 참조) |
| eval 실측 | 부분 | 스코어러 동작. `eval/data/`에 실제 파일 14개 + `SOURCES.md` + `clips_manifest.json` 작성됨. 아직 실측 미실행. `score.py` 오경보율 분모 정의 불일치 존재 (PRD F9) |
| 앱 화면 안전 고지 | 구현됨 | 웹 화면에 "보조 도구 — 안전 보장 안 함, 오탐·미탐 가능" 고지 표시 (2026-10-29) |
| 스캔 동시 요청 제한 | 구현됨 | `app.js`가 진행 중인 스캔 1건만 유지, 겹치는 요청을 보내지 않음 (2026-10-29) |

## 실행·검증 명령

```bash
cd trail-sentinel

# CLI 스텁 데모 (키·네트워크 불필요) — 뱀 경고 1회 + 쿨다운 억제가 보이면 정상
python3 main.py

# 웹앱 서버 (기본 포트 8765, PORT 환경변수로 변경)
python3 server.py
# 라이브 모드 (실 SAM 호출 — 크레딧 지출. opt-in일 때만)
TRAIL_SENTINEL_LIVE=1 python3 server.py
curl -s localhost:8765/api/status
curl -s -X POST localhost:8765/api/scan -H 'Content-Type: application/json' \
  -d '{"frame_index": 45, "mode": "demo", "reset": true}'   # "발 앞 3미터, 뱀" 경고가 와야 함
curl -s -X POST localhost:8765/api/scan -H 'Content-Type: application/json' \
  -d '{"frame_index": 0, "mode": "demo", "reset": true}'    # alert: null 이어야 함

# eval 스코어러 (예시 데이터)
cd eval && python3 score.py

# RealSAM adapter mock 테스트 (프로젝트 루트에서, 네트워크 없음)
python3 -m unittest discover -s tests -v
```

주의: 브라우저 카메라는 HTTPS 또는 localhost에서만 동작한다. `/api/scan` 호출마다 지출 가드 카운터가 오른다 (스텁 포함).

## 절대 규칙 (가드레일)

- **API 키를 코드·문서·git·채팅·로그 어디에도 쓰지 않는다.** 키는 Secure Vault의 `custom.meta-model-api` connection에만 두고, project server가 직접 읽지 않는다. connector helper도 `hsurr:` surrogate만 다룬다.
- **유료 live 호출 선행 조건**: Jun이 $150 credit 수령을 확인함 (2026-10-31). 그래도 실호출은 항상 `CallBudget`을 거치고, 작업 단위로 정한 호출 상한(예: 검증 런 6회)을 넘기지 않는다.
- **권리 없는 데이터 사용 금지.** 테스트 영상·이미지는 직접 촬영 또는 라이선스 확인된 것만. 출처를 `eval/data/SOURCES.md`에 기록하기 전에는 어떤 파일도 제출 자료에 쓰지 않는다. 유튜브 등 무단 다운로드 금지.
- **신규 작업 기간(2026-10-26 – 11-04) 밖의 코드를 기간 내 작업이라고 주장하지 않는다.** 기여 식별이 안 되면 실격이다. 기존 자산(브라우저 API, Meta 모델)과 신규 구현을 구분해 적는다.
- **지출 가드를 우회하지 않는다.** `CallBudget`을 거치지 않는 실호출 경로를 만들지 않는다. Meta Billing에는 강제 상한이 없다 — 이 가드가 유일한 물리적 방벽이다.
- **포지셔닝**: 이 제품을 "simple image analyzer"로 기술하지 않는다 (룰의 회피 목록). 항상 **실시간 능동 경고 시스템**(연속 스캔·추적·우선순위 판정·음성 경고)으로 쓴다.
- **안전 보장 표현 금지.** "안전을 보장/예방한다"고 쓰지 않는다. 보조 도구이며 오탐·미탐이 있음을 명시한다. 종 판별을 근거로 안전 판정을 하지 않는다.
- **정직성 표시 의무**: 캐시·스텁·데모 재생을 라이브처럼 보이게 하지 않는다. 배지·상태 표기를 유지한다. 지연이 크면 늦은 경고 대신 "확인 불가"로 표시한다.
- **수치 날조 금지**: 실측하지 않은 성능·정확도 수치를 목표와 섞어 쓰지 않는다. 목표에는 "목표", 실측에는 측정 조건을 붙인다.

## 다음 작업 큐

1. **배포 + 지연 단축** — F1 연결은 완료 (2026-10-31). 남은 일: 폰에서 열 수 있는 HTTPS 배포와 폰 실기 검증, 스캔 지연 단축(실측 6.1초 — subprocess 기동·순차 인증 교환이 의심 구간), 거리 추정 휴리스틱을 실측 거리 사진으로 캘리브레이션, eval 데이터셋 대상 live 측정 (프롬프트당 1콜 과금이라 총콜 예산을 먼저 정할 것).
2. **eval 실측** — `eval/data/SOURCES.md` 작성 → 라벨 manifest 작성 → 기준선 1차 측정. `score.py` 오경보율 분모 정의를 하나로 통일한다.
3. **지연 계측** — 클라이언트·서버 타임스탬프를 남겨 PRD 9.2절 SLO를 실측 가능하게 만든다. 경고 유효 기간(3.0초) 검사와 동시 요청 1건 제한도 이때 넣는다.
4. **F7 구현** — 개념 동적 추가 API + 입력 UI (데모의 라이브 확장 장면이 걸려 있다).
5. **배포** — 폰 프리뷰·데모 촬영용 HTTPS 경로 확정 (후보와 조건은 TECH.md 리스크 절). repo public 전환 전 시크릿 점검.

## 작업 관례

- 문서와 코드가 어긋나면 **둘 다 고치고** PRD 변경 이력에 남긴다. 불일치를 발견하면 숨기지 말고 해당 문서의 "알려진 한계"에 적는다.
- 상태 표기(구현됨/부분/계획)를 낙관적으로 올리지 않는다. 실제로 동작 확인한 것만 "구현됨"이다.
- 스코프를 바꾸는 결정(히어로 장면, 개념 수, 테마)은 Jun 확인 없이 하지 않는다.
