# YOLOX-Nano lesson locator candidate

These two files are the promoted locator candidate evaluated in
`../../yolox_locator_experiment_report.json`. The same hashes are installed in
`src/models/student_recognition/` on this branch, so the game loads YOLOX
directly while keeping the existing encoder and gallery.

The candidate was trained only from the five `new_ui` fixtures. The five
`lesson_independent_v1` screenshots were read once for the committed comparison
report and were never training or threshold-selection inputs.
