# 05. Meta Global AI Developer Hackathon 요구사항 및 Trail Sentinel 준수성 감사 보고서

> **동기화 원본**: [`../HACKATHON_REQUIREMENTS.md`](../HACKATHON_REQUIREMENTS.md)
> **기준 문서**:
> - [`01-hackathon-overview-and-rules.md`](./01-hackathon-overview-and-rules.md)
> - [`02-meta-ai-models-and-tooling.md`](./02-meta-ai-models-and-tooling.md)
> - [`../PRD.md`](../PRD.md) (v0.5)
> - [`../AGENTS.md`](../AGENTS.md)

---

## 1. 공식 해커톤 필수 요구사항 체크리스트

1. **Meta AI 모델 핵심 활용 (`Use of Meta AI Tooling` — 심사 배점 25% & 1차 적격 기준)**
   - Meta Model API (`SAM 3.1`, `Muse Wonder`, `Muse Spark 1.3`, `Muse Image`, `Muse Voice Transcribe`) 또는 Meta 오픈웨이트 모델(`Muse Spark Open 816B`, `Muse Glimmer 30B`)을 프로젝트의 핵심 기능으로 사용해야 함.
2. **신규 작업 기간 엄수 (2026-10-26 ~ 2026-11-04)**
   - 해커톤 기간 내에 작성된 코드만 평가 대상이며, 커밋 히스토리와 문서를 통해 신규 구현 범위와 기존 자산을 명확히 구분해야 함.
3. **공개 GitHub 레포지토리 필수 & 시크릿 제로**
   - Public GitHub 저장소 제출 필수.
   - 코드·커밋 히스토리·프론트엔드·로그 어디에도 API 키나 시크릿이 포함되지 않아야 함.
4. **3분 데모 영상 & 재현 가능한 데모(F6)**
   - 최대 3분 길이의 데모 영상 제출 필수.
   - 심사위원이 레포를 클론해 API 키 없이도 기본 실행(`python3 server.py`)으로 전체 파이프라인을 확인할 수 있어야 함.
5. **데이터·미디어 라이선스 적격성 (`eval/data/SOURCES.md`)**
   - 직접 촬영했거나 라이선스가 검증된(Public Domain, CC0, CC BY, Pexels 등) 미디어만 사용해야 하며 무단 다운로드 영상 사용 시 실격.
6. **안전 고지 및 포지셔닝 규칙**
   - "단순 이미지 분석기(simple image analyzer)"가 아닌 실시간 능동 경고 시스템(연속 스캔 + 추적 + 우선순위 판정 + 음성/진동 경고)으로 포지셔닝.
   - "안전을 보장/예방한다"는 표현 및 종 단정 안전 판정 금지 ("보조 도구"임을 명시).

---

## 2. Trail Sentinel 해커톤 기준 준수 검사 및 수정 완료 결과 (전 항목 통과 ✅)

| # | 점검 항목 | 준수 여부 | 조치 완료 내역 |
| :---: | :--- | :---: | :--- |
| 1 | **Meta AI 모델 중심성 (`Tooling` 25%)** | ✅ **통과** | `trail_sentinel/meta_transport.py`, `server.py`, `webapp/`에서 타사 모델 참조를 전수 제거하고 **Meta SAM 3.1 (개념 분할·추적) + Muse Wonder 역할 결정적 판정 (`triage.py`)** 정식 아키텍처로 복원 완료 |
| 2 | **환경변수 키 직접 로드 금지 (`PRD.md` §9.6)** | ✅ **통과** | `trail_sentinel/meta_transport.py` 내 환경변수 API 키 직접 로더(`*_API_KEY`)를 완전히 제거하고 `$TRAIL_SENTINEL_META_HELPER` subprocess 경계만 유지 |
| 3 | **공개 레포 내 Cloud Run 라이브 URL 보호** | ✅ **통과** | `webapp/index.html`에서 고정 Cloud Run URL을 제거하고 `window.location.origin` 동적 표시로 변경, 기본 `DAILY_CALL_CAP=200` 유지 |
| 4 | **실시간 스캔(F1) + 데모/스텁 재현성(F6)** | ✅ **통과** | 풀스크린 택티컬 HUD에서 `📷 실시간 스캔 시작`과 `▶ 데모`를 모두 지원하며, 기본 `python3 server.py` (스텁 모드)에서도 정직성 배지(`#demoBadge`)와 함께 완벽히 작동 |
| 5 | **실시간 커스텀 위험 개념 추가 (F7)** | ✅ **통과** | `POST /api/concepts` 및 프론트엔드 `＋ 개념 추가` (한국어 음성 인식 🎙 + 텍스트 입력) 구현 및 단위 테스트(`CustomConceptTests`) 검증 완료 |
| 6 | **3.0초 경고 유효 기간 (§9.2) & 정직성 원칙** | ✅ **통과** | `ALERT_VALIDITY_MS = 3000` 초과 응답 폐기 및 `"확인 불가"` 배지 전환 구현, 인위적 거리 클램핑 제거 완료 |
| 7 | **Eval 오경보율 분모 통일 (F9) & 데이터 저작권** | ✅ **통과** | `eval/score.py`에서 무위험 클립 분(minute) 기준 오경보율과 전체 영상 분 기준을 함께 출력하도록 통일, `eval/data/SOURCES.md` 완비 |
| 8 | **시크릿 감사(`secret audit`) & 단위 테스트 (`34/34`)** | ✅ **통과** | `secret audit` 0건, 단위 테스트 `34/34` 전원 통과 |
