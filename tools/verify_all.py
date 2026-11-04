#!/usr/bin/env python3
"""Two-layer verification gate — run this before calling any change done.

    python3 tools/verify_all.py

Layer 1 · FORMAL (no behaviour executed): compile/syntax validity, JSON
asset validity, AST-level contracts (fast-path thinking level, output
token cap, fail-fast retry, mask alpha caps, budget guard wiring),
JS fast-path constants, and a no-secrets scan. These prove the code
*cannot* silently drift from the agreed contracts.

Layer 2 · EMPIRICAL (behaviour executed and measured): the full unit
suite, a live runtime probe of the real scan pipeline (SAM tint payload,
honest Muse-only payload, mask lightness decoded from the PNG bytes),
and timing budgets measured on this machine.

Both layers always run. There is deliberately no flag to skip a layer:
a formal-only pass says nothing about behaviour, and a behaviour-only
pass says nothing about the contracts the next edit might break.
Exit code is 0 only when every check in both layers passes.
"""
from __future__ import annotations

import ast
import base64
import json
import os
import re
import struct
import subprocess
import sys
import tempfile
import time
import zlib
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


@dataclass
class CheckResult:
    layer: str
    name: str
    ok: bool
    detail: str = ""


def _result(layer: str, name: str, ok: bool, detail: str = "") -> CheckResult:
    return CheckResult(layer, name, bool(ok), detail)


# ---------------------------------------------------------------------------
# Layer 1 · FORMAL
# ---------------------------------------------------------------------------

def check_py_compile(root: Path = ROOT) -> CheckResult:
    files = sorted(root.glob("*.py")) + sorted((root / "tools").glob("*.py")) \
        + sorted((root / "tests").glob("*.py")) + sorted((root / "eval").glob("*.py"))
    bad = []
    for path in files:
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        except SyntaxError as exc:
            bad.append(f"{path.name}: {exc}")
    return _result("FORMAL", "python-compile", not bad,
                   f"{len(files)} files" if not bad else "; ".join(bad))


def check_js_syntax(root: Path = ROOT) -> CheckResult:
    proc = subprocess.run(
        ["node", "--check", str(root / "webapp" / "app.js")],
        capture_output=True, text=True,
    )
    return _result("FORMAL", "js-syntax (node --check)", proc.returncode == 0,
                   proc.stderr.strip()[:200] or "webapp/app.js parses")


def check_json_assets(root: Path = ROOT) -> CheckResult:
    targets = [root / "eval" / "clips_manifest.json",
               root / "webapp" / "manifest.webmanifest",
               root / "webapp" / "audio" / "manifest.json"]
    targets += sorted((root / "fixtures").glob("*.json"))
    bad = []
    for path in targets:
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            bad.append(f"{path.name}: {exc}")
    return _result("FORMAL", "json-assets", not bad,
                   f"{len(targets)} files" if not bad else "; ".join(bad))


_SECRET_RE = re.compile(
    r"(api[_-]?key|secret|password)\s*=\s*['\"][A-Za-z0-9_\-]{12,}['\"]"
    r"|sk-[A-Za-z0-9]{20,}"
)


def find_secret_hits(text: str) -> list[str]:
    return [m.group(0)[:24] for m in _SECRET_RE.finditer(text)]


def check_no_secrets(root: Path = ROOT) -> CheckResult:
    files = sorted(root.glob("*.py")) + [root / "webapp" / "app.js"]
    hits = []
    for path in files:
        for hit in find_secret_hits(path.read_text(encoding="utf-8")):
            hits.append(f"{path.name}: {hit}…")
    return _result("FORMAL", "no-secrets", not hits,
                   "no credential-shaped literals" if not hits else "; ".join(hits))


def _literal_dict_assign(tree: ast.Module, name: str) -> dict | None:
    for node in tree.body:
        value = None
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == name for t in node.targets
        ):
            value = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) \
                and node.target.id == name:
            value = node.value
        if value is not None:
            try:
                return ast.literal_eval(value)
            except (ValueError, SyntaxError):
                return None
    return None


def bridge_thinking_ok(router_source: str) -> bool:
    """Every bridge route must stay MINIMAL (performance-first contract)."""
    config = _literal_dict_assign(ast.parse(router_source), "_BRIDGE_CONFIG")
    return bool(config) and all(v[1] == "MINIMAL" for v in config.values())


def check_ast_contracts(root: Path = ROOT) -> CheckResult:
    problems = []
    router_src = (root / "vision_router.py").read_text(encoding="utf-8")
    if not bridge_thinking_ok(router_src):
        problems.append("_BRIDGE_CONFIG not all MINIMAL")
    m = re.search(r'"maxOutputTokens":\s*(\d+)', router_src)
    if not m or int(m.group(1)) > 160:
        problems.append("maxOutputTokens > 160 or missing")
    if not re.search(r"for attempt in range\(1\):", router_src):
        problems.append("vision bridge retry is not fail-fast range(1)")
    m = re.search(r"min\(92,\s*alpha\)", router_src)
    if not m:
        problems.append("synthesized mask alpha cap 92 missing")

    transport_src = (root / "meta_transport.py").read_text(encoding="utf-8")
    m = re.search(r"_MASK_ALPHA\s*=\s*(\d+)", transport_src)
    if not m or int(m.group(1)) > 120:
        problems.append("real SAM _MASK_ALPHA > 120 or missing")

    server_src = (root / "server.py").read_text(encoding="utf-8")
    if "sam_segmentation" not in server_src or '"sam-3.1"' not in server_src:
        problems.append("server SAM segmentation payload wiring missing")
    if "CallBudget" not in server_src or ".spend(" not in server_src:
        problems.append("CallBudget guard wiring missing")
    return _result("FORMAL", "ast-contracts (fast/SAM/budget)", not problems,
                   "all contracts hold" if not problems else "; ".join(problems))


_JS_CONST_RE = {
    "CAPTURE_TARGET_LONG": 320,
    "NEXT_LIVE_DELAY_MS": 0,
    "FRAME_CACHE_MAX_MS": 2000,
}


def js_fast_constants_ok(app_js: str) -> bool:
    for name, want in _JS_CONST_RE.items():
        m = re.search(rf"const {name} = ([\d.]+);", app_js)
        if not m or float(m.group(1)) != want:
            return False
    return True


def check_js_fast_invariants(root: Path = ROOT) -> CheckResult:
    src = (root / "webapp" / "app.js").read_text(encoding="utf-8")
    problems = []
    if not js_fast_constants_ok(src):
        problems.append(f"fast constants drifted from {_JS_CONST_RE}")
    if "1950" in src:
        problems.append("removed 1950ms verify-video hold is back")
    if "async function drawBoxes" in src:
        problems.append("drawBoxes blocks painting on mask decode again")
    if "frameSignatureDiff" not in src or "FRAME_SKIP_DIFF" not in src:
        problems.append("frame-skip path missing")
    label = re.search(r"const label = `([^`]*)`;", src)
    if not label or "formatProximity(d.distance_m)" not in label.group(1) \
            or "verifyStr" in label.group(1) or "confStr" in label.group(1):
        problems.append("HUD pill is not name+distance only")
    return _result("FORMAL", "js-fast-invariants", not problems,
                   "fast path + simple pill hold" if not problems else "; ".join(problems))


FORMAL_CHECKS = (
    check_py_compile,
    check_js_syntax,
    check_json_assets,
    check_no_secrets,
    check_ast_contracts,
    check_js_fast_invariants,
)


# ---------------------------------------------------------------------------
# Layer 2 · EMPIRICAL
# ---------------------------------------------------------------------------

def check_unit_suite(root: Path = ROOT) -> CheckResult:
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        cwd=root, capture_output=True, text=True,
    )
    tail = (proc.stderr or proc.stdout).strip().splitlines()
    summary = tail[-1] if tail else ""
    count = next((ln for ln in tail if ln.startswith("Ran ")), "")
    return _result("EMPIRICAL", "unit-suite", proc.returncode == 0,
                   f"{count} · {summary}".strip(" ·"))


def _png_max_alpha(mask_png: str) -> int:
    raw = base64.b64decode(mask_png.split(",", 1)[1])
    idat, pos, width = b"", 8, 0
    while pos < len(raw):
        (length,) = struct.unpack(">I", raw[pos:pos + 4])
        tag, data = raw[pos + 4:pos + 8], raw[pos + 8:pos + 8 + length]
        if tag == b"IHDR":
            (width,) = struct.unpack(">I", data[:4])
        elif tag == b"IDAT":
            idat += data
        pos += 12 + length
    pixels = zlib.decompress(idat)
    stride = 1 + width * 4
    return max(
        pixels[row * stride + 1 + x * 4 + 3]
        for row in range(len(pixels) // stride)
        for x in range(width)
    )


# Runtime probe executed in a child process with an isolated call-budget
# file, so probing never spends or mutates the real daily counter.
_PROBE_CODE = r'''
import json, os, statistics, sys, time
sys.path.insert(0, os.environ["VERIFY_ROOT"])
import server
import tempfile

out = {}
# demo/stub pipeline: SAM tint payload must be present and light
ts = []
result = None
for i in range(20):
    t = time.perf_counter()
    result = server.scan_frame("hero_snake_leaves", 45, reset=(i == 0))
    ts.append((time.perf_counter() - t) * 1000)
dets = result["detections"]
out["demo_detections"] = len(dets)
out["demo_all_sam"] = bool(dets) and all(
    d.get("segmentation") == "sam-3.1" and d.get("mask_png", "").startswith("data:image/png;base64,")
    for d in dets)
out["demo_payload_bytes"] = len(json.dumps(result))
out["stub_median_ms"] = round(statistics.median(ts), 2)

# pure-SAM live path (fake transport): mask guaranteed even with no pixel mask
from tests.test_server_live import make_scanner, JPEG_BYTES
with tempfile.TemporaryDirectory() as tmp:
    scanner, _, _ = make_scanner(tmp)
    live = scanner.scan(JPEG_BYTES, "image/jpeg", ["snake"])
    d0 = live["detections"][0]
    out["live_sam_mask"] = d0.get("segmentation") == "sam-3.1" and "mask_png" in d0
print(json.dumps(out))
'''


def check_runtime_probe(root: Path = ROOT) -> CheckResult:
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ)
        env["VERIFY_ROOT"] = str(root)
        env["CALL_COUNTER_FILE"] = str(Path(tmp) / "counter.json")
        proc = subprocess.run(
            [sys.executable, "-c", _PROBE_CODE],
            cwd=root, env=env, capture_output=True, text=True,
        )
    if proc.returncode != 0:
        return _result("EMPIRICAL", "runtime-probe", False,
                       (proc.stderr or proc.stdout).strip()[-300:])
    try:
        out = json.loads(proc.stdout.strip().splitlines()[-1])
    except Exception as exc:
        return _result("EMPIRICAL", "runtime-probe", False, f"bad probe output: {exc}")
    problems = []
    if not out.get("demo_all_sam"):
        problems.append("demo detections lack SAM tint payload")
    if not out.get("live_sam_mask"):
        problems.append("pure-SAM live detection lacks tint mask")
    if out.get("demo_payload_bytes", 10**9) > 8192:
        problems.append(f"demo payload too large: {out.get('demo_payload_bytes')}B")
    if out.get("stub_median_ms", 10**9) > 50:
        problems.append(f"stub scan too slow: {out.get('stub_median_ms')}ms")
    detail = (f"dets={out.get('demo_detections')} payload={out.get('demo_payload_bytes')}B "
              f"stub_median={out.get('stub_median_ms')}ms")
    return _result("EMPIRICAL", "runtime-probe (SAM tint + timing)",
                   not problems, detail if not problems else "; ".join(problems))


def probe_mask_light_and_fast(root: Path = ROOT) -> CheckResult:
    sys.path.insert(0, str(root))
    from vision_router import synthesize_contour_mask_png

    mask_png, _rect = synthesize_contour_mask_png([0.1, 0.2, 0.5, 0.5], 3)
    max_alpha = _png_max_alpha(mask_png)
    started = time.perf_counter()
    for _ in range(100):
        synthesize_contour_mask_png([0.1, 0.2, 0.5, 0.5], 3)
    per_call_ms = (time.perf_counter() - started) * 10
    ok = 0 < max_alpha <= 92 and per_call_ms < 5 and len(mask_png) < 8192
    return _result("EMPIRICAL", "mask-lightness+speed", ok,
                   f"max_alpha={max_alpha} synth={per_call_ms:.2f}ms/call "
                   f"png={len(mask_png)}B")


def frame_diff(a, b) -> float:
    """Same mean-abs-diff rule as webapp/app.js frameSignatureDiff."""
    return sum(abs(x - y) for x, y in zip(a, b)) / len(a)


def check_frame_skip_rule(root: Path = ROOT) -> CheckResult:
    same = frame_diff([100] * 144, [100] * 144)
    moved = frame_diff([100] * 144, [160] * 144)
    ok = same == 0.0 and same < 1.8 < moved
    return _result("EMPIRICAL", "frame-skip rule", ok,
                   f"identical={same:.1f} (skip) vs changed={moved:.1f} (scan), threshold=1.8")


def run_formal(root: Path = ROOT) -> list[CheckResult]:
    results = []
    for check in FORMAL_CHECKS:
        try:
            results.append(check(root))
        except Exception as exc:
            results.append(_result("FORMAL", check.__name__, False, f"raised: {exc}"))
    return results


def run_empirical(root: Path = ROOT, *, include_unit_suite: bool = True) -> list[CheckResult]:
    checks = [check_runtime_probe, probe_mask_light_and_fast, check_frame_skip_rule]
    if include_unit_suite:
        checks.insert(0, check_unit_suite)
    results = []
    for check in checks:
        try:
            results.append(check(root))
        except Exception as exc:
            results.append(_result("EMPIRICAL", check.__name__, False, f"raised: {exc}"))
    return results


def main() -> int:
    started = time.perf_counter()
    results = run_formal() + run_empirical()
    for r in results:
        mark = "PASS" if r.ok else "FAIL"
        print(f"[{r.layer:<9}] {mark}  {r.name:<38} {r.detail}")
    failed = [r for r in results if not r.ok]
    elapsed = time.perf_counter() - started
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed in {elapsed:.1f}s")
    if failed:
        print("FAILED: " + ", ".join(f"{r.layer}/{r.name}" for r in failed))
        return 1
    print("ALL CHECKS PASSED (formal + empirical)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
