# Student recognition development tools

Runtime inference only depends on the project's existing OpenCV and NumPy
packages. PyTorch, torchvision and ONNX are development-only dependencies.

From the repository root:

```powershell
python -m venv .training-venv
.\.training-venv\Scripts\python.exe -m pip install -r develop_tools/student_recognition/requirements-training.txt
.\.training-venv\Scripts\python.exe develop_tools/student_recognition/train_student_models.py all
```

The locator annotations describe five checked-in new-UI screenshots and contain
all 81 manually labelled avatar instances: 71 affection-eligible portraits and
10 plain portraits across 74 identities. Per-image card indices support both
the seven-card and eight-card layouts without inventing a card in an empty grid
slot. Each screenshot is held out as one complete cross-validation fold, so its
augmented variants never enter that fold's encoder training set or prototype
gallery. The grouped result is a diagnostic rather than an independent external
validation claim. The deliverable encoder is trained once more with all labelled
screenshots, using identity-balanced sampling: every one of the 265 identities
contributes three augmented draws per epoch regardless of raw source count. The
exported gallery contains at most three distinct source prototypes per student.

The encoder seed library is checked in under `data/` and is never loaded by the
normal application runtime. `historical_portraits/` contains 177 distinct Git
blobs across 122 labels; `extract_historical_templates.py` is the explicit
maintenance tool that can rebuild that directory from full Git history. Model
training reads the committed files and does not query Git history itself.

`roster_montages/` contains the three English, three Chinese and three Japanese
roster images plus a position/name manifest. The English images contribute one
selected portrait for each of the 265 catalog identities. The Chinese and
Japanese images are retained as auditable alias evidence, not duplicated as
training pixels. Hoshino (Battle) and Shun (Swimsuit) each have two illustrations
in the montage; their first form is selected and the second form is explicitly
excluded in the manifest.

Runtime selection ranks all 265 identities globally. A pink portrait whose
Top-1 name matches the configured target is selectable at cosine similarity
0.60 or above. Top-1/Top-2 margin and source-support status are logged for
diagnostics but are not click gates. Plain/gray portraits are recognized and
reported but can never trigger a lesson-card click.

The training catalog is always loaded from `STATIC_DEFAULT_CONFIG`, not the
generated and ignored `config/static.json`. It contains 265 unique students and
only the `CN_name`, `Global_name` and `JP_name` aliases; server implementation
flags are no longer part of the catalog. Affection eligibility is a click gate
only: eligible and plain crops train the same identity encoder, but a plain
portrait can never select a lesson card by itself.

`training_data.py` validates every source checksum and exposes the historical
and montage portraits to the training script. Loading it does not augment data,
write model files or start training.

## Sealed independent baseline

`develop_tools/test/fixtures/lesson_independent_v1/` contains five additional
screenshots that are deliberately excluded from `lesson_locator_annotations.json`
and every training loader. Their complete user-confirmed identity and
pink/plain ground truth is stored in `independent_test_annotations_v1.json`.
The recorded boxes are the unchanged production locator's pre-annotation crop
regions; identity and eligibility are the independently confirmed truth.

Run the read-only model evaluation with:

```powershell
.\.venv\Scripts\python.exe develop_tools/student_recognition/evaluate_independent_test.py
```

It writes `independent_test_report_v1.json`, the one-time pre-training baseline
for the production model that existed before these five screenshots were used
for any model change. The baseline is 66/83 identity Top-1, 81/83 eligibility
classification and 57/70 correct pink-target card selections. It is separate
from `validation_report.json` and must never be merged into the earlier
training-fixture replay or its 65-student success list.

If these screenshots are later added to training, preserve this report as the
historical pre-training result. From that point onward the screenshots are
training fixtures, not an independent test set; a new sealed screenshot set is
required for another independent post-training claim.

Training writes candidates under `.training-runs/student_recognition/`. The
production ONNX files and gallery are replaced only after OpenCV replay, click,
gray-blocking, scaling, CPU and resource-size checks all pass. The committed
`validation_report.json` lists all 65 students and 71 pink instances that pass
the five-fixture click test, plus all 10 blocked gray instances. Those checks are
training-fixture replay and must not be described as independent validation of
all 265 students.

## YOLOX locator experiment

The `codex/student-recognition-yolox-locator` branch uses the official
Apache-2.0 YOLOX-Nano implementation at the commit recorded in
`yolox_attribution.json`. The external source checkout and downloaded COCO
checkpoint stay under ignored `.training-runs/`; they are not vendored and are
not runtime dependencies. The committed candidate ONNX and metadata live under
`experiments/yolox_locator/`.

Generate the isolated COCO dataset and train from the repository root after
cloning the recorded YOLOX revision into `.training-runs/third_party/YOLOX`:

```powershell
.\.training-venv\Scripts\python.exe -m pip install -r develop_tools/student_recognition/requirements-yolox.txt
.\.training-venv\Scripts\python.exe develop_tools/student_recognition/export_yolox_lesson_dataset.py
```

The exporter accepts only `new_ui_1.png` through `new_ui_5.png`: 39 non-empty
cards and 81 avatars. It cannot enumerate the `lesson_independent_v1` directory.
The candidate uses three mutually exclusive classes (card, pink avatar and gray
avatar); avatar classes share a class-agnostic NMS pass because one portrait
cannot be both pink and gray.

`yolox_locator_experiment_report.json` is the frozen comparison report. Against
the untouched production baseline it detects 40/40 independent cards and 83/83
avatars, improves identity crops from 66 to 67 correct, improves eligibility
from 81 to 82 correct, improves pink-target clicks from 57 to 58, and reduces
gray-target clicks from one to zero. This comparison is reporting-only: the
sealed screenshots were not used for training, threshold tuning or model
selection. The passing locator is promoted to `src/models/student_recognition/`
on this branch, so source and packaged runs load YOLOX directly; the identity
encoder and gallery remain unchanged.
