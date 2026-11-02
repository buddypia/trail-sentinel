"use strict";
// Trail Sentinel · Meta SAM 3.1 + Muse Wonder Real-Time Optical HUD
// - Multi-language UI & Voice (EN default + auto-detected browser locale + explicit top-bar switcher: en / ja / ko)
// - Live Camera Mode (F1/F2): captures frames -> POST /api/scan -> mask/bbox + triage alert
// - Demo Mode (F6): replays recorded hero fixture frames 0..60 without camera
// - Live Custom Hazard (F7): adds zero-retraining concepts via voice/text -> POST /api/concepts
// - Latency & Honesty Guardrails (PRD 9.2, 9.4): alert validity window + unverified badge

const $ = (id) => document.getElementById(id);
const stage = $("stage");
const video = $("cam");
const canvas = $("overlay");
const ctx = canvas.getContext("2d");
const banner = $("alertBanner");
const demoBadge = $("demoBadge");
const msg = $("message");
const msgText = $("messageText");
const statusEl = $("status");
const latencyPill = $("latencyPill");
const scanDot = $("scanDot");
const unknownBadge = $("unknownBadge");
const kpiDistance = $("kpiDistance");
const kpiDirection = $("kpiDirection");
const kpiLatency = $("kpiLatency");
const kpiBudget = $("kpiBudget");
const btnLive = $("btnLive");
const btnDemo = $("btnDemo");
const btnStartHero = $("btnStartHero");
const btnDemoHero = $("btnDemoHero");
const btnAudio = $("btnAudio");
const audioLabel = $("audioLabel");
const btnQrModal = $("btnQrModal");
const btnExpandQr = $("btnExpandQr");
const btnCloseQr = $("btnCloseQr");
const qrPanel = $("qrPanel");
const langSelect = $("langSelect");
const modelSelect = $("modelSelect");
const activeModelTag = $("activeModelTag");
const modelModeDesc = $("modelModeDesc");
const specModelName = $("specModelName");
const specVerifyMode = $("specVerifyMode");
const btnAddConcept = $("btnAddConcept");
const conceptForm = $("conceptForm");
const conceptNameInput = $("conceptNameInput");
const conceptPromptInput = $("conceptPromptInput");
const btnVoiceConcept = $("btnVoiceConcept");

const shot = document.createElement("canvas");
const shotCtx = shot.getContext("2d");

const CAPTURE_TARGET_LONG = 416;
const CAPTURE_MIN_SHORT = 240;
const NEXT_LIVE_DELAY_MS = 160;
const DEMO_TICK_MS = 1000;
const FRAME_STEP = 5;
const LAST_FRAME = 60;
const SCAN_TIMEOUT_MS = 18000;
const ALERT_VALIDITY_MS = 5000;

const SUPPORTED_LANGS = ["en", "ja", "ko"];
const DEFAULT_LANG = "en";
const LANG_STORAGE_KEY = "trail_sentinel_lang";
const VOICE_LANG_MAP = {
  en: "en-US",
  ja: "ja-JP",
  ko: "ko-KR",
};

const I18N = {
  en: {
    page_title: "Trail Sentinel · Meta SAM 3.1 Real-Time Trail Hazard HUD",
    lang_prefix: "Lang",
    model_prefix: "Model",
    voice_on: "Voice On",
    voice_off: "Voice Off",
    qr_btn: "Mobile QR",
    kpi_distance: "Nearest Hazard Distance",
    kpi_direction: "Hazard Bearing",
    kpi_latency: "Pipeline Latency",
    kpi_budget: "Daily Call Budget",
    demo_badge_replay: "Demo scene playing (not live camera)",
    demo_badge_stub: "Stub simulation (camera preview + demo detections)",
    unknown_badge_default: "Unverified · Scan delayed",
    hero_scope: "Meta SAM 3.1 + Muse Wonder · Optical Segmentation & Range Triage",
    hero_title: "Real-Time Trail Hazard Detection",
    hero_copy:
      "Point your camera at a trail or test video to segment and track prompt-defined hazards at the pixel level, with instant voice and haptic warnings when entering hazard range.",
    btn_start_hero: "Start Camera Scan",
    btn_demo_hero: "Play Hero Demo Scene (Frames 0..60)",
    qr_inline_title: "Open Instantly on Smartphone",
    qr_expand_btn: "Enlarge QR",
    qr_inline_hint:
      "Scan with your phone's camera to launch immediately in your mobile browser.",
    chips_label: "Concept Filters",
    btn_add_concept: "+ Add Concept",
    concept_name_placeholder: "New hazard name (e.g., Fallen tree)",
    concept_prompt_placeholder: "English prompt (optional: a fallen tree)",
    voice_unsupported_placeholder: "Voice input unsupported · Type hazard name",
    btn_voice_input: "Voice Input",
    btn_voice_listening: "Listening...",
    btn_register_concept: "Add",
    btn_live_start: "Start Live Scan",
    btn_live_stop: "Stop Scan",
    btn_demo_start: "Play Demo",
    btn_demo_stop: "Stop Demo",
    safety_line:
      "Assistive tool only · Does not guarantee safety; false positives or misses may occur. Always watch your surroundings.",
    qr_card_title: "Instant Mobile Field HUD",
    btn_close: "Close",
    qr_card_desc:
      "Scan the QR code below with your smartphone camera to open this deployed Trail Sentinel web app immediately.",
    qr_step_1: "Open your smartphone camera app",
    qr_step_2: "Scan QR and tap the link banner",
    qr_step_3: "Start camera scan or play demo",
    btn_copy_url: "Copy URL",
    btn_copied_url: "Copied",
    spec_card_title: "Pipeline Specifications",
    spec_dt_seg: "Concept Seg & Track",
    spec_dt_verify: "Semantic Verification",
    spec_verify_on: "Active (Verifies real bear/snake vs rock)",
    spec_verify_off: "Inactive (Pure shape mask segmentation)",
    spec_dt_triage: "Priority Triage",
    spec_dd_triage: "Muse Wonder Role Triage",
    spec_dt_cooldown: "Track Cooldown",
    spec_dd_cooldown: "3.0 s (Anti-chatter)",
    spec_dt_concepts: "Default Concepts",
    spec_dd_concepts: "Snake · Wasp · Bear · Boar · Rockfall · Slippery",
    log_card_title: "Live Detection Log",
    log_standby: "Standby",
    log_empty_standby:
      "Start a live scan or demo to log segmented hazards, bearings, and distances per frame.",
    log_empty_clear: "No hazards detected in the current frame.",
    status_checking: "Checking server connection...",
    status_live_prefix: "Live",
    status_stub_prefix: "Stub (Demo Fixtures)",
    status_calls: "Calls",
    status_clear: "Trail Clear",
    status_partial_err: "Partial errors",
    status_model_changed: "Model switched",
    status_lang_changed: "Language: English",
    status_concept_added: "Added concept",
    stop_manual: "Stopped · Ready to start scanning again.",
    stop_demo_done: "Hero demo scene (frames 0..60) playback finished.",
    stop_cap_reached: "Daily API call cap reached. Please try again tomorrow.",
    cam_denied:
      "Camera permission was denied or no camera is available. Allow camera access or try [Play Demo].",
    err_timeout: "Request timed out (10s)",
    err_network: "Network error",
    err_stale_prefix: "Latency exceeded",
    err_stale_suffix: "s (>3.0s validity window)",
    alert_prefix: "Hazard Alert",
    chip_toggle_hint: "Click to toggle filter",
  },
  ja: {
    page_title: "Trail Sentinel · Meta SAM 3.1 リアルタイム登山道危険検知 HUD",
    lang_prefix: "言語",
    model_prefix: "モデル",
    voice_on: "音声 ON",
    voice_off: "音声 OFF",
    qr_btn: "スマホ QR",
    kpi_distance: "最接近の危険距離",
    kpi_direction: "危険方位（時計方向）",
    kpi_latency: "パイプライン遅延",
    kpi_budget: "本日のAPI呼び出し枠",
    demo_badge_replay: "デモシーン再生中（実際のカメラではありません）",
    demo_badge_stub: "スタブシミュレーション中（カメラプレビュー＋デモ判定）",
    unknown_badge_default: "確認不可 · スキャン遅延",
    hero_scope: "Meta SAM 3.1 + Muse Wonder · 光学セグメンテーション＆距離トリアージ",
    hero_title: "前方トレイルの危険要素をリアルタイム計測",
    hero_copy:
      "カメラで登山道やテスト動画を映すと、テキストプロンプトで定義された危険要素をピクセル単位で分割・追跡し、危険半径に入った際に方向と距離を音声・振動で即座に警告します。",
    btn_start_hero: "カメラスキャン開始",
    btn_demo_hero: "ヒーローデモ再生 (フレーム 0..60)",
    qr_inline_title: "スマホのカメラですぐ開く",
    qr_expand_btn: "QRを拡大表示",
    qr_inline_hint:
      "スマートフォンの標準カメラでスキャンすると、モバイルブラウザで即座に起動します。",
    chips_label: "分割コンセプトフィルター",
    btn_add_concept: "+ コンセプト追加",
    concept_name_placeholder: "新しい危険名 (例: 倒木)",
    concept_prompt_placeholder: "英語プロンプト (任意: a fallen tree)",
    voice_unsupported_placeholder: "音声認識非対応ブラウザ · テキストで入力してください",
    btn_voice_input: "音声入力",
    btn_voice_listening: "聞き取り中...",
    btn_register_concept: "追加",
    btn_live_start: "リアルタイムスキャン開始",
    btn_live_stop: "スキャン停止",
    btn_demo_start: "デモ再生",
    btn_demo_stop: "デモ停止",
    safety_line:
      "補助ツールです · 安全を保証するものではなく、誤検知や見逃しが発生する場合があります。必ずご自身の目で周囲を確認してください。",
    qr_card_title: "モバイルフィールドHUD即時接続",
    btn_close: "閉じる",
    qr_card_desc:
      "スマートフォンのカメラで下のQRコードをスキャンすると、現在デプロイされているTrail Sentinelアプリにすぐアクセスできます。",
    qr_step_1: "スマホの標準カメラアプリを起動",
    qr_step_2: "QRを読み取りリンクバナーをタップ",
    qr_step_3: "カメラスキャンまたはデモ再生を開始",
    btn_copy_url: "URLをコピー",
    btn_copied_url: "コピー完了",
    spec_card_title: "システムパイプライン仕様",
    spec_dt_seg: "概念分割・追跡",
    spec_dt_verify: "意味論的検証",
    spec_verify_on: "有効（クマ・ヘビ等の真偽検証・誤検知除外）",
    spec_verify_off: "無効（純粋な形状マスク分割のみ）",
    spec_dt_triage: "優先度トリアージ",
    spec_dd_triage: "Muse Wonder ロールトリアージ",
    spec_dt_cooldown: "同一対象クールダウン",
    spec_dd_cooldown: "3.0 s（重複発話抑制）",
    spec_dt_concepts: "基本検知コンセプト",
    spec_dd_concepts: "ヘビ · スズメバチの巣 · クマ · イノシシ · 落石 · 滑りやすい路面",
    log_card_title: "リアルタイム分割検知ログ",
    log_standby: "待機中",
    log_empty_standby:
      "スキャンまたはデモを開始すると、フレームごとの分割オブジェクトと方位・距離判定が記録されます。",
    log_empty_clear: "現在のフレームで検知された危険要素はありません。",
    status_checking: "サーバー接続を確認中...",
    status_live_prefix: "ライブ",
    status_stub_prefix: "スタブ (デモデータ)",
    status_calls: "呼び出し",
    status_clear: "前方安全",
    status_partial_err: "一部エラー",
    status_model_changed: "モデル変更完了",
    status_lang_changed: "言語: 日本語",
    status_concept_added: "新規コンセプト追加",
    stop_manual: "停止中 · いつでもスキャンを再開できます。",
    stop_demo_done: "ヒーローデモシーン（フレーム 0..60）の再生が完了しました。",
    stop_cap_reached: "本日のAPI呼び出し上限に達しました。明日もう一度お試しください。",
    cam_denied:
      "カメラの権限が拒否されたか、カメラを利用できません。カメラ権限を許可するか［デモ再生］をお試しください。",
    err_timeout: "応答タイムアウト (10秒)",
    err_network: "ネットワークエラー",
    err_stale_prefix: "遅延超過",
    err_stale_suffix: "秒 (>3.0秒の有効期限切れ)",
    alert_prefix: "危険警告",
    chip_toggle_hint: "クリックでON/OFF切替",
  },
  ko: {
    page_title: "Trail Sentinel · Meta SAM 3.1 실시간 등산로 위험 감지 HUD",
    lang_prefix: "언어",
    model_prefix: "모델",
    voice_on: "음성 켜짐",
    voice_off: "음성 꺼짐",
    qr_btn: "모바일 QR",
    kpi_distance: "최근접 위험 거리",
    kpi_direction: "위험 방위각",
    kpi_latency: "파이프라인 지연",
    kpi_budget: "일일 호출 예산",
    demo_badge_replay: "데모 장면 재생 중 (실제 카메라 아님)",
    demo_badge_stub: "스텁 시뮬레이션 중 (카메라 프리뷰 + 데모 판정)",
    unknown_badge_default: "확인 불가 · 스캔 지연",
    hero_scope: "Meta SAM 3.1 + Muse Wonder · 광학 분할 및 거리 판정",
    hero_title: "전방 등산로 위험 요소 실시간 계측",
    hero_copy:
      "카메라로 등산로나 테스트 영상을 비추면 텍스트 프롬프트로 정의된 위험 요소를 픽셀 단위로 분할·추적하고, 위험 반경 진입 시 방향과 거리를 음성·진동으로 즉시 경고합니다.",
    btn_start_hero: "카메라 스캔 시작",
    btn_demo_hero: "히어로 데모 장면 재생 (프레임 0..60)",
    qr_inline_title: "스마트폰 카메라로 바로 열기",
    qr_expand_btn: "QR 크게 보기",
    qr_inline_hint:
      "핸드폰 기본 카메라로 스캔하면 모바일 브라우저에서 즉시 실행됩니다.",
    chips_label: "분할 개념 필터",
    btn_add_concept: "+ 개념 추가",
    concept_name_placeholder: "새 위험 이름 (예: 쓰러진 나무)",
    concept_prompt_placeholder: "영어 프롬프트 (선택: a fallen tree)",
    voice_unsupported_placeholder: "음성인식 미지원 브라우저 · 텍스트로 입력하세요",
    btn_voice_input: "음성 입력",
    btn_voice_listening: "듣는 중...",
    btn_register_concept: "등록",
    btn_live_start: "실시간 스캔 시작",
    btn_live_stop: "스캔 중지",
    btn_demo_start: "데모 재생",
    btn_demo_stop: "데모 중지",
    safety_line:
      "보조 도구입니다 · 안전을 보장하지 않으며 오탐·미탐이 있을 수 있으니 주변을 직접 확인하세요.",
    qr_card_title: "모바일 필드 HUD 즉시 연결",
    btn_close: "닫기",
    qr_card_desc:
      "스마트폰 카메라로 아래 QR 코드를 스캔하면 현재 배포된 Trail Sentinel 웹앱에 즉시 접속합니다.",
    qr_step_1: "스마트폰 기본 카메라 앱 실행",
    qr_step_2: "QR 스캔 후 배너를 눌러 접속",
    qr_step_3: "카메라 스캔 또는 데모 재생 실행",
    btn_copy_url: "URL 복사",
    btn_copied_url: "복사됨",
    spec_card_title: "시스템 파이프라인 사양",
    spec_dt_seg: "개념 분할·추적",
    spec_dt_verify: "의미론적 검증",
    spec_verify_on: "활성 (곰·뱀 등 정밀 시각 검증)",
    spec_verify_off: "비활성 (순수 형태 마스크 분할)",
    spec_dt_triage: "우선순위 판정",
    spec_dd_triage: "Muse Wonder 역할 트리아지",
    spec_dt_cooldown: "동일 객체 쿨다운",
    spec_dd_cooldown: "3.0 s (중복 발화 억제)",
    spec_dt_concepts: "기본 감지 개념",
    spec_dd_concepts: "뱀 · 말벌집 · 곰 · 멧돼지 · 낙석 · 미끄럼",
    log_card_title: "실시간 분할 감지 로그",
    log_standby: "대기 중",
    log_empty_standby:
      "스캔 또는 데모를 시작하면 프레임별 분할 객체와 거리·방위 판정이 기록됩니다.",
    log_empty_clear: "현재 프레임에서 감지된 위험 요소가 없습니다.",
    status_checking: "서버 연결 확인 중...",
    status_live_prefix: "라이브",
    status_stub_prefix: "스텁 (데모 픽스처)",
    status_calls: "호출",
    status_clear: "전방 안전",
    status_partial_err: "일부 실패",
    status_model_changed: "모델 변경됨",
    status_lang_changed: "언어: 한국어",
    status_concept_added: "새 개념 추가됨",
    stop_manual: "중지됨 · 다시 스캔을 시작할 수 있습니다.",
    stop_demo_done: "히어로 데모 장면(프레임 0..60) 재생이 완료되었습니다.",
    stop_cap_reached: "오늘의 API 호출 상한에 도달했습니다. 내일 다시 시도하세요.",
    cam_denied:
      "카메라 권한이 거부되었거나 카메라를 사용할 수 없습니다. 카메라 권한을 허용하거나 [데모 재생] 모드로 확인해 보세요.",
    err_timeout: "응답 시간 초과 (10초)",
    err_network: "네트워크 오류",
    err_stale_prefix: "지연 초과",
    err_stale_suffix: "초 (>3.0초 유효기간 만료)",
    alert_prefix: "위험 경고",
    chip_toggle_hint: "눌러서 켜기/끄기",
  },
};

const HAZARD_LABELS_FALLBACK = {
  snake: { en: "Snake", ja: "ヘビ", ko: "뱀" },
  wasp_nest: { en: "Wasp nest", ja: "スズメバチの巣", ko: "말벌집" },
  bear: { en: "Bear", ja: "クマ", ko: "곰" },
  boar: { en: "Wild boar", ja: "イノシシ", ko: "멧돼지" },
  rockfall: { en: "Rockfall zone", ja: "落石区間", ko: "낙석 구간" },
  slippery: { en: "Slippery path", ja: "滑りやすい路面", ko: "미끄러운 구간" },
};

function detectInitialLanguage() {
  try {
    const params = new URLSearchParams(window.location.search);
    const qLang = (params.get("lang") || "").toLowerCase().slice(0, 2);
    if (SUPPORTED_LANGS.includes(qLang)) return qLang;
  } catch {}
  try {
    const saved = (localStorage.getItem(LANG_STORAGE_KEY) || "").toLowerCase().slice(0, 2);
    if (SUPPORTED_LANGS.includes(saved)) return saved;
  } catch {}
  const browserLangs =
    Array.isArray(navigator.languages) && navigator.languages.length
      ? navigator.languages
      : [navigator.language || DEFAULT_LANG];
  for (const raw of browserLangs) {
    const code = String(raw || "").toLowerCase().slice(0, 2);
    if (SUPPORTED_LANGS.includes(code)) {
      return code;
    }
  }
  return DEFAULT_LANG;
}

let currentLang = detectInitialLanguage();
let loopTimer = null;
let stream = null;
let isRunning = false;
let mode = null; // "live" | "demo"
let frame = 0;
let scanning = false;
let audioEnabled = true;
let lastSpoken = "";
let lastSpokenAt = 0;
let emptyAlertFrames = 0;
let serverMode = "stub";
let selectedModel = "sam-3.1-hybrid";
let modelsMeta = new Map();
let hazards = [];
let selectedConcepts = new Set();
let chipElements = new Map();
let failCount = 0;
let lastStatus = null;
let lastDetections = [];
let lastReportedMs = null;
let lastAlertObj = null;

function t(key) {
  const dict = I18N[currentLang] || I18N[DEFAULT_LANG];
  return dict[key] ?? I18N[DEFAULT_LANG][key] ?? key;
}

function getHazardLabel(item) {
  if (!item) return "";
  const key = item.key || item.concept;
  if (currentLang === "ja") {
    return (
      item.label_ja ||
      (HAZARD_LABELS_FALLBACK[key] && HAZARD_LABELS_FALLBACK[key].ja) ||
      item.label_en ||
      item.label ||
      item.label_ko ||
      key
    );
  }
  if (currentLang === "ko") {
    return (
      item.label_ko ||
      (HAZARD_LABELS_FALLBACK[key] && HAZARD_LABELS_FALLBACK[key].ko) ||
      item.label ||
      item.label_en ||
      key
    );
  }
  return (
    item.label_en ||
    (HAZARD_LABELS_FALLBACK[key] && HAZARD_LABELS_FALLBACK[key].en) ||
    item.label ||
    item.label_ko ||
    key
  );
}

function formatBearing(clockDir) {
  const dir = clockDir || 12;
  if (currentLang === "ja") return `${dir}時方向`;
  if (currentLang === "ko") return `${dir}시 방향`;
  return `${dir} o'clock`;
}

function formatDetectionCount(count) {
  if (currentLang === "ja") return `${count}件検知`;
  if (currentLang === "ko") return `${count}건 감지`;
  return `${count} detected`;
}

function formatImmediateBannerText(det) {
  const dir = det.clock_direction || 12;
  const dist = det.distance_m.toFixed(1);
  const name = getHazardLabel(det);
  if (currentLang === "ja") {
    return `${dir}時方向 ${dist}m · ${name}を捕捉`;
  }
  if (currentLang === "ko") {
    return `${dir}시 방향 ${dist}m ${name} 포착`;
  }
  return `${dir} o'clock · ${dist}m · ${name} spotted`;
}

function getAlertText(alert) {
  if (!alert) return "";
  if (currentLang === "ja" && alert.text_ja) return alert.text_ja;
  if (currentLang === "ko" && alert.text_ko) return alert.text_ko;
  if (currentLang === "en" && alert.text_en) return alert.text_en;
  return alert.text || alert.text_en || alert.text_ko || "";
}

function syncModelOptionsUI() {
  if (!modelSelect || modelsMeta.size === 0) return;
  for (const opt of modelSelect.options) {
    const m = modelsMeta.get(opt.value);
    if (!m) continue;
    if (currentLang === "ja" && m.label_ja) opt.textContent = m.label_ja;
    else if (currentLang === "ko" && m.label_ko) opt.textContent = m.label_ko;
    else if (m.label_en || m.label) opt.textContent = m.label_en || m.label;
  }
}

function syncModelSpecUI() {
  const m = modelsMeta.get(selectedModel);
  const shortLabel = m ? m.short_label : selectedModel;
  if (activeModelTag) activeModelTag.textContent = shortLabel;
  if (specModelName) specModelName.textContent = shortLabel;
  if (modelModeDesc && m) {
    if (currentLang === "ja" && m.description_ja) {
      modelModeDesc.textContent = m.description_ja;
    } else if (currentLang === "ko" && m.description_ko) {
      modelModeDesc.textContent = m.description_ko;
    } else {
      modelModeDesc.textContent = m.description_en || m.description || "";
    }
  }
  if (specVerifyMode) {
    specVerifyMode.textContent =
      selectedModel === "sam-3.1" ? t("spec_verify_off") : t("spec_verify_on");
  }
}

function applyLanguage(lang, { userInitiated = false } = {}) {
  const normalized = String(lang || DEFAULT_LANG).toLowerCase().slice(0, 2);
  currentLang = SUPPORTED_LANGS.includes(normalized) ? normalized : DEFAULT_LANG;
  document.documentElement.lang = currentLang;
  document.title = t("page_title");
  if (langSelect && langSelect.value !== currentLang) {
    langSelect.value = currentLang;
  }
  if (userInitiated) {
    try {
      localStorage.setItem(LANG_STORAGE_KEY, currentLang);
    } catch {}
  }

  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    if (!key) return;
    if (el === btnLive && isRunning) {
      el.textContent = mode === "demo" ? t("btn_demo_stop") : t("btn_live_stop");
      return;
    }
    el.textContent = t(key);
  });

  if (audioLabel) {
    audioLabel.textContent = audioEnabled ? t("voice_on") : t("voice_off");
  }
  if (conceptNameInput) {
    conceptNameInput.placeholder = t("concept_name_placeholder");
  }
  if (conceptPromptInput) {
    conceptPromptInput.placeholder = t("concept_prompt_placeholder");
  }
  if (!demoBadge.hidden) {
    demoBadge.textContent =
      mode === "demo" ? t("demo_badge_replay") : t("demo_badge_stub");
  }

  syncModelOptionsUI();
  syncModelSpecUI();
  renderChips();
  updateTelemetryKpis(lastDetections, lastReportedMs);
  if (lastDetections.length > 0) {
    drawBoxes(lastDetections);
  }
  if (!banner.hidden) {
    if (lastAlertObj) {
      banner.textContent = `${t("alert_prefix")} · ${getAlertText(lastAlertObj)}`;
    } else if (lastDetections.length > 0) {
      banner.textContent = formatImmediateBannerText(lastDetections[0]);
    }
  }
  if (userInitiated) {
    unlockSpeech();
    renderStatus(t("status_lang_changed"));
    if (audioEnabled && lastAlertObj && !banner.hidden) {
      speakText(getAlertText(lastAlertObj));
    }
  } else {
    renderStatus();
  }
}

function renderStatus(extra) {
  if (!lastStatus) {
    statusEl.textContent = t("status_checking");
    return;
  }
  const isLive = lastStatus.mode === "live";
  const m = modelsMeta.get(selectedModel);
  const modelLabel = m ? m.short_label : "SAM 3.1 + Muse Spark";
  const engineLabel = isLive
    ? `${t("status_live_prefix")} (${modelLabel})`
    : t("status_stub_prefix");
  statusEl.textContent =
    `${engineLabel} · ${t("status_calls")} ${lastStatus.calls_today}/${lastStatus.daily_cap}` +
    (extra ? ` · ${extra}` : "");
  if (kpiBudget) {
    kpiBudget.textContent = `${lastStatus.calls_today} / ${lastStatus.daily_cap}`;
  }
}

function updateTelemetryKpis(dets, latencyMs) {
  if (kpiLatency) {
    kpiLatency.textContent = typeof latencyMs === "number" ? `${latencyMs} ms` : "-";
  }
  const logEl = $("detectionLog");
  const logCountTag = $("logCountTag");
  if (!dets || dets.length === 0) {
    if (kpiDistance) {
      kpiDistance.textContent = "-";
      kpiDistance.classList.remove("danger");
    }
    if (kpiDirection) {
      kpiDirection.textContent = "-";
    }
    if (logCountTag) {
      logCountTag.textContent = isRunning ? formatDetectionCount(0) : t("log_standby");
    }
    if (logEl && !isRunning) {
      logEl.innerHTML = `<p class="log-empty">${t("log_empty_standby")}</p>`;
    } else if (logEl) {
      logEl.innerHTML = `<p class="log-empty">${t("log_empty_clear")}</p>`;
    }
    return;
  }
  const sorted = [...dets].sort((a, b) => a.distance_m - b.distance_m);
  const nearest = sorted[0];
  const nearestLabel = getHazardLabel(nearest);
  if (kpiDistance) {
    kpiDistance.innerHTML = `${nearest.distance_m.toFixed(1)} m <span class="kpi-unit">· ${nearestLabel}</span>`;
    kpiDistance.classList.toggle("danger", nearest.severity >= 3 && nearest.distance_m <= 2.5);
  }
  if (kpiDirection) {
    kpiDirection.textContent = formatBearing(nearest.clock_direction);
  }
  if (logCountTag) {
    logCountTag.textContent = formatDetectionCount(sorted.length);
  }
  if (logEl) {
    logEl.innerHTML = sorted
      .slice(0, 4)
      .map((d) => {
        const name = getHazardLabel(d);
        const verifyText = d.verify || d.verify_ko;
        const verifyNote = verifyText ? ` · ${verifyText}` : "";
        return `<div class="log-row num"><span class="log-row-name">${name}${verifyNote}</span><span class="log-row-meta">${formatBearing(d.clock_direction)} · ${d.distance_m.toFixed(1)} m</span></div>`;
      })
      .join("");
  }
}

function renderChips() {
  const chipsContainer = $("chips");
  if (!chipsContainer) return;
  chipsContainer.innerHTML = "";
  chipElements.clear();
  for (const h of hazards) {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = `chip sev${h.severity}` + (selectedConcepts.has(h.key) ? "" : " off");
    const label = getHazardLabel(h);
    chip.textContent = label;
    chip.title = `${h.prompt || label} (${t("chip_toggle_hint")})`;
    chip.onclick = () => {
      if (selectedConcepts.has(h.key)) {
        if (selectedConcepts.size <= 1) return;
        selectedConcepts.delete(h.key);
        chip.classList.add("off");
        chip.classList.remove("detected");
      } else {
        selectedConcepts.add(h.key);
        chip.classList.remove("off");
      }
    };
    chipsContainer.appendChild(chip);
    chipElements.set(h.key, chip);
  }
}

async function loadStatus() {
  const originUrl = window.location.origin;
  if ($("qrUrl")) {
    $("qrUrl").href = originUrl;
    $("qrUrl").textContent = originUrl;
  }
  if ($("inlineQrUrl")) {
    $("inlineQrUrl").textContent = originUrl;
  }
  try {
    const res = await fetch("/api/status");
    const s = await res.json();
    lastStatus = s;
    serverMode = s.mode;
    if (Array.isArray(s.models)) {
      modelsMeta.clear();
      for (const m of s.models) {
        modelsMeta.set(m.id, m);
      }
    }
    if (s.default_model && modelsMeta.has(s.default_model)) {
      selectedModel = s.default_model;
      if (modelSelect) modelSelect.value = selectedModel;
    }
    hazards = s.hazards || [];
    selectedConcepts = new Set(hazards.map((h) => h.key));
    applyLanguage(currentLang);
  } catch {
    statusEl.textContent = t("status_checking");
  }
}

function captureFrame() {
  if (!video.videoWidth || !video.videoHeight || video.readyState < 2) return null;
  const vw = video.videoWidth;
  const vh = video.videoHeight;
  const longSide = Math.max(vw, vh);
  const scale = CAPTURE_TARGET_LONG / longSide;
  let tw = Math.round(vw * scale);
  let th = Math.round(vh * scale);
  if (tw < CAPTURE_MIN_SHORT) tw = CAPTURE_MIN_SHORT;
  if (th < CAPTURE_MIN_SHORT) th = CAPTURE_MIN_SHORT;
  shot.width = tw;
  shot.height = th;
  shotCtx.drawImage(video, 0, 0, tw, th);
  return shot.toDataURL("image/jpeg", 0.78);
}

function registerFailure(reason) {
  failCount += 1;
  unknownBadge.hidden = false;
  if (currentLang === "ja") {
    unknownBadge.textContent =
      failCount >= 3
        ? `確認不可 · ${failCount}回連続失敗 (${reason})`
        : `確認不可 · ${reason}`;
  } else if (currentLang === "ko") {
    unknownBadge.textContent =
      failCount >= 3
        ? `확인 불가 · 스캔 ${failCount}회 연속 실패 (${reason})`
        : `확인 불가 · ${reason}`;
  } else {
    unknownBadge.textContent =
      failCount >= 3
        ? `Unverified · ${failCount} consecutive failures (${reason})`
        : `Unverified · ${reason}`;
  }
  scanDot.className = "scan-dot error";
  if (failCount >= 3) renderStatus(unknownBadge.textContent);
}

function registerSuccess(latencyMs) {
  failCount = 0;
  unknownBadge.hidden = true;
  scanDot.className = "scan-dot live";
  if (typeof latencyMs === "number") {
    latencyPill.textContent = `${latencyMs} ms`;
    latencyPill.className =
      "latency-pill num " + (latencyMs <= 1500 ? "fast" : "warn");
  }
}

function highlightDetectedChips(dets) {
  const activeKeys = new Set((dets || []).map((d) => d.concept));
  for (const [key, el] of chipElements.entries()) {
    el.classList.toggle("detected", activeKeys.has(key));
  }
}

function scheduleNextTick(delayMs) {
  if (!isRunning) return;
  clearTimeout(loopTimer);
  loopTimer = setTimeout(() => {
    if (isRunning) scanOnce(false);
  }, delayMs);
}

async function scanOnce(reset) {
  if (!isRunning || scanning) return;
  scanning = true;
  const isRealLive = mode === "live" && serverMode === "live";
  let nextDelay = isRealLive ? NEXT_LIVE_DELAY_MS : DEMO_TICK_MS;

  try {
    let body;
    const captureTs = performance.now();
    if (isRealLive) {
      const image = captureFrame();
      if (!image) {
        nextDelay = 200;
        return;
      }
      body = {
        image,
        concepts: [...selectedConcepts],
        mode: "live",
        model: selectedModel,
        lang: currentLang,
        reset: !!reset,
      };
    } else {
      body = {
        frame_index: frame,
        mode: "demo",
        lang: currentLang,
        reset: !!reset,
      };
    }

    const ctl = new AbortController();
    const killer = setTimeout(() => ctl.abort(), SCAN_TIMEOUT_MS);
    let res, data;
    try {
      res = await fetch("/api/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: ctl.signal,
      });
      data = await res.json();
    } finally {
      clearTimeout(killer);
    }
    const clientRttMs = Math.round(performance.now() - captureTs);

    if (data.calls_today !== undefined && lastStatus) {
      lastStatus = {
        ...lastStatus,
        calls_today: data.calls_today,
        daily_cap: data.cap ?? lastStatus.daily_cap,
      };
    }

    if (data.error === "scan_too_soon") {
      nextDelay = Math.max(180, data.retry_after_ms || 250);
      return;
    }
    if (data.error === "daily_call_cap_reached") {
      renderStatus();
      stopAll(t("stop_cap_reached"));
      return;
    }
    if (data.error) {
      registerFailure(data.detail || data.error);
      nextDelay = 700;
      return;
    }

    const reportedMs = data.latency_ms ?? clientRttMs;
    const dets = data.detections || [];
    lastDetections = dets;
    lastReportedMs = reportedMs;
    drawBoxes(dets);
    highlightDetectedChips(dets);
    updateTelemetryKpis(dets, reportedMs);

    if (isRealLive && clientRttMs > ALERT_VALIDITY_MS) {
      registerFailure(
        `${t("err_stale_prefix")} ${(clientRttMs / 1000).toFixed(1)}${t("err_stale_suffix")}`
      );
      return;
    }

    registerSuccess(reportedMs);
    const extra = [];
    if (isRealLive) {
      extra.push(`${reportedMs}ms`);
    }
    if (data.partial_errors && data.partial_errors.length) {
      extra.push(`${t("status_partial_err")}: ${data.partial_errors.length}`);
    }
    extra.push(dets.length ? formatDetectionCount(dets.length) : t("status_clear"));
    renderStatus(extra.join(" · "));

    if (data.alert) {
      emptyAlertFrames = 0;
      lastAlertObj = data.alert;
      fireAlert(data.alert);
    } else if (dets.length > 0) {
      emptyAlertFrames = 0;
      showImmediateBanner(dets[0]);
    } else {
      emptyAlertFrames += 1;
      if (emptyAlertFrames >= 2) {
        banner.hidden = true;
        lastAlertObj = null;
      }
    }

    if (!isRealLive) {
      frame += FRAME_STEP;
      if (frame > LAST_FRAME) {
        if (mode === "live") {
          frame = 0;
          lastSpoken = "";
        } else {
          stopAll(t("stop_demo_done"));
          return;
        }
      }
    }
  } catch (e) {
    registerFailure(e.name === "AbortError" ? t("err_timeout") : t("err_network"));
    nextDelay = 700;
  } finally {
    scanning = false;
    scheduleNextTick(nextDelay);
  }
}

function showImmediateBanner(det) {
  if (!banner.hidden) return;
  banner.hidden = false;
  banner.textContent = formatImmediateBannerText(det);
  banner.className = "alert-banner" + (det.severity < 3 ? " caution" : "");
}

function drawBoxes(dets) {
  canvas.width = canvas.clientWidth;
  canvas.height = canvas.clientHeight;
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  for (const d of dets) {
    if (d.mask_png && d.mask_rect) {
      const [mx, my, mw, mh] = d.mask_rect;
      const img = new Image();
      img.onload = () =>
        ctx.drawImage(
          img,
          mx * canvas.width,
          my * canvas.height,
          mw * canvas.width,
          mh * canvas.height
        );
      img.src = d.mask_png;
    }

    const [x, y, w, h] = d.bbox_norm;
    const px = x * canvas.width;
    const py = y * canvas.height;
    const pw = w * canvas.width;
    const ph = h * canvas.height;

    const color =
      d.severity === 3 ? "#e5484d" : d.severity === 2 ? "#e5a93b" : "#c6f24e";

    ctx.fillStyle =
      d.severity === 3
        ? "rgba(229, 72, 77, 0.16)"
        : d.severity === 2
        ? "rgba(229, 169, 59, 0.14)"
        : "rgba(198, 242, 78, 0.12)";
    ctx.fillRect(px, py, pw, ph);

    ctx.strokeStyle = color;
    ctx.lineWidth = 1.5;
    ctx.strokeRect(px, py, pw, ph);

    const corner = Math.max(10, Math.min(22, Math.min(pw, ph) * 0.2));
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(px, py + corner);
    ctx.lineTo(px, py);
    ctx.lineTo(px + corner, py);
    ctx.moveTo(px + pw - corner, py);
    ctx.lineTo(px + pw, py);
    ctx.lineTo(px + pw, py + corner);
    ctx.moveTo(px, py + ph - corner);
    ctx.lineTo(px, py + ph);
    ctx.lineTo(px + corner, py + ph);
    ctx.moveTo(px + pw - corner, py + ph);
    ctx.lineTo(px + pw, py + ph);
    ctx.lineTo(px + pw, py + ph - corner);
    ctx.stroke();

    const confStr =
      typeof d.confidence === "number" ? ` · ${Math.round(d.confidence * 100)}%` : "";
    const verifyNote = d.verify || d.verify_ko;
    const verifyStr = verifyNote ? ` [${verifyNote}]` : "";
    const label = `${getHazardLabel(d)} · ${d.distance_m.toFixed(1)}m${confStr}${verifyStr}`;
    ctx.font = "600 13px Inter, -apple-system, BlinkMacSystemFont, sans-serif";
    const textW = ctx.measureText(label).width;
    const pillW = textW + 16;
    const pillH = 24;
    const pillX = Math.max(6, Math.min(canvas.width - pillW - 6, px));
    const pillY = py >= pillH + 6 ? py - pillH - 4 : py + 6;

    ctx.fillStyle = color;
    ctx.beginPath();
    if (ctx.roundRect) {
      ctx.roundRect(pillX, pillY, pillW, pillH, 4);
    } else {
      ctx.rect(pillX, pillY, pillW, pillH);
    }
    ctx.fill();

    ctx.fillStyle = "#000000";
    ctx.fillText(label, pillX + 8, pillY + 16);
  }
}

function pickVoiceForLang(langCode) {
  try {
    if (!window.speechSynthesis || !speechSynthesis.getVoices) return null;
    const voices = speechSynthesis.getVoices() || [];
    const prefix = String(langCode || DEFAULT_LANG).toLowerCase().slice(0, 2);
    const matching = voices.filter((v) =>
      String(v.lang || "").toLowerCase().startsWith(prefix)
    );
    if (!matching.length) return null;
    return matching.find((v) => v.localService) || matching[0];
  } catch {
    return null;
  }
}

function speakText(spokenText) {
  if (!audioEnabled || !window.speechSynthesis || !spokenText) return;
  try {
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(spokenText);
    const bcp47 = VOICE_LANG_MAP[currentLang] || VOICE_LANG_MAP[DEFAULT_LANG];
    u.lang = bcp47;
    const voice = pickVoiceForLang(currentLang);
    if (voice) u.voice = voice;
    u.rate = 1.05;
    speechSynthesis.speak(u);
  } catch {}
}

function fireAlert(alert) {
  const alertText = getAlertText(alert);
  banner.hidden = false;
  banner.textContent = `${t("alert_prefix")} · ${alertText}`;
  banner.className =
    "alert-banner" + (alert.level === "caution" ? " caution" : "");

  const now = Date.now();
  if (
    audioEnabled &&
    window.speechSynthesis &&
    (alertText !== lastSpoken || now - lastSpokenAt > 4500)
  ) {
    lastSpoken = alertText;
    lastSpokenAt = now;
    speakText(alertText);
  }
  if (navigator.vibrate) {
    navigator.vibrate(alert.level === "danger" ? [250, 100, 250] : [150]);
  }
}

function unlockSpeech() {
  try {
    if (!window.speechSynthesis) return;
    const warm = new SpeechSynthesisUtterance("");
    warm.volume = 0;
    warm.lang = VOICE_LANG_MAP[currentLang] || VOICE_LANG_MAP[DEFAULT_LANG];
    const voice = pickVoiceForLang(currentLang);
    if (voice) warm.voice = voice;
    speechSynthesis.speak(warm);
  } catch {}
}

async function startLiveScan() {
  if (isRunning) {
    stopAll();
    return;
  }
  unlockSpeech();
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: {
        facingMode: { ideal: "environment" },
        width: { ideal: 1280 },
        height: { ideal: 720 },
      },
      audio: false,
    });
    video.srcObject = stream;
    await video.play().catch(() => {});

    isRunning = true;
    mode = "live";
    frame = 0;
    lastSpoken = "";
    emptyAlertFrames = 0;
    msg.hidden = true;
    banner.hidden = true;
    stage.classList.add("live-active");
    stage.classList.remove("demo-bg");
    if (serverMode !== "live") {
      demoBadge.textContent = t("demo_badge_stub");
      demoBadge.hidden = false;
    } else {
      demoBadge.hidden = true;
    }
    registerSuccess();

    btnLive.textContent = t("btn_live_stop");
    btnLive.classList.remove("primary");
    btnLive.classList.add("stop");
    if (btnDemo) btnDemo.disabled = true;

    setTimeout(() => scanOnce(true), 120);
  } catch {
    msg.hidden = false;
    msgText.textContent = t("cam_denied");
  }
}

function startDemoMode() {
  if (isRunning) stopAll();
  unlockSpeech();
  isRunning = true;
  mode = "demo";
  frame = 0;
  lastSpoken = "";
  emptyAlertFrames = 0;
  msg.hidden = true;
  banner.hidden = true;
  stage.classList.remove("live-active");
  stage.classList.add("demo-bg");
  demoBadge.textContent = t("demo_badge_replay");
  demoBadge.hidden = false;
  registerSuccess();

  btnLive.textContent = t("btn_demo_stop");
  btnLive.classList.remove("primary");
  btnLive.classList.add("stop");
  if (btnDemo) btnDemo.disabled = true;

  scanOnce(true);
}

function stopAll(note) {
  isRunning = false;
  mode = null;
  clearTimeout(loopTimer);
  loopTimer = null;
  if (stream) {
    stream.getTracks().forEach((tr) => tr.stop());
    stream = null;
  }
  video.srcObject = null;
  stage.classList.remove("live-active");
  stage.classList.remove("demo-bg");
  demoBadge.hidden = true;
  banner.hidden = true;
  unknownBadge.hidden = true;
  scanDot.className = "scan-dot";
  latencyPill.textContent = "- ms";
  latencyPill.className = "latency-pill num";
  lastDetections = [];
  lastReportedMs = null;
  lastAlertObj = null;
  highlightDetectedChips([]);
  updateTelemetryKpis([], null);
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  btnLive.textContent = t("btn_live_start");
  btnLive.classList.remove("stop");
  btnLive.classList.add("primary");
  if (btnDemo) btnDemo.disabled = false;

  msg.hidden = false;
  msgText.textContent = note || t("hero_copy");
}

btnLive.onclick = () => {
  if (isRunning) stopAll(t("stop_manual"));
  else startLiveScan();
};
if (btnStartHero) btnStartHero.onclick = () => startLiveScan();
if (btnDemo) btnDemo.onclick = () => startDemoMode();
if (btnDemoHero) btnDemoHero.onclick = () => startDemoMode();

if (btnAudio) {
  btnAudio.onclick = () => {
    audioEnabled = !audioEnabled;
    if (audioLabel) {
      audioLabel.textContent = audioEnabled ? t("voice_on") : t("voice_off");
    } else {
      btnAudio.textContent = audioEnabled ? t("voice_on") : t("voice_off");
    }
    btnAudio.classList.toggle("muted", !audioEnabled);
    if (!audioEnabled && window.speechSynthesis) {
      speechSynthesis.cancel();
    } else if (audioEnabled) {
      unlockSpeech();
    }
  };
}

if (btnAddConcept && conceptForm) {
  btnAddConcept.onclick = () => {
    conceptForm.hidden = !conceptForm.hidden;
    if (!conceptForm.hidden && conceptNameInput) conceptNameInput.focus();
  };
  conceptForm.onsubmit = async (e) => {
    e.preventDefault();
    const rawName = (conceptNameInput.value || "").trim();
    const prompt = (conceptPromptInput.value || "").trim();
    if (!rawName) return;
    try {
      const res = await fetch("/api/concepts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name_ko: rawName,
          name_en: rawName,
          name_ja: rawName,
          prompt: prompt || undefined,
        }),
      });
      const data = await res.json();
      if (data.added && data.hazards) {
        hazards = data.hazards;
        selectedConcepts.add(data.added.key);
        renderChips();
        conceptNameInput.value = "";
        conceptPromptInput.value = "";
        conceptForm.hidden = true;
        renderStatus(`${t("status_concept_added")}: ${getHazardLabel(data.added)}`);
      }
    } catch {}
  };
}

if (btnVoiceConcept && conceptNameInput) {
  btnVoiceConcept.onclick = () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
      conceptNameInput.placeholder = t("voice_unsupported_placeholder");
      conceptNameInput.focus();
      return;
    }
    const rec = new SR();
    rec.lang = VOICE_LANG_MAP[currentLang] || VOICE_LANG_MAP[DEFAULT_LANG];
    rec.interimResults = false;
    rec.maxAlternatives = 1;
    btnVoiceConcept.textContent = t("btn_voice_listening");
    rec.onresult = (ev) => {
      const transcript = ev.results[0][0].transcript.trim();
      if (transcript) conceptNameInput.value = transcript;
    };
    rec.onend = () => {
      btnVoiceConcept.textContent = t("btn_voice_input");
    };
    rec.onerror = () => {
      btnVoiceConcept.textContent = t("btn_voice_input");
    };
    rec.start();
  };
}

if (btnQrModal && qrPanel) {
  btnQrModal.onclick = () => qrPanel.classList.add("open");
}
if (btnExpandQr && qrPanel) {
  btnExpandQr.onclick = () => qrPanel.classList.add("open");
}
if (btnCloseQr && qrPanel) {
  btnCloseQr.onclick = () => qrPanel.classList.remove("open");
}
if (qrPanel) {
  qrPanel.onclick = (e) => {
    if (e.target === qrPanel) qrPanel.classList.remove("open");
  };
}

if ($("btnCopyUrl")) {
  $("btnCopyUrl").onclick = async () => {
    const url = window.location.origin;
    try {
      await navigator.clipboard.writeText(url);
      $("btnCopyUrl").textContent = t("btn_copied_url");
      setTimeout(() => {
        $("btnCopyUrl").textContent = t("btn_copy_url");
      }, 2000);
    } catch {}
  };
}

if (langSelect) {
  langSelect.value = currentLang;
  langSelect.onchange = () => {
    applyLanguage(langSelect.value, { userInitiated: true });
  };
}

if (modelSelect) {
  modelSelect.onchange = () => {
    selectedModel = modelSelect.value;
    syncModelSpecUI();
    renderStatus(t("status_model_changed"));
  };
}

applyLanguage(currentLang);
loadStatus();
