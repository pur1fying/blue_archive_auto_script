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

The encoder seed set is reconstructed from the three Git revisions documented
by `extract_historical_templates.py`, deduplicated by blob hash, and never
loaded by the normal application runtime. Historical seeds are not
automatically considered verified: `student_encoder.json` explicitly separates
independently validated `verified_student_ids` from single-source
`prototype_only_student_ids`. Only the verified set may trigger a click.

Low-confidence identities are rejected by both cosine similarity and the
top-one/top-two margin. Add current-UI labels and recalibrate those thresholds
before marking additional students as verified.

The training catalog is always loaded from `STATIC_DEFAULT_CONFIG`, not the
generated and ignored `config/static.json`. The current target data resolves
against the 204 unique students in that source catalog. Affection eligibility
is a click gate only: eligible and plain crops train the same identity encoder,
but a plain portrait can never select a lesson card by itself.
