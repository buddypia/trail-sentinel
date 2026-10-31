# Meta Global AI Developer Hackathon — 공식 요구사항 및 Trail Sentinel 준수성 감사 보고서

> **최종 갱신일**: 2026-10-31
> **출처**:
> 1. 공식 이벤트 페이지: <https://cerebralvalley.ai/e/meta-ai-developer-hackathon> (`meta-ai-developer-hackathon.md`)
> 2. 공식 규칙 및 Waiver: <https://cerebralvalley.ai/e/meta-ai-developer-hackathon/waiver> (`Credit Terms` 포함)
> 3. Meta AI 개발자 포털: <https://dev.meta.ai/docs/overview>
> 4. 프로젝트 내부 기준 문서: [`PRD.md`](./PRD.md) (v0.5), [`AGENTS.md`](./AGENTS.md), [`TECH.md`](./TECH.md), [`DEPLOY.md`](./DEPLOY.md)

---

## 파트 1. Meta Global AI Developer Hackathon 공식 요구사항 정리

### 1. 대회 개요 및 일정
- **주최**: Meta & Cerebral Valley
- **진행 방식**: 100% 온라인 (Worldwide Virtual)
- **해커톤 개발 기간**: **2026-10-26 12:00 PM EDT ~ 2026-11-04 09:00 PM EST**
  - 한국/일본 표준시(KST/JST) 기준 마감: **2026-11-05 (목) 11:00 AM KST/JST**
- **제출 포털**: <https://cerebralvalley.ai/e/meta-ai-developer-hackathon/hackathon/submit>
- **출품 트랙 및 상금 (총 $1,000,000)**:
  - **Indie Developer Track ($400,000)**: 개인 빌더·학생·4인 이하 팀 (1등 $150k, 2등 $100k, 3등 $75k, 4등 $50k, 5등 $25k) — *창의성(Creativity), 기술적 야심(Technical Ambition), 실제 작동 여부(Whether it works) 중점*
  - **Startup Track ($550,000)**: 기술 창업자 및 스타트업 팀 (1등 $250k 등)
  - **Bonus Prizes ($50,000)**: Community Vote Award, Most Viral Project Award 등
- **Trail Sentinel 출품 트랙 및 테마**:
  - **트랙**: **Indie Developer Track** (1인 솔로 개발: Jun)
  - **테마**: **Push the Frontier** (*"Give a machine a new capability... Show us what becomes possible when these models meet the real world."*)

---

### 2. 공식 심사 기준 및 배점 (Judging Criteria — 100%)

| 심사 항목 | 배점 | 공식 세부 평가 기준 |
| :--- | :---: | :--- |
| **1. Impact (임팩트)** | **30%** | 실제 세계에서의 잠재력(real-world potential), 수혜 대상의 명확성, 문제의 중요도, 사람들이 실제로 사용할 수 있는 제품인가, 선택한 테마(`Push the Frontier`)에 부합하는가 |
| **2. Use of Meta AI Tooling (Meta AI 도구 활용도)** | **25%** | **Meta의 AI 모델(`SAM 3.1`, `Muse Wonder`, `Muse Spark`, `Muse Image`, `Muse Voice Transcribe`, `Muse Glimmer` 등) 및 도구를 얼마나 창의적으로 활용했는가**, 단순 기본 연동(basic integration)을 넘어 예상치 못한 새로운 역량을 끌어냈는가 |
| **3. Demo (데모 완성도)** | **25%** | 인상적이고 실제로 작동하는 데모가 있는가, **라이브 환경에서도 제품이 제대로 버티는가(holds up live)**, 3분 데모 영상의 완성도가 높은가 |
| **4. Technical Depth & Execution (기술적 깊이 및 실행력)** | **20%** | 엔지니어링이 견고하고 사려 깊게 다듬어졌는가, 프로젝트가 진정한 기술적 장인정신(real craft)을 보여주는가 |

---

### 3. 필수 제출물 및 실격 방지 규칙 (Mandatory Rules & Disqualification Gates)

1. **Meta AI 모델 필수 활용 (Core Tooling Requirement)**
   - 제출 프로젝트는 Meta Model API(`SAM 3.1`, `Muse Wonder`, `Muse Spark 1.3`, `Muse Image`, `Muse Voice Transcribe`) 또는 Meta 오픈웨이트 모델(`Muse Spark Open`, `Muse Glimmer`)을 핵심 기능으로 사용해야 함.
2. **신규 작업 기간 엄수 & 기여 식별 가능성 (New Work Only)**
   - 해커톤 공식 기간(**2026-10-26 ~ 2026-11-04**) 내에 작성된 작업물만 평가 대상임.
   - 기존 오픈소스·브라우저 표준 API·외부 자산과 해커톤 기간 중 새로 작성한 코드를 심사위원이 명확히 구분할 수 있어야 함(구분 불가 시 실격).
3. **공개 GitHub 저장소 필수 (Public Repository)**
   - 제출 시 전체 소스 코드가 담긴 GitHub 저장소를 **Public**으로 공개해야 하며, 심사위원이 클론하여 구조를 검증·실행할 수 있어야 함.
   - 저장소와 커밋 이력에 **API 키·시크릿이 절대 포함되지 않아야 함**.
4. **3분 데모 영상 필수 (3-Minute Demo Video)**
   - 심사 1·2단계의 핵심 증거 자료로, 최대 3분 길이의 실제 작동 데모 영상을 제출해야 함.
5. **데이터·코드·미디어 저작권 및 라이선스 준수 (Authorized Assets Only)**
   - 권리 없는 코드, 무단 다운로드한 YouTube 영상, 라이선스 미확인 이미지/데이터셋을 제출 자료나 레포에 포함하면 실격.
   - 직접 촬영한 영상이거나 라이선스(Public Domain, CC0, CC BY, Pexels License 등)가 검증·기록된 미디어만 사용해야 함.
6. **회피/금지 영역 (Prohibited / Low-Score Patterns)**
   - **"단순 이미지 분석기(Simple image analyzer / basic wrapper)" 지양**: 사진 1장을 넣어 설명만 출력하는 단순 래퍼가 아니라, 연속 스캔·추적·우선순위 판정·능동 경고를 수행하는 실시간 시스템이어야 함.
   - **안전·의료·법률 보장 문구 금지**: 사고 예방이나 안전을 100% 보장한다고 주장하거나 독성/비독성 종 판별로 안전 판정을 내리는 행위 금지 ("보조 도구"임을 명시).

---

## 파트 2. Trail Sentinel 해커톤 기준 준수 검사 및 조치 결과 (전 항목 통과 ✅)

| # | 점검 영역 | 상태 | 조치 및 검증 내용 |
| :---: | :--- | :---: | :--- |
| **1** | **Meta AI 모델 중심성 (`Use of Meta AI Tooling` 25%)** | ✅ **준수 완료** | [`trail_sentinel/meta_transport.py`](./trail_sentinel/meta_transport.py), [`server.py`](./server.py), [`webapp/index.html`](./webapp/index.html), [`webapp/app.js`](./webapp/app.js)에서 타사 모델 참조를 전수 제거하고 **Meta SAM 3.1 (개념 분할·추적) + Muse Wonder 역할 결정적 판정 (`triage.py`)** 단일 정식 파이프라인으로 정렬 완료 |
| **2** | **API 키·보안 아키텍처 (`PRD.md` §9.6 & `AGENTS.md`)** | ✅ **준수 완료** | `secret audit` 검사 **0건 통과**. 프로젝트 코드 내 환경변수 키 로더(`*_API_KEY`)가 전혀 없으며, `MetaSAMTransport`는 오직 외부 connector helper(`$TRAIL_SENTINEL_META_HELPER`) subprocess 경계로만 동작 |
| **3** | **공개 레포 크레딧 보호 (`PRD.md` §9.5 & `DEPLOY.md`)** | ✅ **준수 완료** | [`webapp/index.html`](./webapp/index.html)에서 고정 Cloud Run URL 문자열을 제거하고 `window.location.origin` 동적 바인딩으로 전환, 기본 일일 호출 상한 `DAILY_CALL_CAP=200` 유지 |
| **4** | **실시간 카메라(F1) + 데모 모드(F6) + 스텁 호환성** | ✅ **준수 완료** | 풀스크린 택티컬 HUD에서 **`📷 실시간 스캔 시작`**과 **`▶ 데모`**를 모두 지원하며, API 키 없는 기본 `python3 server.py` 실행 시에도 에러 없이 스텁 시뮬레이션·히어로 장면 재생 및 정직성 배지(`#demoBadge`)가 정상 작동 |
| **5** | **재학습 없는 실시간 커스텀 위험 개념 추가 (F7)** | ✅ **구현·검증 완료** | `POST /api/concepts` ([`server.py`](./server.py), [`config.py`](./trail_sentinel/config.py)) 및 프론트엔드 `＋ 개념 추가` (Web Speech Recognition `ko-KR` 음성 인식 🎙 + 텍스트 입력) 구현 완료 |
| **6** | **지연 계측·3.0초 경고 유효 기간 (`PRD.md` §9.2) & 정직성** | ✅ **구현·검증 완료** | [`webapp/app.js`](./webapp/app.js)에서 캡처 시점 대비 왕복 지연을 실측하고 `ALERT_VALIDITY_MS = 3000` 초과 응답은 경고를 폐기하며 `"확인 불가"` 배지를 표시. 인위적 거리 클램핑 제거 완료 |
| **7** | **Eval 오경보율 분모 통일 (`PRD.md` F9) & 데이터 라이선스** | ✅ **준수 완료** | [`eval/score.py`](./eval/score.py)에서 무위험 클립 분(minute) 기준 오경보율과 전체 영상 분 기준을 함께 출력하도록 통일. `eval/data/SOURCES.md` 14개 미디어 라이선스 기록 완비 |
| **8** | **신규 작업 기간(10/26~11/04), 안전 고지, 단위 테스트** | ✅ **준수 완료** | 전 커밋 2026-10-31 작성, MIT 라이선스 명시, 화면 하단 보조 도구 고지 상시 표시, 단위 테스트 **34/34 통과** |
