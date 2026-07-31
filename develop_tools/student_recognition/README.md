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
10 plain portraits across 72 identities. Per-image card indices support both
the seven-card and eight-card layouts without inventing a card in an empty grid
slot. Each screenshot is held out as one complete cross-validation fold, so its
augmented variants never enter that fold's encoder training set or prototype
gallery. After thresholds and verified identities are selected from the grouped
folds, the deliverable encoder is trained once more with all labelled
screenshots. That final target-domain fit repeats the real target portraits
three times for 105 epochs; the exported gallery still contains at most three
distinct source prototypes per student and does not store augmented duplicates.

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

Low-confidence identities are rejected by both cosine similarity and the
top-one/top-two margin. Add current-UI labels and recalibrate those thresholds
before marking additional students as verified.

The training catalog is always loaded from `STATIC_DEFAULT_CONFIG`, not the
generated and ignored `config/static.json`. It contains 265 unique students and
only the `CN_name`, `Global_name` and `JP_name` aliases; server implementation
flags are no longer part of the catalog. Affection eligibility is a click gate
only: eligible and plain crops train the same identity encoder, but a plain
portrait can never select a lesson card by itself.

`training_data.py` validates every source checksum and exposes the historical
and montage portraits to the training script. Loading it does not augment data,
write model files or start training.
