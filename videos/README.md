# 危険生物・山岳危険物検知 検証用動画 & トップ画面デモ動画

Trail Sentinel（Meta SAM 3.1 + Muse リアルタイム登山道危険検知システム）の検証用およびトップ画面表示用に収集・整形・生成した動画アセット一式です。すべての元映像はハッカソン規約に準拠したオープンライセンス（Pexels License / Wikimedia Commons CC BY / CC BY-SA）の映像を使用しています。

---

## 1. トップ画面表示用「このように動きます」デモ動画

| ファイル名 | 長さ / 解像度 | 内容 |
| :--- | :--- | :--- |
| [`hero_how_it_works.mp4`](./hero_how_it_works.mp4) | 15.8秒 / 960×540 (24fps) | トップ画面（スタンバイ画面）で「このように動きます」を視覚的に紹介するループ動画。<br>① 落葉に隠れている蛇 → ② 林床の落葉に潜む毒蛇 → ③ 山中に隠れているガラガラヘビ → ④ 山道の猪（複数頭同時追跡＆優先度トリアージ） → ⑤ 登山道脇の熊 の5シーンに対し、**Meta SAM 3.1 ピクセル分割マスク・コーナーブラケット枠・距離/方位ラベル・音声/振動警告バナー**がリアルタイムに動作する様子を収録。 |

---

## 2. 結合済み検証用動画（1本にまとめた動画・各速度バージョン）

AIの推論レイテンシ（1.5〜6.0秒/回）でも各シーンの動物を複数回しっかり検知できるよう、等倍（`1.0x`）に加えて**4段階のスロー再生バージョン（`0.5x`, `0.33x`, `0.25x`, `0.2x`）**を用意しています。

| 再生速度 | ファイル名 | 1シーンあたりの滞在時間 | 合計再生時間 (全8シーン) | おすすめ用途 |
| :---: | :--- | :---: | :---: | :--- |
| **1.0x（等倍）** | [`hazard_verification_combined.mp4`](./hazard_verification_combined.mp4) | **6.0秒** / シーン | **48.0秒** (0:48) | 高速環境・映像確認用 |
| **0.5x（1/2倍速）** | [`hazard_verification_combined_0.5x.mp4`](./hazard_verification_combined_0.5x.mp4) | **12.0秒** / シーン | **96.0秒** (1:36) | SAM 3.1 単体モード（1.5〜2.5秒/回）での検証 |
| **0.33x（1/3倍速・推奨）** | [`hazard_verification_combined_0.33x.mp4`](./hazard_verification_combined_0.33x.mp4) | **18.0秒** / シーン | **144.0秒** (2:24) | **標準検証（Webアプリのデフォルト選択）** |
| **0.25x（1/4倍速）** | [`hazard_verification_combined_0.25x.mp4`](./hazard_verification_combined_0.25x.mp4) | **24.0秒** / シーン | **192.0秒** (3:12) | SAM 3.1 + Muse ハイブリッド検証・スマホカメラ越し撮影検証 |
| **0.2x（1/5倍速）** | [`hazard_verification_combined_0.2x.mp4`](./hazard_verification_combined_0.2x.mp4) | **30.0秒** / シーン | **240.0秒** (4:00) | 通信遅延が大きい環境や、1シーンずつじっくり複数回判定させたい場合 |

---

## 3. 個別保存した検証用動画（`individual/`）

すべて **1280×720 (16:9), 25fps, H.264 MP4 (`yuv420p`)** に正規化済み（各6.0秒）。

| # | ファイル名 | 時間区間 (結合動画内) | カテゴリ / 検知対象 | シーン詳細 | 出典・ライセンス |
| :---: | :--- | :---: | :--- | :--- | :--- |
| 1 | [`individual/01_snake_fallen_leaves_tree.mp4`](./individual/01_snake_fallen_leaves_tree.mp4) | `00:00 – 00:06` | `snake`（落葉に隠れている蛇①） | 木の根元に積もった枯れ葉・落葉に紛れて這う蛇（保護色カモフラージュ） | Pexels `11822499` (Ahila devi Manoharan, Pexels License) |
| 2 | [`individual/02_snake_fallen_leaves_closeup.mp4`](./individual/02_snake_fallen_leaves_closeup.mp4) | `00:06 – 00:12` | `snake`（落葉に隠れている蛇②） | 枯れ葉と枝の間に潜み、中央で鎌首をもたげる蛇 | Pexels `11822448` (Ahila devi Manoharan, Pexels License) |
| 3 | [`individual/03_snake_fallen_leaves_viper.mp4`](./individual/03_snake_fallen_leaves_viper.mp4) | `00:12 – 00:18` | `snake`（落葉に隠れている毒蛇③） | 林床の枯れ葉の上に潜むヨーロッパクサリヘビ (*Vipera berus*) | Wikimedia Commons (`Петрозаводск, парк Безымянный Ручей, гадюка.webm`, CC BY-SA 4.0) |
| 4 | [`individual/04_snake_mountain_rattlesnake.mp4`](./individual/04_snake_mountain_rattlesnake.mp4) | `00:18 – 00:24` | `snake`（山の中に隠れている蛇①） | 山林の倒木・枝・落ち葉の間に潜むシンリンガラガラヘビ (*Crotalus horridus*) | Wikimedia Commons (`Timber rattlesnake (Crotalus horridus) in Pennsylvania.webm`, CC BY 2.0) |
| 5 | [`individual/05_snake_mountain_rockwall.mp4`](./individual/05_snake_mountain_rockwall.mp4) | `00:24 – 00:30` | `snake`（山の中に隠れている蛇②） | 山中の苔むした岩壁と草の間を移動するアオダイショウ (*Elaphe climacophora*) | Wikimedia Commons (`Elaphe climacophora - Japanese rat snake - 2015 10 4.webm`, CC BY 4.0) |
| 6 | [`individual/06_boar_mountain_trail.mp4`](./individual/06_boar_mountain_trail.mp4) | `00:30 – 00:36` | `boar`（山の中の猪①） | 落ち葉が敷き詰められた山道を歩く野生イノシシ (*Sus scrofa*) の群れ | Wikimedia Commons (`Sus scrofa-wild boars-Bulgaria-4 VP8.webm`, Vitosha Nature Park, CC BY-SA 4.0) |
| 7 | [`individual/07_boar_forest_encounter.mp4`](./individual/07_boar_forest_encounter.mp4) | `00:36 – 00:42` | `boar`（山の中の猪②） | 森林の道で正面から鉢合わせし、脇のシダの茂みへ走り去る野生のイノシシ | Wikimedia Commons (`Wild boar, Dordogne (1).webm`, CC BY-SA 4.0) |
| 8 | [`individual/08_bear_mountain_trail.mp4`](./individual/08_bear_mountain_trail.mp4) | `00:42 – 00:48` | `bear`（山の中の熊） | 登山道脇の茂みから現れる野生のアメリカグマ (*Ursus americanus*) | Wikimedia Commons (`Black bear - trail camera.webm`, CC BY-SA 2.0) |

---

## 4. Trail Sentinel アプリ側の配置場所

- `trail-sentinel/webapp/videos/hero_how_it_works.mp4` — トップ画面（スタンバイカード内）の「このように動きます」プレビュー動画として自動再生
- `trail-sentinel/webapp/videos/hazard_verification_combined.mp4` — トップ画面の「検証動画でスキャン」ボタンから直接AIリアルタイムスキャンを実行可能
- `trail-sentinel/eval/data/verification_videos/` — 個別動画8本 (`01`〜`08`)・結合動画・デモ動画の保存ディレクトリ
