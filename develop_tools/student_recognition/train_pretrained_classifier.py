"""Train the mature torchvision MobileNetV3-Small identity experiment."""

import argparse
import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
PRODUCTION_MODEL_DIR = ROOT / "src" / "models" / "student_recognition"
DEFAULT_OUTPUT = ROOT / ".training-runs" / "student_recognition" / "pretrained_classifier"


def _pretrained_trainer(training, frozen_backbone_epochs: int):
    import torch
    from torch.nn import functional as F
    from torch.utils.data import DataLoader

    from develop_tools.student_recognition.models import (
        PretrainedMobileNetV3StudentEncoder,
        StudentEncoderTrainer,
    )

    def train(
        templates,
        epochs: int,
        label: str,
        initial_encoder_state=None,
        seed: int = training.SEED,
        checkpoint_path=None,
    ):
        training.seed_everything(seed)
        names = sorted({name for name, _, _ in templates})
        label_to_index = {name: index for index, name in enumerate(names)}
        dataset = training.IdentityBalancedStudentDataset(templates, label_to_index)
        loader = DataLoader(dataset, batch_size=64, shuffle=True, num_workers=0)
        device = training.training_device()
        model = StudentEncoderTrainer(
            len(names),
            encoder=PretrainedMobileNetV3StudentEncoder(),
        ).to(device)
        if initial_encoder_state is not None:
            model.encoder.load_state_dict(initial_encoder_state)
        optimizer = torch.optim.AdamW(
            [
                {"params": model.encoder.features.parameters(), "lr": 2e-4},
                {"params": model.encoder.projection.parameters(), "lr": 2e-3},
                {"params": model.classifier.parameters(), "lr": 2e-3},
            ],
            weight_decay=1e-4,
        )
        start_epoch = 0
        if checkpoint_path is not None and checkpoint_path.exists():
            checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=True)
            model.load_state_dict(checkpoint["model"])
            optimizer.load_state_dict(checkpoint["optimizer"])
            start_epoch = int(checkpoint["epoch"]) + 1
            print(f"encoder {label} resume_epoch={start_epoch:03d}")
        freeze_epochs = frozen_backbone_epochs if initial_encoder_state is None else 0
        model.train()
        for epoch in range(start_epoch, epochs):
            backbone_trainable = epoch >= freeze_epochs
            for parameter in model.encoder.features.parameters():
                parameter.requires_grad = backbone_trainable
            model.encoder.features.train(backbone_trainable)
            running_loss = 0.0
            for views, labels in loader:
                views = views.to(device)
                labels = labels.to(device)
                batch_size = len(labels)
                images = views.reshape(batch_size * 2, 3, 96, 96)
                expanded_labels = labels.repeat_interleave(2)
                optimizer.zero_grad()
                embeddings, logits = model(images)
                classification_loss = F.cross_entropy(logits, expanded_labels)
                contrastive_loss = training.supervised_contrastive_loss(
                    embeddings,
                    expanded_labels,
                )
                loss = classification_loss + 0.20 * contrastive_loss
                loss.backward()
                optimizer.step()
                running_loss += float(loss)
            if epoch % 5 == 0 or epoch == epochs - 1:
                print(
                    f"encoder {label} epoch={epoch:03d} "
                    f"loss={running_loss / len(loader):.5f}"
                )
                if checkpoint_path is not None:
                    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
                    torch.save(
                        {
                            "epoch": epoch,
                            "model": model.state_dict(),
                            "optimizer": optimizer.state_dict(),
                        },
                        checkpoint_path,
                    )
        return model.encoder.to("cpu").eval(), names

    return train


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--seed", type=int, default=20260731)
    parser.add_argument("--pretrain-epochs", type=int, default=100)
    parser.add_argument("--frozen-backbone-epochs", type=int, default=20)
    parser.add_argument("--fold-epochs", type=int, default=35)
    parser.add_argument("--final-epochs", type=int, default=80)
    args = parser.parse_args()

    # Import after argument parsing so --help does not initialize PyTorch.
    from develop_tools.student_recognition import train_student_models as training

    training._train_student_encoder = _pretrained_trainer(
        training,
        args.frozen_backbone_epochs,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name in ("lesson_locator.onnx", "lesson_locator.json"):
        shutil.copy2(PRODUCTION_MODEL_DIR / name, args.output_dir / name)
    diagnostics = training.train_encoder(
        args.output_dir,
        epochs=args.fold_epochs,
        pretrain_epochs=args.pretrain_epochs,
        final_epochs=args.final_epochs,
        seed=args.seed,
    )
    diagnostics["metadata"].update(
        {
            "architecture": "torchvision-MobileNetV3-Small-ImageNet1K-V1",
            "backbone_pretrained": True,
            "seed_pretrain_frozen_backbone_epochs": args.frozen_backbone_epochs,
        }
    )
    (args.output_dir / "student_encoder.json").write_text(
        json.dumps(diagnostics["metadata"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    report = {
        "version": 1,
        "classification": "training_domain_diagnostic_not_independent_validation",
        "architecture": "torchvision-MobileNetV3-Small-ImageNet1K-V1",
        "seed": args.seed,
        "pretrain_epochs": args.pretrain_epochs,
        "frozen_backbone_epochs": args.frozen_backbone_epochs,
        "fold_epochs": args.fold_epochs,
        "final_epochs": args.final_epochs,
        "independent_comparison_data_included": False,
        "metadata": diagnostics["metadata"],
    }
    (args.output_dir / "pretrained_classifier_training_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
