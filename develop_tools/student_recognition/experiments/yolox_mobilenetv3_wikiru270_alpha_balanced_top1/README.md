# YOLOX + Alpha-aware MobileNetV3 Wikiru270 bundle

This is the promoted seed `20260731` candidate. The YOLOX-Nano locator is
byte-identical to the pre-training production locator. Only the MobileNetV3
identity encoder, 270-identity gallery and encoder metadata were replaced.

Training used 177 user-audited Git-history portraits, 270 Alpha-preserving
Wikiru portraits, 265 roster portraits and 81 labelled lesson portraits. The
identity-balanced sampler visits every raw image while assigning six draws to
every identity per epoch. The gallery uses up to three source centroids per
identity.

The five `independent_v1` screenshots were excluded from weights, prototypes,
gallery/seed selection and augmentation. The promoted result records 83/83
identity Top-1, 82/83 eligibility and 70/70 pink-target clicks. The sole
remaining error is the frozen locator classifying the gray `Sena (Casual)`
portrait as pink; it was already present in the rollback baseline.

See `../../combined_top1_alpha_balanced_report.json` for all 83 predictions and
the 270-student evidence classification, and
`../../wikiru270_alpha_balanced_training_report.json` for training inputs,
hashes, sampling, grouped folds, replay and promotion gates.
