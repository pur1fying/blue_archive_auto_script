# YOLOX + MobileNetV3 global Top-1 candidate

This bundle composes the already exported YOLOX-Nano lesson locator with the
already exported torchvision MobileNetV3-Small student encoder and 265-identity
prototype gallery. The two networks are sequential and share no trainable
weights, so no retraining was performed for this first integration pass.

The locator was trained only from the five `new_ui` fixtures. The identity
encoder was trained from the committed 177 historical portraits, 265 selected
English roster portraits and 81 portraits from those same five lesson fixtures.
The five `lesson_independent_v1` screenshots were not included in either model,
the prototype gallery or weight selection.

Runtime identity selection uses every valid global Top-1 result. Cosine score,
Top-1/Top-2 margin and support status are diagnostics only; pink eligibility
and card availability remain click gates. See `combined_top1_report.json` and
`combined_top1_report.md` for the frozen comparison and per-student evidence.
