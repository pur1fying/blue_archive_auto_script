# YOLOX + MobileNetV3 + Wikiru270 production bundle

This bundle freezes the previously promoted YOLOX-Nano lesson locator and
replaces only the MobileNetV3-Small identity encoder and prototype gallery.
The selected seed is `20260801`; the gallery contains 270 identities and 690
prototypes. The 177 history, 270 Wikiru, 265 roster and 81 labelled lesson
training-source replays are complete, as are 71 pink clicks and 10 gray blocks.

`independent_v1` was excluded from training, prototypes, retries and seed
selection. Its post-training regression result is 71/83 identity Top-1,
82/83 eligibility and 62/70 pink clicks. This is lower than the pre-Wikiru
combined baseline and was reported but did not block promotion under the chosen
release policy. See the root `combined_top1_report.json` for all 83 rows.
