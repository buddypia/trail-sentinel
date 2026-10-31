# DEPLOY.md — Trail Sentinel 데모 배포

_최종 갱신: 2026-10-31_

## 현재 상태 (솔직하게)

| 항목 | 상태 |
| --- | --- |
| 웹 서버 (스텁/데모 모드) | **이 VM에서 실행 중** — `http://localhost:8765` (VM 내부에서만 접근 가능) |
| 공개 HTTPS URL | **아직 없음 — 이 VM의 네트워크에서는 터널 생성이 차단됨** (아래 참조) |

이 VM의 외부 연결은 프록시 경유가 강제되고 직접 TLS/SSH 연결은 게이트웨이가 끊는다. 그래서 아래 3가지 공개 방법을 모두 시도했지만 공개 URL을 만들지 못했다:

- Cloudflare quick tunnel (`cloudflared tunnel --url http://localhost:8765`): `failed to request quick Tunnel: Post "https://api.trycloudflare.com/tunnel": tls: first record does not look like a TLS handshake` — 프록시 환경변수 유무와 무관하게 동일 실패 (3회 시도).
- localhost.run (SSH 리버스 터널): 게이트웨이가 SSH 연결을 즉시 종료 (`Connection closed by 198.19.0.1 port 3128`).
- localtunnel (Node): URL을 발급받지 못하고 무응답으로 멈춤.

앱 자체의 문제가 아니다 — 같은 스크립트(`deploy/start_demo.sh`)는 일반 네트워크(예: Jun의 Mac)에서는 그대로 동작한다.

## 공개 URL 만드는 법 (일반 네트워크에서)

준비물: python3, cloudflared 공식 바이너리.

```bash
cd trail-sentinel
./deploy/start_demo.sh
# 출력된 https://<random>.trycloudflare.com 이 공개 URL
cat deploy/current_url.txt   # 같은 URL이 저장됨
./deploy/stop_demo.sh        # 종료 (서버+터널)
```

- `start_demo.sh`는 서버를 **항상 스텁 모드로** 띄운다 (`TRAIL_SENTINEL_LIVE`를 명시적으로 제거). 공개 URL로 크레딧이 새는 일은 없다.
- quick tunnel URL은 **임시 주소**다: 스크립트를 다시 실행하거나 VM/호스트가 바뀌면 주소가 바뀐다. 제출 자료에는 이 주소를 고정 링크로 쓰지 말 것.

## 폰에서 여는 법 (공개 URL이 생긴 뒤)

1. 폰 브라우저에서 공개 URL을 연다.
2. 카메라 권한을 허용한다 (브라우저 카메라는 HTTPS에서만 동작 — 터널 주소는 HTTPS라 OK).
3. 화면 모드를 확인한다:
   - **데모 모드**: 녹화된 히어로 장면(낙엽 속 뱀)을 재생하며 스캔한다. 실제 카메라 분석이 아니며 화면에 "데모 장면 재생 중" 배지가 뜬다.
   - **카메라 모드**: 폰 카메라가 켜진다. 스텁 서버에서는 실제 분석 없이 데모 판정만 돌아가므로, 실분석은 아래 라이브 모드가 필요하다.

## 라이브 모드로 전환하는 법 (주의해서 읽을 것)

라이브 모드는 서버를 실행하는 쪽에서만 켠다:

```bash
cd trail-sentinel
TRAIL_SENTINEL_LIVE=1 python3 server.py   # 이후 터널을 따로 연결
```

- **경고**: 라이브 모드에서 공개 URL을 열면, **URL을 아는 누구나 스캔을 돌려 Jun의 크레딧을 소모할 수 있다.** 물리적 상한은 `CallBudget` 일일 캡 200콜 = **최악 $0.50/일**이지만, 캡이 차면 정작 필요한 데모 때 라이브를 못 쓴다.
- 그래서 라이브 공개는 **Jun 본인의 폰 테스트와 데모 촬영 시간에만** 켜고, 끝나면 즉시 스텁으로 되돌린다. 평소 공개 데모는 스텁으로 둔다.
- 라이브에는 connector helper(`custom.meta-model-api`)가 있는 이 VM 환경이 필요하다. helper 경로는 `TRAIL_SENTINEL_META_HELPER` 환경변수로 바꿀 수 있다 (없으면 "not configured" 오류로 정직하게 실패한다).

## 로컬 확인 커맨드

```bash
curl -s localhost:8765/api/status        # {"mode": "stub", "live_enabled": false, ...}
curl -s -X POST localhost:8765/api/scan -H 'Content-Type: application/json' \
  -d '{"frame_index": 45, "mode": "demo", "reset": true}'   # "발 앞 3미터, 뱀"
```
