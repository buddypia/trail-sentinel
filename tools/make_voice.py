#!/usr/bin/env python3
"""Pre-generate neural alert voice fragments for Trail Sentinel (F5).

The HUD speaks proximity-style alerts built frontend-side in
``webapp/app.js`` (``getAlertText``): ``{where} · {proximity}, {hazard}``.
The OS Web Speech voice sounds mechanical, so this script synthesizes the
alert vocabulary once — with a neural TTS engine — into tiny MP3 fragments
under ``webapp/audio/``. The app then plays two fragments back-to-back
(A: where + proximity, B: hazard name) and falls back to live Web Speech
for anything without a fragment (custom F7 concepts, dual-threat
sentences, missing files).

Fragment inventory (126 files, well under 1 MB)::

    audio/{en,ko,ja}/a_c{01..12}_{immediate,approaching,ahead}.mp3  (108)
    audio/{en,ko,ja}/b_{snake,wasp_nest,bear,boar,rockfall,slippery}.mp3  (18)

Spoken texts mirror ``getAlertText``/``formatProximity`` wording exactly;
only the ``·``/``・`` separators become commas so the TTS pauses naturally.
Hazard names are single-sourced from ``config.DEFAULT_HAZARDS``.

Usage::

    pip install edge-tts        # once; needs network to the TTS endpoint
    python3 tools/make_voice.py            # generate missing fragments
    python3 tools/make_voice.py --check    # verify all 126 files exist
    python3 tools/make_voice.py --dry-run  # print the manifest, no network
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config import HAZARD_BY_KEY  # noqa: E402

AUDIO_DIR = ROOT / "webapp" / "audio"
MANIFEST_PATH = AUDIO_DIR / "manifest.json"

LANGS = ("en", "ko", "ja")
CLOCKS = tuple(range(1, 13))
TIERS = ("immediate", "approaching", "ahead")
CONCEPTS = (
    "snake",
    "wasp_nest",
    "bear",
    "boar",
    "rockfall",
    "slippery",
)

# Female neural voices: the standard pick for warning systems.
VOICES = {
    "ko": "ko-KR-SunHiNeural",
    "en": "en-US-AvaNeural",
    "ja": "ja-JP-NanamiNeural",
}
DEFAULT_RATE = "+10%"


# === Spoken texts: must mirror webapp/app.js ================================
# where_text ~ getAlertText's `where`; prox_text ~ formatProximity.
def where_text(clock: int, lang: str) -> str:
    if lang == "ja":
        return "正面（12時方向）" if clock == 12 else f"{clock}時方向"
    if lang == "ko":
        return "정면(12시 방향)" if clock == 12 else f"{clock}시 방향"
    return "12 o'clock ahead" if clock == 12 else f"{clock} o'clock"


def prox_text(tier: str, lang: str) -> str:
    table = {
        "ja": {"immediate": "至近", "approaching": "接近", "ahead": "前方警戒"},
        "ko": {"immediate": "초근접", "approaching": "접근", "ahead": "전방 경계"},
        "en": {"immediate": "Immediate", "approaching": "Approaching", "ahead": "Ahead"},
    }
    return table[lang][tier]


def fragment_a_text(clock: int, tier: str, lang: str) -> str:
    """Where + proximity. Commas (not the banner's ·/・) cue TTS pauses."""
    where, prox = where_text(clock, lang), prox_text(tier, lang)
    if lang == "ja":
        return f"{where}、{prox}"
    return f"{where}, {prox}"


def fragment_b_text(concept: str, lang: str) -> str:
    """Hazard name, single-sourced from config (same labels the server sends)."""
    return HAZARD_BY_KEY[concept].label_for(lang)


def fragment_a_relpath(clock: int, tier: str, lang: str) -> str:
    return f"audio/{lang}/a_c{clock:02d}_{tier}.mp3"


def fragment_b_relpath(concept: str, lang: str) -> str:
    return f"audio/{lang}/b_{concept}.mp3"


@dataclass(frozen=True)
class VoiceJob:
    relpath: str
    lang: str
    text: str
    voice: str


def build_manifest(voices: dict[str, str] | None = None) -> list[VoiceJob]:
    """Pure manifest: 126 jobs. No network, no TTS dependency."""
    voices = voices or VOICES
    jobs: list[VoiceJob] = []
    for lang in LANGS:
        for clock in CLOCKS:
            for tier in TIERS:
                jobs.append(
                    VoiceJob(
                        fragment_a_relpath(clock, tier, lang),
                        lang,
                        fragment_a_text(clock, tier, lang),
                        voices[lang],
                    )
                )
        for concept in CONCEPTS:
            jobs.append(
                VoiceJob(
                    fragment_b_relpath(concept, lang),
                    lang,
                    fragment_b_text(concept, lang),
                    voices[lang],
                )
            )
    return jobs


# === Generation (needs the edge-tts package + network) ======================
async def _synthesize(job: VoiceJob, rate: str, sem: asyncio.Semaphore) -> str:
    import edge_tts  # lazy: manifest/check/dry-run work without it

    async with sem:
        out = ROOT / "webapp" / job.relpath
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = out.with_suffix(".tmp.mp3")
        try:
            await edge_tts.Communicate(job.text, job.voice, rate=rate).save(
                str(tmp)
            )
        except Exception:
            if tmp.exists():
                tmp.unlink()
            raise
        tmp.replace(out)
        return job.relpath


async def _generate_all(
    jobs: list[VoiceJob], rate: str, concurrency: int, force: bool
) -> tuple[int, list[str]]:
    pending = [
        j for j in jobs if force or not (ROOT / "webapp" / j.relpath).exists()
    ]
    if not pending:
        return 0, []
    sem = asyncio.Semaphore(max(1, concurrency))
    results = await asyncio.gather(
        *(_synthesize(j, rate, sem) for j in pending), return_exceptions=True
    )
    done, failed = 0, []
    for job, res in zip(pending, results):
        if isinstance(res, Exception):
            failed.append(f"{job.relpath}: {res}")
        else:
            done += 1
            if done % 20 == 0 or done == len(pending):
                print(f"  .. {done}/{len(pending)}", flush=True)
    return done, failed


def cmd_generate(args: argparse.Namespace) -> int:
    try:
        import edge_tts  # noqa: F401
    except ImportError:
        print(
            "error: the 'edge-tts' package is required "
            "(pip install edge-tts)",
            file=sys.stderr,
        )
        return 2
    voices = dict(VOICES)
    if args.ko_voice:
        voices["ko"] = args.ko_voice
    if args.en_voice:
        voices["en"] = args.en_voice
    if args.ja_voice:
        voices["ja"] = args.ja_voice
    jobs = build_manifest(voices)
    print(f"synthesizing {len(jobs)} fragments -> webapp/audio/ ...")
    done, failed = asyncio.run(
        _generate_all(jobs, args.rate, args.jobs, args.force)
    )
    MANIFEST_PATH.write_text(
        json.dumps(
            {
                "voices": voices,
                "rate": args.rate,
                "files": [
                    {"path": j.relpath, "lang": j.lang, "text": j.text}
                    for j in jobs
                ],
            },
            ensure_ascii=False,
            indent=1,
        )
        + "\n"
    )
    print(f"done: {done} synthesized, {len(failed)} failed "
          f"({len(jobs) - done - len(failed)} already present)")
    for f in failed:
        print(f"FAILED {f}", file=sys.stderr)
    return 1 if failed else 0


def cmd_check(_args: argparse.Namespace) -> int:
    jobs = build_manifest()
    missing = [j.relpath for j in jobs if not (ROOT / "webapp" / j.relpath).exists()]
    if missing:
        print(f"missing {len(missing)}/{len(jobs)} fragments:", file=sys.stderr)
        for rel in missing[:10]:
            print(f"  {rel}", file=sys.stderr)
        if len(missing) > 10:
            print(f"  .. and {len(missing) - 10} more", file=sys.stderr)
        print("run: python3 tools/make_voice.py", file=sys.stderr)
        return 1
    print(f"ok: all {len(jobs)} voice fragments present")
    return 0


def cmd_dry_run(_args: argparse.Namespace) -> int:
    for job in build_manifest():
        print(f"{job.relpath}\t[{job.voice}]\t{job.text}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check", action="store_true",
        help="verify all fragments exist, no network",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="print the manifest (path, voice, text), no network",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="re-synthesize even when the file exists",
    )
    parser.add_argument(
        "--jobs", type=int, default=6,
        help="parallel syntheses (default 6)",
    )
    parser.add_argument(
        "--rate", default=DEFAULT_RATE,
        help="speech rate, edge-tts format (default +10%%)",
    )
    parser.add_argument("--ko-voice", default=None)
    parser.add_argument("--en-voice", default=None)
    parser.add_argument("--ja-voice", default=None)
    args = parser.parse_args(argv)
    if args.dry_run:
        return cmd_dry_run(args)
    if args.check:
        return cmd_check(args)
    return cmd_generate(args)


if __name__ == "__main__":
    raise SystemExit(main())
