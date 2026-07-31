# Student recognition development tools

Runtime inference only depends on the project's existing OpenCV and NumPy
packages. PyTorch, torchvision and ONNX are development-only dependencies.

From the repository root:

```powershell
python -m venv .training-venv
.\.training-venv\Scripts\python.exe -m pip install -r develop_tools/student_recognition/requirements-training.txt
.\.training-venv\Scripts\python.exe develop_tools/student_recognition/train_student_models.py all
```

The locator annotations describe the three checked-in new-UI screenshots.
Only identities that passed a strict Git-history template cross-check are
labelled. `new_ui_2.png` is held out as one complete validation group, so its
augmented variants never enter training or the prototype gallery.

The encoder seed set is reconstructed from the three Git revisions documented
by `extract_historical_templates.py`, deduplicated by blob hash, and never
loaded by the normal application runtime. Historical seeds are not
automatically considered verified: `student_encoder.json` explicitly lists
the target-domain verified stable IDs that may trigger a click.

Low-confidence identities are rejected by both cosine similarity and the
top-one/top-two margin. Add current-UI labels and recalibrate those thresholds
before marking additional students as verified.
