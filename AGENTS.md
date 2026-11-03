# AGENTS.md — Meta Global AI Developer Hackathon & Trail Sentinel

> **機能別の実装箇所・逆引きレシピは [`FEATURE_MAP.md`](./FEATURE_MAP.md) を最初に参照すること。**
> コード内の `[FEAT:F1]`〜`[FEAT:F12]` タグを `rg -n "\[FEAT:" .` で検索すると 1秒で該当行へ移動できる。

**概要**: スマホカメラ（または検証動画）で登山道を連続スキャンし、Meta SAM 3.1（テキストプロンプト概念分割）＋ Muse（意味検証・優先度トリアージ）で危険を検知、危険半径に入った時だけ 3言語（EN/JA/KO）の音声＋振動で警告するリアルタイム登山道危険検知 HUD。Meta Global AI Developer Hackathon（Indie Track / Push the Frontier）、提出締切 **2026-11-05 11:00 JST**。

## 1. ワークスペース構成（どこに何があるか）

| 目的 | ファイル |
| :--- | :--- |
| **どの機能をどこで直すか（機能ID・関数・DOM ID・逆引きレシピ）** | **[`FEATURE_MAP.md`](./FEATURE_MAP.md)** |
| アプリ本体（Webバックエンド・HUD・コアパッケージ・CLI） | `server.py`, `webapp/`, `trail_sentinel/`, `main.py` |
| 単体テスト・評価ハーネス・ライセンス台帳 | `tests/`, `eval/score.py`, `eval/data/SOURCES.md` |
| 製品要件・技術選定・適合要件・デプロイ手順 | `PRD.md`, `TECH.md`, `HACKATHON_REQUIREMENTS.md`, `DEPLOY.md` |
| ハッカソン公式ルール・賞金配分(`01`)、Meta AI 新モデル仕様(`02`)、アイデア提案(`03`)、応募回答(`04`)、適合監査レポート(`05`) | [`docs/`](./docs/README.md) |
| 検証動画マスター（`individual/01..08` 個別8本、結合版 `hazard_verification_combined*.mp4`、トップ画面デモ `hero_how_it_works.mp4`） | [`videos/`](./videos/README.md) |
| Web配信用圧縮動画（`webapp/` から相対参照） | `webapp/videos/` |

## 2. 機能ID クイックサマリー (`F1`〜`F12`)

| ID | 機能 | 主なフロント (`webapp/`) | 主なバックエンド (`server.py`, `trail_sentinel/`) | 状態 |
| :---: | :--- | :--- | :--- | :---: |
| **`F1`** | ライブカメラスキャン | `app.js`: `startLiveScan`, `captureFrame`, `scanOnce` | `server.py`: `LiveScanner.scan`, `Handler._scan_live` | ✅ 実装済 |
| **`F2`** | Meta AI モデル切替 & SAM 3.1 分割 | `index.html`: `#modelSelect`<br>`app.js`: `syncModelOptionsUI` | `vision_router.py`: `AVAILABLE_MODELS`, `scan_with_vertex_vision`<br>`sam_client.py`, `meta_transport.py` | ✅ 実装済 |
| **`F3`** | 距離・時計方向推定 & 4-KPI表示 | `index.html`: `#kpiDistance`, `#kpiDirection`<br>`app.js`: `updateTelemetryKpis` | `vision_router.py`: `estimate_visual_distance_m`<br>`meta_transport.py`: `ground_plane_distance_estimator` | ✅ 実装済 |
| **`F4`** | 優先度トリアージ (Muse Wonder ロール) | `app.js`: `data.alert` ハンドリング | `triage.py`: `evaluate`, `score`, `ALERT_DISTANCE_M`, `COOLDOWN_FRAMES` | ✅ 実装済 |
| **`F5`** | 音声警告(TTS)・振動・HUD描画 | `index.html`: `#overlay`, `#alertBanner`, `#btnAudio`<br>`app.js`: `drawBoxes`, `fireAlert`, `speakText` | `vision_router.py`: `synthesize_contour_mask_png`<br>`triage.py`: `phrase_for` | ✅ 実装済 |
| **`F6`** | ヒーローデモ再生 & 誠実性バッジ | `index.html`: `#btnDemoHero`, `#demoBadge`, `#unknownBadge`<br>`app.js`: `startDemoMode`, `registerFailure` | `server.py`: `scan_frame`<br>`sam_client.py`: `StubSAMClient`<br>`fixtures/hero_snake_leaves.json` | ✅ 実装済 |
| **`F7`** | カスタム危険概念追加 (音声/テキスト) | `index.html`: `#btnAddConcept`, `#conceptForm`, `#btnVoiceConcept` | `server.py`: `add_concept` (`POST /api/concepts`)<br>`config.py`: `register_custom_hazard` | ✅ 実装済 |
| **`F8`** | 日次呼び出し予算ガード (`CallBudget`) | `index.html`: `#kpiBudget` | `config.py`: `CallBudget`, `.call_counter.json` (上限200/日) | ✅ 実装済 |
| **`F9`** | 評価ハーネス & ライセンス台帳 | — | `eval/score.py`, `eval/clips_manifest.json`, `eval/data/SOURCES.md` | ✅ 実装済 |
| **`F10`** | 多言語対応 i18n (EN / JA / KO) | `index.html`: `#langSelect`<br>`app.js`: `I18N`, `applyLanguage` | `config.py`: `Hazard.label_for`<br>`triage.py`: `phrase_for(det, lang)` | ✅ 実装済 |
| **`F11`** | 検証動画スキャン & トッププレビュー動画 | `index.html`: `#heroShowcaseVideo`, `#btnVerifyVideoHero`<br>`app.js`: `startVerificationVideoScan` | `webapp/videos/hero_how_it_works.mp4`<br>`webapp/videos/hazard_verification_combined*.mp4` | ✅ 実装済 |
| **`F12`** | スマホQR即時接続 & Cloud Run 構成 | `index.html`: `#btnQrModal`, `#qrPanel`<br>`app.js`: `loadStatus` (`window.location.origin`) | `Dockerfile`, `DEPLOY.md` | ✅ 実装済 |

## 3. 実行・検証コマンド

```bash
# 1. 機能タグ検索（改修箇所の即時特定）
rg -n "\[FEAT:" .

# 2. 単体テスト全実行（ネットワーク不要・0.02秒）
python3 -m unittest discover -s tests -v

# 3. CLI スタブデモ & 評価ハーネス
python3 main.py
python3 eval/score.py

# 4. Webアプリ起動（デフォルト: ポート8765）
python3 server.py
```

## 4. 絶対ルール（ハッカソン失格防止ガードレール）

- **シークレットゼロ**: APIキーやトークンをコード・設定ファイル・Git履歴・ログに一切書かない。
- **予算ガード必須 (`F8`)**: すべてのスキャン呼び出しは必ず `CallBudget`（デフォルト `DAILY_CALL_CAP=200`）を通す。
- **権利確認済みメディアのみ (`F9`)**: テスト・検証用の画像や動画は直接撮影またはオープンライセンス（Pexels / Wikimedia CC）のみ使用し、`eval/data/SOURCES.md` に出典を明記する。
- **誠実性表示 (`F6`) & 補助ツール明記**: デモ・スタブ・検証動画再生時は必ず `#demoBadge` で明示し、ライブ遅延超過時は `#unknownBadge`（「確認不可」）を表示する。「安全を保証する」表現は禁止（「補助ツール」と明記）。
