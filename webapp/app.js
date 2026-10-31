"use strict";
// Trail Sentinel web app.
//  - demo mode: fixture frame indices -> POST /api/scan -> overlay + alert.
//  - camera (live) mode: captures the real video frame (canvas, max width
//    1024, JPEG data URL) and POSTs it with the selected hazard concepts.
//    Live scans only work when the server runs with TRAIL_SENTINEL_LIVE=1;
//    otherwise the server says so and the app shows "확인 불가" instead of
//    pretending. Failures are never silent (PRD 9.4): the 확인 불가 badge
//    appears on the first failure and stays until a scan succeeds.
const $ = (id) => document.getElementById(id);
const video = $("cam"), canvas = $("overlay"), ctx = canvas.getContext("2d");
const banner = $("alertBanner"), msg = $("message"), msgText = $("messageText") || msg, statusEl = $("status");
const unknownBadge = $("unknownBadge");
const shot = document.createElement("canvas"), shotCtx = shot.getContext("2d");

const SCAN_MS = 1200, FRAME_STEP = 5, LAST_FRAME = 60; // hero fixture: frames 0..60
const LIVE_MS = 5000;            // live tick; server enforces >= 2.5s anyway
const SCAN_TIMEOUT_MS = 40000;   // covers 10s/call server cap + join time
const CAPTURE_MAX_WIDTH = 1024;

let timer = null, stream = null, frame = 0, mode = null, lastSpoken = "", scanning = false;
let serverMode = "stub", hazards = [], selectedConcepts = new Set();
let failCount = 0, lastStatus = null;

function renderStatus(extra) {
  if (!lastStatus) return;
  const modeText = lastStatus.mode === "live"
    ? "라이브 (실제 SAM 3.1 API)" : "스텁 (가짜 데이터, 실제 API 아님)";
  statusEl.textContent =
    `모드: ${modeText} · 오늘 호출 ${lastStatus.calls_today}/${lastStatus.daily_cap}` +
    (extra ? ` · ${extra}` : "");
}

async function loadStatus() {
  try {
    const s = await (await fetch("/api/status")).json();
    lastStatus = s; serverMode = s.mode;
    hazards = s.hazards;
    selectedConcepts = new Set(hazards.map(h => h.key));
    renderStatus();
    $("chips").innerHTML = "";
    for (const h of hazards) {
      const chip = document.createElement("span");
      chip.className = `chip sev${h.severity}`;
      chip.textContent = h.label_ko;
      chip.title = "눌러서 스캔 대상 켜기/끄기";
      chip.onclick = () => {
        if (selectedConcepts.has(h.key)) { selectedConcepts.delete(h.key); chip.classList.add("off"); }
        else { selectedConcepts.add(h.key); chip.classList.remove("off"); }
      };
      $("chips").appendChild(chip);
    }
  } catch { statusEl.textContent = "서버 연결 실패"; }
}

function captureFrame() {
  if (!video.videoWidth || video.readyState < 2) return null;
  const scale = Math.min(1, CAPTURE_MAX_WIDTH / video.videoWidth);
  shot.width = Math.max(1, Math.round(video.videoWidth * scale));
  shot.height = Math.max(1, Math.round(video.videoHeight * scale));
  shotCtx.drawImage(video, 0, 0, shot.width, shot.height);
  return shot.toDataURL("image/jpeg", 0.8);
}

function registerFailure(reason) {
  failCount += 1;
  unknownBadge.hidden = false;
  unknownBadge.textContent = failCount >= 3
    ? `확인 불가 — 스캔 ${failCount}회 연속 실패 (${reason})`
    : `확인 불가 — 스캔 실패 (${reason})`;
  if (failCount >= 3) renderStatus(`스캔 실패 ${failCount}회 연속: ${reason}`);
}

function registerSuccess() {
  failCount = 0;
  unknownBadge.hidden = true;
}

async function scan(reset) {
  if (scanning) return; // one in-flight scan at a time: no overlapping requests
  scanning = true;
  try {
    let body;
    if (mode === "live" && serverMode === "live") {
      const image = captureFrame();
      if (!image) { registerFailure("카메라 영상이 아직 준비되지 않음"); return; }
      body = { image, concepts: [...selectedConcepts], mode };
    } else {
      body = { frame_index: frame, mode: "demo", reset: !!reset };
    }
    const ctl = new AbortController();
    const killer = setTimeout(() => ctl.abort(), SCAN_TIMEOUT_MS);
    let res, data;
    try {
      res = await fetch("/api/scan", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body), signal: ctl.signal,
      });
      data = await res.json();
    } finally { clearTimeout(killer); }

    if (data.calls_today !== undefined) {
      lastStatus = { ...lastStatus, calls_today: data.calls_today, daily_cap: data.cap };
    }
    if (data.error === "scan_too_soon") return; // rate guard, not a failure
    if (data.error === "daily_call_cap_reached") {
      renderStatus();
      stopAll("오늘의 API 호출 상한에 도달했습니다. 내일 다시 시도하세요.");
      return;
    }
    if (data.error === "live_not_enabled") {
      stopAll("서버가 스텁 모드입니다. 라이브 스캔은 서버를 TRAIL_SENTINEL_LIVE=1로 " +
        "실행해야 합니다. (지금은 카메라 프레임을 분석하지 않았습니다)");
      return;
    }
    if (data.error) { registerFailure(data.detail || data.error); return; }

    registerSuccess();
    drawBoxes(data.detections || []);
    const extra = [];
    if (data.mode === "live" && data.latency_ms !== undefined)
      extra.push(`스캔 지연 ${(data.latency_ms / 1000).toFixed(1)}초`);
    if (data.partial_errors && data.partial_errors.length)
      extra.push(`일부 개념 실패: ${data.partial_errors.join(", ")}`);
    renderStatus(extra.join(" · ") || undefined);
    if (data.alert) fireAlert(data.alert);
  } catch (e) {
    registerFailure(e.name === "AbortError" ? "응답 시간 초과" : "네트워크 오류");
  } finally {
    scanning = false;
  }
}

function drawBoxes(dets) {
  canvas.width = canvas.clientWidth; canvas.height = canvas.clientHeight;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  for (const d of dets) {
    if (d.mask_png && d.mask_rect) {
      const [mx, my, mw, mh] = d.mask_rect;
      const img = new Image();
      img.onload = () => ctx.drawImage(img, mx * canvas.width, my * canvas.height,
                                       mw * canvas.width, mh * canvas.height);
      img.src = d.mask_png;
    }
    const [x, y, w, h] = d.bbox_norm;
    const px = x * canvas.width, py = y * canvas.height;
    ctx.strokeStyle = d.severity === 3 ? "#ff3b30" : d.severity === 2 ? "#ff9500" : "#ffd60a";
    ctx.lineWidth = 3;
    ctx.strokeRect(px, py, w * canvas.width, h * canvas.height);
    ctx.font = "bold 16px system-ui";
    const label = `${d.label_ko} ${d.distance_m.toFixed(1)}m`;
    ctx.fillStyle = ctx.strokeStyle;
    ctx.fillRect(px, Math.max(0, py - 22), ctx.measureText(label).width + 10, 22);
    ctx.fillStyle = "#000";
    ctx.fillText(label, px + 5, Math.max(16, py - 6));
  }
}

function fireAlert(alert) {
  banner.hidden = false;
  banner.textContent = `⚠️ ${alert.text_ko}`;
  banner.className = "alert-banner" + (alert.level === "caution" ? " caution" : "");
  if (alert.text_ko !== lastSpoken) {           // speak each new warning once
    lastSpoken = alert.text_ko;
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(alert.text_ko);
    u.lang = "ko-KR";
    speechSynthesis.speak(u);
  }
  if (navigator.vibrate) navigator.vibrate(alert.level === "danger" ? [250, 100, 250] : [150]);
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

function startLoop(m) {
  mode = m; frame = 0; lastSpoken = "";
  banner.hidden = true; msg.hidden = true;
  registerSuccess();
  $("btnLive").disabled = $("btnDemo").disabled = true;
  $("btnStop").disabled = false;
  const isRealLive = mode === "live" && serverMode === "live";
  scan(true);
  timer = setInterval(() => {
    if (isRealLive) { scan(false); return; }
    frame += FRAME_STEP;
    if (frame > LAST_FRAME) {
      if (mode === "live") { frame = 0; lastSpoken = ""; scan(true); return; }
      stopAll("데모 장면이 끝났습니다.");
      return;
    }
    scan(false);
  }, isRealLive ? LIVE_MS : SCAN_MS);
}

function stopAll(note) {
  clearInterval(timer); timer = null;
  if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; }
  video.srcObject = null;
  $("stage").classList.remove("demo-bg");
  $("demoBadge").hidden = true;
  $("btnLive").disabled = $("btnDemo").disabled = false;
  $("btnStop").disabled = true;
  banner.hidden = true;
  registerSuccess();
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  if (note) { msg.hidden = false; msgText.textContent = note; }
}

$("btnDemo").onclick = () => {
  unlockSpeech();
  $("stage").classList.add("demo-bg");
  $("demoBadge").textContent = "데모 장면 재생 중 (카메라 아님)";
  $("demoBadge").hidden = false;
  startLoop("demo");
};
$("btnStop").onclick = () => stopAll("중지됨. 다시 시작할 수 있습니다.");
$("btnLive").onclick = async () => {
  unlockSpeech();
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: "environment" }, audio: false });
    video.srcObject = stream;
    if (serverMode !== "live") {
      $("demoBadge").textContent = "스텁 시뮬레이션 중 (카메라 프리뷰 + 데모 판정)";
      $("demoBadge").hidden = false;
    }
    startLoop("live");
  } catch {
    msg.hidden = false;
    msgText.textContent = "카메라 권한이 거부됐거나 카메라를 쓸 수 없습니다. " +
      "브라우저 설정에서 카메라를 허용하거나, 데모 모드로 확인해 보세요. " +
      "(카메라는 HTTPS 또는 localhost에서만 동작합니다)";
  }
};

if ($("btnCopyUrl")) {
  $("btnCopyUrl").onclick = async () => {
    const url = ($("qrUrl") && $("qrUrl").href) || window.location.href;
    try {
      await navigator.clipboard.writeText(url);
      $("btnCopyUrl").textContent = "✅ 복사 완료!";
      setTimeout(() => { $("btnCopyUrl").textContent = "🔗 URL 복사"; }, 2000);
    } catch {}
  };
}

loadStatus();
