"""Pre-generated voice fragment tests (F5). No network, no TTS dependency.

Pins the tools/make_voice.py manifest: 126 fragments covering every
(clock x proximity-tier x lang) A-fragment and every (baseline concept x
lang) B-fragment, with spoken texts mirroring webapp/app.js getAlertText /
formatProximity wording so the neural voice says exactly what the banner
shows.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import make_voice
from config import DEFAULT_HAZARDS, HAZARD_BY_KEY


class ManifestShapeTest(unittest.TestCase):
    def test_count(self):
        jobs = make_voice.build_manifest()
        self.assertEqual(len(jobs), 126)

    def test_paths_unique(self):
        jobs = make_voice.build_manifest()
        paths = [j.relpath for j in jobs]
        self.assertEqual(len(set(paths)), len(paths))

    def test_a_covers_every_clock_tier_and_lang(self):
        jobs = make_voice.build_manifest()
        paths = {j.relpath for j in jobs}
        for lang in ("en", "ko", "ja"):
            for clock in range(1, 13):
                for tier in ("immediate", "approaching", "ahead"):
                    self.assertIn(
                        f"audio/{lang}/a_c{clock:02d}_{tier}.mp3", paths
                    )

    def test_b_covers_every_baseline_concept_and_lang(self):
        jobs = make_voice.build_manifest()
        paths = {j.relpath for j in jobs}
        self.assertEqual(len(DEFAULT_HAZARDS), 6)
        for lang in ("en", "ko", "ja"):
            for hazard in DEFAULT_HAZARDS:
                self.assertIn(
                    f"audio/{lang}/b_{hazard.key}.mp3", paths
                )

    def test_all_paths_under_webapp_audio(self):
        for job in make_voice.build_manifest():
            self.assertTrue(job.relpath.startswith("audio/"))
            self.assertTrue(job.relpath.endswith(".mp3"))
            self.assertNotIn(" ", job.relpath)


class SpokenTextParityTest(unittest.TestCase):
    """Golden texts: must match webapp/app.js getAlertText wording.

    Separators differ on purpose (commas cue TTS pauses; the banner shows
    middle dots), but every word must stay identical.
    """

    def test_where_text(self):
        self.assertEqual(make_voice.where_text(12, "ko"), "정면(12시 방향)")
        self.assertEqual(make_voice.where_text(9, "ko"), "9시 방향")
        self.assertEqual(make_voice.where_text(12, "ja"), "正面（12時方向）")
        self.assertEqual(make_voice.where_text(3, "ja"), "3時方向")
        self.assertEqual(make_voice.where_text(12, "en"), "12 o'clock ahead")
        self.assertEqual(make_voice.where_text(11, "en"), "11 o'clock")

    def test_prox_text(self):
        self.assertEqual(make_voice.prox_text("immediate", "ko"), "초근접")
        self.assertEqual(make_voice.prox_text("approaching", "ko"), "접근")
        self.assertEqual(make_voice.prox_text("ahead", "ko"), "전방 경계")
        self.assertEqual(make_voice.prox_text("immediate", "ja"), "至近")
        self.assertEqual(make_voice.prox_text("approaching", "ja"), "接近")
        self.assertEqual(make_voice.prox_text("ahead", "ja"), "前方警戒")
        self.assertEqual(make_voice.prox_text("immediate", "en"), "Immediate")
        self.assertEqual(make_voice.prox_text("approaching", "en"), "Approaching")
        self.assertEqual(make_voice.prox_text("ahead", "en"), "Ahead")

    def test_fragment_a_full_sentence(self):
        self.assertEqual(
            make_voice.fragment_a_text(12, "immediate", "ko"),
            "정면(12시 방향), 초근접",
        )
        self.assertEqual(
            make_voice.fragment_a_text(9, "approaching", "ja"),
            "9時方向、接近",
        )
        self.assertEqual(
            make_voice.fragment_a_text(12, "ahead", "en"),
            "12 o'clock ahead, Ahead",
        )

    def test_fragment_b_matches_config_labels(self):
        for hazard in DEFAULT_HAZARDS:
            for lang in ("en", "ko", "ja"):
                self.assertEqual(
                    make_voice.fragment_b_text(hazard.key, lang),
                    HAZARD_BY_KEY[hazard.key].label_for(lang),
                )

    def test_fragment_b_golden(self):
        self.assertEqual(make_voice.fragment_b_text("snake", "ko"), "뱀")
        self.assertEqual(
            make_voice.fragment_b_text("wasp_nest", "ja"), "スズメバチの巣"
        )
        self.assertEqual(
            make_voice.fragment_b_text("rockfall", "en"), "Rockfall zone"
        )


class VoiceSelectionTest(unittest.TestCase):
    def test_default_voices_cover_all_langs(self):
        jobs = make_voice.build_manifest()
        by_lang = {}
        for job in jobs:
            by_lang.setdefault(job.lang, set()).add(job.voice)
        self.assertEqual(
            {lang: voices.pop() for lang, voices in by_lang.items()
             if len(voices) == 1},
            {"ko": "ko-KR-SunHiNeural",
             "en": "en-US-AvaNeural",
             "ja": "ja-JP-NanamiNeural"},
        )

    def test_custom_voices_override(self):
        jobs = make_voice.build_manifest(
            {"ko": "ko-KR-InJoonNeural",
             "en": "en-US-GuyNeural",
             "ja": "ja-JP-KeitaNeural"}
        )
        voices = {j.voice for j in jobs}
        self.assertEqual(
            voices,
            {"ko-KR-InJoonNeural", "en-US-GuyNeural", "ja-JP-KeitaNeural"},
        )


if __name__ == "__main__":
    unittest.main()
