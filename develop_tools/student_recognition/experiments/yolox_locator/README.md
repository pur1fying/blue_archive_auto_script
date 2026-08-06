# YOLOX-Nano lesson locator candidate

These two files are the promoted locator candidate evaluated in
`../../yolox_locator_experiment_report.json`. They are not automatically loaded
while the production baseline remains locked. To test this branch in the game,
copy `lesson_locator.onnx` and `lesson_locator.json` to
`src/models/student_recognition/`; keep the existing encoder and gallery.

The candidate was trained only from the five `new_ui` fixtures. The five
`lesson_independent_v1` screenshots were read once for the committed comparison
report and were never training or threshold-selection inputs.
