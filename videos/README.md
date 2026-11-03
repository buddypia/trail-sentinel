# Hazardous Wildlife & Mountain-Trail Hazard Verification Videos and Top-Screen Demo Video

This is the complete set of video assets collected, normalized, and generated for verification and top-screen display in Trail Sentinel (the Meta SAM 3.1 + Muse real-time hiking-trail hazard detection system). All source footage complies with the hackathon rules and uses open licenses (Pexels License / Wikimedia Commons CC BY / CC BY-SA).

---

## 1. Top-Screen "How It Works" Demo Video

| File name | Length / Resolution | Content |
| :--- | :--- | :--- |
| [`hero_how_it_works.mp4`](./hero_how_it_works.mp4) | 15.8 s / 960×540 (24fps) | Looping video shown on the top (standby) screen that visually demonstrates "how it works" (このように動きます).<br>5 scenes — ① snake hidden in fallen leaves → ② venomous snake lurking in leaf litter on the forest floor → ③ rattlesnake hidden in the mountains → ④ wild boars on a mountain trail (simultaneous multi-target tracking & priority triage) → ⑤ bear beside the hiking trail — recorded with **Meta SAM 3.1 pixel segmentation masks, corner-bracket boxes, distance/bearing labels, and audio/vibration alert banners** operating in real time. |

---

## 2. Combined Verification Video (All Scenes in One File, Per-Speed Versions)

So that each scene's animal is reliably detected multiple times even at AI inference latency (1.5–6.0 s per pass), **four slow-playback versions (`0.5x`, `0.33x`, `0.25x`, `0.2x`)** are provided in addition to full speed (`1.0x`).

| Playback speed | File name | Dwell time per scene | Total runtime (all 8 scenes) | Recommended use |
| :---: | :--- | :---: | :---: | :--- |
| **1.0x (full speed)** | [`hazard_verification_combined.mp4`](./hazard_verification_combined.mp4) | **6.0 s** / scene | **48.0 s** (0:48) | Fast environments / footage check |
| **0.5x (half speed)** | [`hazard_verification_combined_0.5x.mp4`](./hazard_verification_combined_0.5x.mp4) | **12.0 s** / scene | **96.0 s** (1:36) | Verification in SAM 3.1 standalone mode (1.5–2.5 s per pass) |
| **0.33x (one-third speed, recommended)** | [`hazard_verification_combined_0.33x.mp4`](./hazard_verification_combined_0.33x.mp4) | **18.0 s** / scene | **144.0 s** (2:24) | **Standard verification (web app default selection)** |
| **0.25x (quarter speed)** | [`hazard_verification_combined_0.25x.mp4`](./hazard_verification_combined_0.25x.mp4) | **24.0 s** / scene | **192.0 s** (3:12) | SAM 3.1 + Muse hybrid verification / verification by filming through a smartphone camera |
| **0.2x (one-fifth speed)** | [`hazard_verification_combined_0.2x.mp4`](./hazard_verification_combined_0.2x.mp4) | **30.0 s** / scene | **240.0 s** (4:00) | High-latency network environments, or when you want each scene judged slowly, multiple times |

---

## 3. Individually Saved Verification Videos (`individual/`)

All normalized to **1280×720 (16:9), 25fps, H.264 MP4 (`yuv420p`)** (6.0 s each).

| # | File name | Time range (within combined video) | Category / detection target | Scene details | Source / license |
| :---: | :--- | :---: | :--- | :--- | :--- |
| 1 | [`individual/01_snake_fallen_leaves_tree.mp4`](./individual/01_snake_fallen_leaves_tree.mp4) | `00:00 – 00:06` | `snake` (snake ① hidden in fallen leaves) | Snake crawling through dead/fallen leaves piled at a tree base (protective-coloration camouflage) | Pexels `11822499` (Ahila devi Manoharan, Pexels License) |
| 2 | [`individual/02_snake_fallen_leaves_closeup.mp4`](./individual/02_snake_fallen_leaves_closeup.mp4) | `00:06 – 00:12` | `snake` (snake ② hidden in fallen leaves) | Snake lurking between dead leaves and branches, rearing its head at center | Pexels `11822448` (Ahila devi Manoharan, Pexels License) |
| 3 | [`individual/03_snake_fallen_leaves_viper.mp4`](./individual/03_snake_fallen_leaves_viper.mp4) | `00:12 – 00:18` | `snake` (venomous snake ③ hidden in fallen leaves) | Common European adder (*Vipera berus*) lurking on leaf litter of the forest floor | Wikimedia Commons (`Петрозаводск, парк Безымянный Ручей, гадюка.webm`, CC BY-SA 4.0) |
| 4 | [`individual/04_snake_mountain_rattlesnake.mp4`](./individual/04_snake_mountain_rattlesnake.mp4) | `00:18 – 00:24` | `snake` (snake ① hidden in the mountains) | Timber rattlesnake (*Crotalus horridus*) lurking among fallen logs, branches, and dead leaves in mountain forest | Wikimedia Commons (`Timber rattlesnake (Crotalus horridus) in Pennsylvania.webm`, CC BY 2.0) |
| 5 | [`individual/05_snake_mountain_rockwall.mp4`](./individual/05_snake_mountain_rockwall.mp4) | `00:24 – 00:30` | `snake` (snake ② hidden in the mountains) | Japanese rat snake (*Elaphe climacophora*) moving between a mossy mountain rock wall and grass | Wikimedia Commons (`Elaphe climacophora - Japanese rat snake - 2015 10 4.webm`, CC BY 4.0) |
| 6 | [`individual/06_boar_mountain_trail.mp4`](./individual/06_boar_mountain_trail.mp4) | `00:30 – 00:36` | `boar` (boars ① in the mountains) | Sounder of wild boar (*Sus scrofa*) walking along a mountain trail carpeted with fallen leaves | Wikimedia Commons (`Sus scrofa-wild boars-Bulgaria-4 VP8.webm`, Vitosha Nature Park, CC BY-SA 4.0) |
| 7 | [`individual/07_boar_forest_encounter.mp4`](./individual/07_boar_forest_encounter.mp4) | `00:36 – 00:42` | `boar` (boar ② in the mountains) | Wild boar encountered head-on on a forest path, dashing off into the roadside fern thicket | Wikimedia Commons (`Wild boar, Dordogne (1).webm`, CC BY-SA 4.0) |
| 8 | [`individual/08_bear_mountain_trail.mp4`](./individual/08_bear_mountain_trail.mp4) | `00:42 – 00:48` | `bear` (bear in the mountains) | Wild American black bear (*Ursus americanus*) emerging from bushes beside a hiking trail | Wikimedia Commons (`Black bear - trail camera.webm`, CC BY-SA 2.0) |

---

## 4. Placement in the Trail Sentinel App

- `trail-sentinel/webapp/videos/hero_how_it_works.mp4` — auto-played as the "How It Works" (このように動きます) preview video inside the top-screen standby card
- `trail-sentinel/webapp/videos/hazard_verification_combined.mp4` — AI real-time scanning can be run directly from the top-screen "Scan with verification video" (検証動画でスキャン) button
- `trail-sentinel/eval/data/verification_videos/` — storage directory for the 8 individual videos (`01`–`08`), the combined video, and the demo video
