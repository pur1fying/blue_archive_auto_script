import torch
from torch import nn
from torch.nn import functional as F
from torchvision.models import mobilenet_v2


class ConvBlock(nn.Sequential):
    def __init__(self, input_channels: int, output_channels: int):
        super().__init__(
            nn.Conv2d(input_channels, output_channels, 3, padding=1, bias=False),
            nn.BatchNorm2d(output_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(output_channels, output_channels, 3, padding=1, bias=False),
            nn.BatchNorm2d(output_channels),
            nn.ReLU(inplace=True),
        )


class LessonSegmentationNet(nn.Module):
    """Small four-class U-Net used only for the lesson scene."""

    def __init__(self, class_count: int = 4):
        super().__init__()
        self.encoder1 = ConvBlock(3, 8)
        self.encoder2 = ConvBlock(8, 16)
        self.bottleneck = ConvBlock(16, 32)
        self.pool = nn.MaxPool2d(2)
        self.up2 = nn.ConvTranspose2d(32, 16, 2, stride=2)
        self.decoder2 = ConvBlock(32, 16)
        self.up1 = nn.ConvTranspose2d(16, 8, 2, stride=2)
        self.decoder1 = ConvBlock(16, 8)
        self.output = nn.Conv2d(8, class_count, 1)

    def forward(self, image):
        feature1 = self.encoder1(image)
        feature2 = self.encoder2(self.pool(feature1))
        bottleneck = self.bottleneck(self.pool(feature2))
        decoded2 = self.decoder2(torch.cat((self.up2(bottleneck), feature2), dim=1))
        decoded1 = self.decoder1(torch.cat((self.up1(decoded2), feature1), dim=1))
        return self.output(decoded1)


class StudentEncoder(nn.Module):
    def __init__(self, embedding_size: int = 128):
        super().__init__()
        backbone = mobilenet_v2(weights=None, width_mult=0.5)
        self.features = backbone.features
        self.projection = nn.Linear(backbone.last_channel, embedding_size)

    def forward(self, image):
        feature = self.features(image)
        feature = F.adaptive_avg_pool2d(feature, 1).flatten(1)
        return F.normalize(self.projection(feature), dim=1)


class StudentEncoderTrainer(nn.Module):
    def __init__(self, class_count: int, embedding_size: int = 128):
        super().__init__()
        self.encoder = StudentEncoder(embedding_size)
        self.classifier = nn.Linear(embedding_size, class_count)

    def forward(self, image):
        embedding = self.encoder(image)
        return embedding, self.classifier(embedding) * 12.0
