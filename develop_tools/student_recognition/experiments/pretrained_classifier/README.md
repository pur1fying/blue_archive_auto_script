# Pretrained MobileNetV3-Small classifier candidate

This directory is a complete, directly evaluable model bundle. Only the
encoder, encoder metadata and gallery differ from production; the locator files
are copied unchanged so the generic candidate evaluator can load one directory.

The candidate improves sealed identity Top-1 from 66/83 to 75/83, but reaches
64/70 pink clicks against a predeclared 65/70 promotion threshold. It therefore
remains an experiment and is not copied into `src/models/student_recognition/`.
See `../../pretrained_classifier_experiment_report.json` for every prediction
and `pretrained_classifier_training_report.json` for training-domain diagnostics.
