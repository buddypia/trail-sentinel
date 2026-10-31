"use strict";
// Trail Sentinel — Meta SAM 3.1 + Muse Wonder Real-Time Tactical HUD
// - Live Camera Mode (F1/F2): captures 640px frames -> POST /api/scan -> mask/bbox + triage alert
// - Demo Mode (F6): replays recorded hero fixture frames 0..60 without camera
// - Live Custom Hazard (F7): adds zero-retraining concepts via voice/text -> POST /api/concepts
// - Latency & Honesty Guardrails (PRD 9.2, 9.4): 3.0s alert validity window + "확인 불가" badge

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
const btnLive = $("btnLive");
const btnDemo = $("btnDemo");
const btnStartHero = $("btnStartHero");
const btnDemoHero = $("btnDemoHero");
const btnAudio = $("btnAudio");
const btnQrModal = $("btnQrModal");
const btnCloseQr = $("btnCloseQr");
const qrPanel = $("qrPanel");
const btnAddConcept = $("btnAddConcept");
const conceptForm = $("conceptForm");
const conceptNameInput = $("conceptNameInput");
const conceptPromptInput = $("conceptPromptInput");
const btnVoiceConcept = $("btnVoiceConcept");

const shot = document.createElement("canvas");
const shotCtx = shot.getContext("2d");

const CAPTURE_TARGET_LONG = 640;
const CAPTURE_MIN_SHORT = 288;
const NEXT_LIVE_DELAY_MS = 280;
const DEMO_TICK_MS = 1000;
const FRAME_STEP = 5;
const LAST_FRAME = 60;
const SCAN_TIMEOUT_MS = 18000;
const ALERT_VALIDITY_MS = 3000; // PRD 9.2: discard alerts arriving >3.0s after capture

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
let hazards = [];
let selectedConcepts = new Set();
let chipElements = new Map();
let failCount = 0;
let lastStatus = null;

function renderStatus(extra) {
  if (!lastStatus) return;
  const isLive = lastStatus.mode === "live";
  const engineLabel = isLive ? "라이브 (Meta SAM 3.1)" : "스텁 (데모 데이터)";
  statusEl.textContent =
    `${engineLabel} · 호출 ${lastStatus.calls_today}/${lastStatus.daily_cap}` +
    (extra ? ` · ${extra}` : "");
}

function renderChips() {
  const chipsContainer = $("chips");
  chipsContainer.innerHTML = "";
  chipElements.clear();
  for (const h of hazards) {
    const chip = document.createElement("span");
    chip.className = `chip sev${h.severity}` + (selectedConcepts.has(h.key) ? "" : " off");
    chip.textContent = h.label_ko;
    chip.title = `${h.prompt || h.label_ko} (눌러서 켜기/끄기)`;
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
  if ($("qrUrl")) {
    $("qrUrl").href = window.location.origin;
    $("qrUrl").textContent = window.location.origin;
  }
  try {
    const res = await fetch("/api/status");
    const s = await res.json();
    lastStatus = s;
    serverMode = s.mode;
    hazards = s.hazards || [];
    selectedConcepts = new Set(hazards.map((h) => h.key));
    renderStatus();
    renderChips();
  } catch {
    statusEl.textContent = "서버 연결 확인 중…";
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
  unknownBadge.textContent =
    failCount >= 3
      ? `확인 불가 — 스캔 ${failCount}회 연속 실패 (${reason})`
      : `확인 불가 — ${reason}`;
  scanDot.className = "scan-dot error";
  if (failCount >= 3) renderStatus(`스캔 실패 ${failCount}회 연속: ${reason}`);
}

function registerSuccess(latencyMs) {
  failCount = 0;
  unknownBadge.hidden = true;
  scanDot.className = "scan-dot live";
  if (typeof latencyMs === "number") {
    latencyPill.textContent = `${latencyMs} ms`;
    latencyPill.className =
      "latency-pill " + (latencyMs <= 1500 ? "fast" : "warn");
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
        reset: !!reset,
      };
    } else {
      body = {
        frame_index: frame,
        mode: "demo",
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
      stopAll("오늘의 API 호출 상한에 도달했습니다. 내일 다시 시도하세요.");
      return;
    }
    if (data.error) {
      registerFailure(data.detail || data.error);
      nextDelay = 700;
      return;
    }

    const reportedMs = data.latency_ms ?? clientRttMs;
    const dets = data.detections || [];
    drawBoxes(dets);
    highlightDetectedChips(dets);

    // PRD 9.2: 3.0s alert validity window check on live scans
    if (isRealLive && clientRttMs > ALERT_VALIDITY_MS) {
      registerFailure(`지연 초과 ${(clientRttMs / 1000).toFixed(1)}초 (>3.0초 유효기간 만료)`);
      return;
    }

    registerSuccess(reportedMs);
    const extra = [];
    if (isRealLive) {
      extra.push(`${reportedMs}ms`);
    }
    if (data.partial_errors && data.partial_errors.length) {
      extra.push(`일부 실패: ${data.partial_errors.length}건`);
    }
    extra.push(dets.length ? `${dets.length}건 감지` : "전방 안전");
    renderStatus(extra.join(" · "));

    if (data.alert) {
      emptyAlertFrames = 0;
      fireAlert(data.alert);
    } else if (dets.length > 0) {
      emptyAlertFrames = 0;
      showImmediateBanner(dets[0]);
    } else {
      emptyAlertFrames += 1;
      if (emptyAlertFrames >= 2) {
        banner.hidden = true;
      }
    }

    if (!isRealLive) {
      frame += FRAME_STEP;
      if (frame > LAST_FRAME) {
        if (mode === "live") {
          frame = 0;
          lastSpoken = "";
        } else {
          stopAll("히어로 데모 장면(프레임 0..60) 재생이 완료되었습니다.");
          return;
        }
      }
    }
  } catch (e) {
    registerFailure(e.name === "AbortError" ? "응답 시간 초과 (10초)" : "네트워크 오류");
    nextDelay = 700;
  } finally {
    scanning = false;
    scheduleNextTick(nextDelay);
  }
}

function showImmediateBanner(det) {
  if (!banner.hidden) return;
  const dir = det.clock_direction || 12;
  banner.hidden = false;
  banner.textContent = `🎯 ${dir}시 방향 ${det.distance_m.toFixed(1)}m ${det.label_ko} 포착`;
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
      d.severity === 3 ? "#ff3b30" : d.severity === 2 ? "#ff9f0a" : "#ffd60a";

    ctx.fillStyle =
      d.severity === 3
        ? "rgba(255, 59, 48, 0.14)"
        : d.severity === 2
        ? "rgba(255, 159, 10, 0.12)"
        : "rgba(255, 214, 10, 0.10)";
    ctx.fillRect(px, py, pw, ph);

    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.setLineDash([6, 4]);
    ctx.strokeRect(px, py, pw, ph);
    ctx.setLineDash([]);

    const corner = Math.max(12, Math.min(26, Math.min(pw, ph) * 0.22));
    ctx.lineWidth = 3.5;
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
    const label = `${d.label_ko} ${d.distance_m.toFixed(1)}m${confStr}`;
    ctx.font = "700 14px -apple-system, BlinkMacSystemFont, system-ui, sans-serif";
    const textW = ctx.measureText(label).width;
    const pillW = textW + 16;
    const pillH = 26;
    const pillX = Math.max(6, Math.min(canvas.width - pillW - 6, px));
    const pillY = py >= pillH + 6 ? py - pillH - 4 : py + 6;

    ctx.fillStyle = color;
    ctx.beginPath();
    if (ctx.roundRect) {
      ctx.roundRect(pillX, pillY, pillW, pillH, 7);
    } else {
      ctx.rect(pillX, pillY, pillW, pillH);
    }
    ctx.fill();

    ctx.fillStyle = "#080c10";
    ctx.fillText(label, pillX + 8, pillY + 18);
  }
}

function fireAlert(alert) {
  banner.hidden = false;
  banner.textContent = `⚠️ ${alert.text_ko}`;
  banner.className =
    "alert-banner" + (alert.level === "caution" ? " caution" : "");

  const now = Date.now();
  if (
    audioEnabled &&
    window.speechSynthesis &&
    (alert.text_ko !== lastSpoken || now - lastSpokenAt > 4500)
  ) {
    lastSpoken = alert.text_ko;
    lastSpokenAt = now;
    try {
      speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(alert.text_ko);
      u.lang = "ko-KR";
      u.rate = 1.05;
      speechSynthesis.speak(u);
    } catch {}
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
    warm.lang = "ko-KR";
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
    stage.classList.remove("demo-bg");
    if (serverMode !== "live") {
      demoBadge.textContent = "스텁 시뮬레이션 중 (카메라 프리뷰 + 데모 판정)";
      demoBadge.hidden = false;
    } else {
      demoBadge.hidden = true;
    }
    registerSuccess();

    btnLive.textContent = "⏹ 스캔 중지";
    btnLive.classList.remove("primary");
    btnLive.classList.add("stop");
    if (btnDemo) btnDemo.disabled = true;

    setTimeout(() => scanOnce(true), 120);
  } catch {
    msg.hidden = false;
    msgText.textContent =
      "카메라 권한이 거부되었거나 카메라를 쓸 수 없습니다. 카메라 권한을 허용하거나 [▶ 데모] 모드로 확인해 보세요.";
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
  stage.classList.add("demo-bg");
  demoBadge.textContent = "데모 장면 재생 중 (카메라 아님)";
  demoBadge.hidden = false;
  registerSuccess();

  btnLive.textContent = "⏹ 데모 중지";
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
    stream.getTracks().forEach((t) => t.stop());
    stream = null;
  }
  video.srcObject = null;
  stage.classList.remove("demo-bg");
  demoBadge.hidden = true;
  banner.hidden = true;
  unknownBadge.hidden = true;
  scanDot.className = "scan-dot";
  latencyPill.textContent = "-- ms";
  latencyPill.className = "latency-pill";
  highlightDetectedChips([]);
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  btnLive.textContent = "📷 실시간 스캔 시작";
  btnLive.classList.remove("stop");
  btnLive.classList.add("primary");
  if (btnDemo) btnDemo.disabled = false;

  msg.hidden = false;
  if (note) {
    msgText.textContent = note;
  } else {
    msgText.textContent =
      "카메라로 등산로나 테스트 영상을 비추면 텍스트 프롬프트로 정의된 위험 요소를 분할·추적하고, 위험 거리 진입 시 방향과 거리를 음성·진동으로 경고합니다.";
  }
}

btnLive.onclick = () => {
  if (isRunning) stopAll("중지됨. 다시 시작할 수 있습니다.");
  else startLiveScan();
};
if (btnStartHero) btnStartHero.onclick = () => startLiveScan();
if (btnDemo) btnDemo.onclick = () => startDemoMode();
if (btnDemoHero) btnDemoHero.onclick = () => startDemoMode();

if (btnAudio) {
  btnAudio.onclick = () => {
    audioEnabled = !audioEnabled;
    btnAudio.textContent = audioEnabled ? "🔊 음성 ON" : "🔇 음성 OFF";
    btnAudio.classList.toggle("muted", !audioEnabled);
    if (!audioEnabled && window.speechSynthesis) {
      speechSynthesis.cancel();
    } else if (audioEnabled) {
      unlockSpeech();
    }
  };
}

// F7: Zero-retraining live custom hazard addition (voice + text)
if (btnAddConcept && conceptForm) {
  btnAddConcept.onclick = () => {
    conceptForm.hidden = !conceptForm.hidden;
    if (!conceptForm.hidden && conceptNameInput) conceptNameInput.focus();
  };
  conceptForm.onsubmit = async (e) => {
    e.preventDefault();
    const name_ko = (conceptNameInput.value || "").trim();
    const prompt = (conceptPromptInput.value || "").trim();
    if (!name_ko) return;
    try {
      const res = await fetch("/api/concepts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name_ko, prompt: prompt || undefined }),
      });
      const data = await res.json();
      if (data.added && data.hazards) {
        hazards = data.hazards;
        selectedConcepts.add(data.added.key);
        renderChips();
        conceptNameInput.value = "";
        conceptPromptInput.value = "";
        conceptForm.hidden = true;
        renderStatus(`새 개념 추가됨: ${data.added.label_ko}`);
      }
    } catch {}
  };
}

if (btnVoiceConcept && conceptNameInput) {
  btnVoiceConcept.onclick = () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
      conceptNameInput.placeholder = "브라우저 음성인식 미지원 — 텍스트로 입력하세요";
      conceptNameInput.focus();
      return;
    }
    const rec = new SR();
    rec.lang = "ko-KR";
    rec.interimResults = false;
    rec.maxAlternatives = 1;
    btnVoiceConcept.textContent = "🔴";
    rec.onresult = (ev) => {
      const transcript = ev.results[0][0].transcript.trim();
      if (transcript) conceptNameInput.value = transcript;
    };
    rec.onend = () => {
      btnVoiceConcept.textContent = "🎙";
    };
    rec.onerror = () => {
      btnVoiceConcept.textContent = "🎙";
    };
    rec.start();
  };
}

if (btnQrModal && qrPanel) {
  btnQrModal.onclick = () => qrPanel.classList.add("open");
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
      $("btnCopyUrl").textContent = "✅ URL 복사 완료!";
      setTimeout(() => {
        $("btnCopyUrl").textContent = "🔗 접속 URL 복사";
      }, 2000);
    } catch {}
  };
}

loadStatus();
