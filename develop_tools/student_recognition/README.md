# Student recognition development tools

Runtime inference only depends on the project's existing OpenCV and NumPy
packages. PyTorch, torchvision and ONNX are development-only dependencies.

From the repository root:

```powershell
python -m venv .training-venv
.\.training-venv\Scripts\python.exe -m pip install -r develop_tools/student_recognition/requirements-training.txt
.\.training-venv\Scripts\python.exe develop_tools/student_recognition/train_student_models.py all
```

The locator annotations describe the three checked-in new-UI screenshots and
contain all 47 manually labelled avatar instances. Each screenshot is held out
as one complete cross-validation fold, so its augmented variants never enter
that fold's training set or prototype gallery. After thresholds and verified
identities are selected from the grouped folds, the deliverable encoder is
trained once more with all labelled screenshots.

The encoder seed set is reconstructed from the three Git revisions documented
by `extract_historical_templates.py`, deduplicated by blob hash, and never
loaded by the normal application runtime. Historical seeds are not
automatically considered verified: `student_encoder.json` explicitly separates
independently validated `verified_student_ids` from single-source
`prototype_only_student_ids`. Only the verified set may trigger a click.

Low-confidence identities are rejected by both cosine similarity and the
top-one/top-two margin. Add current-UI labels and recalibrate those thresholds
before marking additional students as verified.
