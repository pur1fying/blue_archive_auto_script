"""YOLOX-Nano experiment for lesson cards and avatar eligibility."""

import os

import torch.nn as nn

from yolox.exp import Exp as BaseExp


class Exp(BaseExp):
    def __init__(self):
        super().__init__()
        self.num_classes = 3
        self.depth = 0.33
        self.width = 0.25
        self.input_size = (384, 640)
        self.test_size = (384, 640)
        self.multiscale_range = 0
        self.random_size = (12, 12)
        self.data_dir = os.environ.get("BAAS_YOLOX_DATASET")
        if not self.data_dir:
            raise RuntimeError("BAAS_YOLOX_DATASET must point to the generated COCO dataset")
        self.output_dir = os.environ.get("BAAS_YOLOX_OUTPUT", self.output_dir)
        self.train_ann = "instances_train2017.json"
        self.val_ann = "instances_val2017.json"
        self.data_num_workers = 0
        self.max_epoch = 80
        self.warmup_epochs = 5
        self.no_aug_epochs = 0
        self.eval_interval = 10
        self.print_interval = 20
        self.save_history_ckpt = False
        self.mosaic_prob = 0.0
        self.mixup_prob = 0.0
        self.enable_mixup = False
        self.flip_prob = 0.0
        self.hsv_prob = 0.5
        self.degrees = 0.0
        self.translate = 0.0
        self.shear = 0.0
        self.test_conf = 0.05
        self.nmsthre = 0.50
        self.seed = 20260731
        self.exp_name = "baas_yolox_nano_lesson_locator"

    def get_model(self, sublinear=False):
        from yolox.models import YOLOX, YOLOPAFPN, YOLOXHead

        def init_yolo(module):
            for child in module.modules():
                if isinstance(child, nn.BatchNorm2d):
                    child.eps = 1e-3
                    child.momentum = 0.03

        if getattr(self, "model", None) is None:
            in_channels = [256, 512, 1024]
            backbone = YOLOPAFPN(
                self.depth,
                self.width,
                in_channels=in_channels,
                act=self.act,
                depthwise=True,
            )
            head = YOLOXHead(
                self.num_classes,
                self.width,
                in_channels=in_channels,
                act=self.act,
                depthwise=True,
            )
            self.model = YOLOX(backbone, head)
        self.model.apply(init_yolo)
        self.model.head.initialize_biases(1e-2)
        return self.model

    def get_eval_dataset(self, **kwargs):
        # YOLOX removes these fields to save memory, while pycocotools 2.0.10
        # expects ``info`` to exist again when constructing result datasets.
        dataset = super().get_eval_dataset(**kwargs)
        dataset.coco.dataset.setdefault("info", {"description": "BAAS YOLOX evaluation"})
        dataset.coco.dataset.setdefault("licenses", [])
        return dataset

    def eval(self, model, evaluator, is_distributed, half=False, return_outputs=False):
        # The optional C++ fast evaluator attempts a just-in-time build under
        # the user's profile on Windows.  Standard pycocotools is deterministic
        # and sufficient for this five-image development experiment.
        import yolox.layers

        if hasattr(yolox.layers, "COCOeval_opt"):
            delattr(yolox.layers, "COCOeval_opt")
        return super().eval(model, evaluator, is_distributed, half, return_outputs)
