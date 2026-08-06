# YOLOX + MobileNetV3 Top-1 组合验收报告

## 结论

- 训练回放：81/81 身份，71/71 粉框点击，10/10 灰框阻止。
- 冻结回归集 independent_v1：71/83 身份，82/83 粉灰，62/70 粉框点击。
- 270人证据分类：correct 55，error 9，uncertain 206。
- 当前生产图库覆盖全部270人，所有配置身份均参与全局Top-1。
- 本报告对应训练动作：已执行；身份分数和分差只用于诊断。

## 模块架构与来源

| 环节 | 来源 |
|---|---|
| 日程定位 | 官方 YOLOX-Nano；项目自定义三类数据、OpenCV解码、NMS和卡片归属 |
| 学生编码 | 官方 torchvision MobileNetV3-Small/ImageNet权重；项目自定义128维投影头和训练损失 |
| 身份判断 | 项目自定义270人原型图库与全局余弦Top-1；配置名册270人 |
| 点击业务 | 项目自定义粉框、卡片可用、优先级、动态点击和回退逻辑 |

## independent_v1 身份错误

| 图片 | 位置 | 正确身份 | Top-1 | 分数 | 分差 |
|---|---:|---|---|---:|---:|
| MuMu-20260731-235301-451.png | 1-2 | Shokuhou Misaki | Yoshimi | 0.717 | 0.028 |
| MuMu-20260731-235301-451.png | 7-1 | Kotori (Cheer Squad) | Yoshimi (Band) | 0.635 | 0.005 |
| MuMu-20260731-235521-485.png | 1-1 | Mimori (Swimsuit) | Mimori | 0.682 | 0.089 |
| MuMu-20260731-235521-485.png | 5-1 | Kanna (Swimsuit) | Kanna | 0.809 | 0.111 |
| MuMu-20260731-235521-485.png | 5-2 | Shokuhou Misaki | Yoshimi | 0.756 | 0.101 |
| MuMu-20260731-235521-485.png | 6-1 | Aru | Hanako (Swimsuit) | 0.593 | 0.041 |
| MuMu-20260731-235327-036.png | 2-2 | Aru | Hanako (Swimsuit) | 0.626 | 0.091 |
| MuMu-20260731-235327-036.png | 7-1 | Mimori (Swimsuit) | Mimori | 0.707 | 0.095 |
| MuMu-20260731-235327-036.png | 8-2 | Marina | Marina (Qipao) | 0.645 | 0.011 |
| MuMu-20260801-074740-652.png | 2-2 | Nozomi | Hikari | 0.804 | 0.067 |
| MuMu-20260801-074740-652.png | 6-2 | Shokuhou Misaki | Yoshimi | 0.782 | 0.165 |
| MuMu-20260801-074754-624.png | 8-2 | Neru | Neru (School) | 0.725 | 0.048 |

## independent_v1 粉灰与点击错误

| 图片 | 位置 | 身份 | 真实粉灰 | 预测粉灰 | 目标点击卡片 |
|---|---:|---|---|---|---:|
| MuMu-20260731-235327-036.png | 7-2 | Sena (Casual) | 灰 | 粉 | 6 |
| MuMu-20260731-235301-451.png | 1-2 | Shokuhou Misaki | 粉 | 粉 | None |
| MuMu-20260731-235301-451.png | 7-1 | Kotori (Cheer Squad) | 粉 | 粉 | None |
| MuMu-20260731-235521-485.png | 5-2 | Shokuhou Misaki | 粉 | 粉 | None |
| MuMu-20260731-235521-485.png | 6-1 | Aru | 粉 | 粉 | None |
| MuMu-20260731-235327-036.png | 2-2 | Aru | 粉 | 粉 | None |
| MuMu-20260801-074740-652.png | 2-2 | Nozomi | 粉 | 粉 | None |
| MuMu-20260801-074740-652.png | 6-2 | Shokuhou Misaki | 粉 | 粉 | None |
| MuMu-20260801-074754-624.png | 8-2 | Neru | 粉 | 粉 | None |

## 相对Wikiru270重训前模型

- 身份正确：75 → 71 (-4)。
- 粉框点击：65 → 62 (-3)。
- 灰框错误点击：1 → 1 (+0)。
- 83个实例中有11个预测或业务结果发生变化；完整逐实例前后结果保存在JSON报告中。

## 270人点击证据分类

这些状态只描述测试证据，不会阻止运行时对任何学生进行Top-1选择。

### Correct（55）

`Ako (Dress)`, `Asuna (Bunny)`, `Asuna (School)`, `Ayane`, `Cherino`, `Chinatsu`, `Chinatsu (Hot Spring)`, `Chise`, `Fuuka (New Year)`, `Hanae`, `Hanae (Christmas)`, `Hanako`, `Haruna (New Year)`, `Hibiki`, `Hibiki (Cheer Squad)`, `Hifumi`, `Ibuki`, `Ichika`, `Iori`, `Izumi (Swimsuit)`, `Izuna (Swimsuit)`, `Junko (New Year)`, `Karin (School)`, `Kayoko (New Year)`, `Kirino`, `Kirino (Swimsuit)`, `Kotama`, `Kotama (Camp)`, `Koyuki`, `Maki`, `Mari (Track)`, `Mashiro (Swimsuit)`, `Michiru`, `Midori`, `Mika`, `Mimori`, `Miyako`, `Miyu`, `Nagisa`, `Neru (School)`, `Noa`, `Nonomi`, `Pina`, `Sakurako`, `Sakurako (Pop Idol)`, `Saten Ruiko`, `Shiroko`, `Shiroko (Cycling)`, `Shun (Small)`, `Sumire`, `Tsubaki`, `Ui`, `Yuuka`, `Yuzu`, `Yuzu (Maid)`

### Error（9）

`Aru`, `Kanna (Swimsuit)`, `Kotori (Cheer Squad)`, `Marina`, `Mimori (Swimsuit)`, `Neru`, `Nozomi`, `Sena (Casual)`, `Shokuhou Misaki`

### Uncertain（206）

`Airi`, `Airi (Band)`, `Akane`, `Akane (Bunny)`, `Akane (School)`, `Akari`, `Akari (New Year)`, `Ako`, `Aoba`, `Aris`, `Aris (Armed)`, `Aris (Maid)`, `Aru (Dress)`, `Aru (New Year)`, `Asuna`, `Atsuko`, `Atsuko (Swimsuit)`, `Ayane (Swimsuit)`, `Azusa`, `Azusa (Swimsuit)`, `Cherino (Hot Spring)`, `Chiaki`, `Chiaki (Swimsuit)`, `Chihiro`, `Chise (Swimsuit)`, `Eimi`, `Eimi (Armed)`, `Eimi (Swimsuit)`, `Eri`, `Erika`, `Fubuki`, `Fubuki (Swimsuit)`, `Fuuka`, `Fuyu`, `Hanako (Swimsuit)`, `Hare`, `Hare (Camp)`, `Haruka`, `Haruka (Dress)`, `Haruka (New Year)`, `Haruna`, `Haruna (Track)`, `Hasumi`, `Hasumi (Swimsuit)`, `Hasumi (Track)`, `Hatsune Miku`, `Hifumi (Swimsuit)`, `Hikari`, `Himari`, `Himari (Armed)`, `Hina`, `Hina (Dress)`, `Hina (Swimsuit)`, `Hinata`, `Hinata (Swimsuit)`, `Hiyori`, `Hiyori (Swimsuit)`, `Hoshino`, `Hoshino (Battle)`, `Hoshino (Swimsuit)`, `Ibuki (Swimsuit)`, `Ichika (Swimsuit)`, `Iori (Swimsuit)`, `Iroha`, `Iroha (Swimsuit)`, `Izumi`, `Izumi (New Year)`, `Izuna`, `Junko`, `Juri`, `Juri (Part-Timer)`, `Kaede`, `Kaho`, `Kanna`, `Kanoe`, `Karin`, `Karin (Bunny)`, `Kasumi`, `Kayoko`, `Kayoko (Dress)`, `Kazusa`, `Kazusa (Band)`, `Kei`, `Kikyou`, `Kikyou (Swimsuit)`, `Kirara`, `Kisaki`, `Kisaki (Swimsuit)`, `Koharu`, `Koharu (Swimsuit)`, `Kokona`, `Konoka`, `Kotori`, `Koyuki (Pajamas)`, `Kurumi`, `Maki (Camp)`, `Makoto`, `Makoto (Swimsuit)`, `Mari`, `Mari (Pop Idol)`, `Marina (Qipao)`, `Mashiro`, `Megu`, `Meru`, `Michiru (Dress)`, `Midori (Maid)`, `Mika (Swimsuit)`, `Mina`, `Mine`, `Mine (Pop Idol)`, `Minori`, `Misaka Mikoto`, `Misaki`, `Misaki (Swimsuit)`, `Miyako (Swimsuit)`, `Miyo`, `Miyu (Swimsuit)`, `Moe`, `Moe (Swimsuit)`, `Momiji`, `Momoi`, `Momoi (Maid)`, `Mutsuki`, `Mutsuki (Dress)`, `Mutsuki (New Year)`, `Nagisa (Swimsuit)`, `Nagusa`, `Nagusa (Swimsuit)`, `Natsu`, `Natsu (Band)`, `Neru (Bunny)`, `Niko`, `Niya`, `Noa (Pajamas)`, `Nodoka`, `Nodoka (Hot Spring)`, `Nonomi (Swimsuit)`, `Otogi`, `Pina (Guide)`, `Rabu`, `Rei`, `Reijo`, `Reisa`, `Reisa (Magical)`, `Rena`, `Renge`, `Renge (Swimsuit)`, `Rio`, `Rio (Armed)`, `Ritsu`, `Rumi`, `Saki`, `Saki (Swimsuit)`, `Saori`, `Saori (Dress)`, `Saori (Swimsuit)`, `Satsuki`, `Satsuki (Swimsuit)`, `Saya`, `Saya (Casual)`, `Seia`, `Seia (Swimsuit)`, `Sena`, `Serika`, `Serika (New Year)`, `Serika (Swimsuit)`, `Serina`, `Serina (Christmas)`, `Shigure`, `Shigure (Hot Spring)`, `Shimiko`, `Shiroko (Swimsuit)`, `Shiroko Terror`, `Shizuko`, `Shizuko (Swimsuit)`, `Shun`, `Shun (Swimsuit)`, `Subaru`, `Sumire (Part-Timer)`, `Suzumi`, `Suzumi (Magical)`, `Takane`, `Toki`, `Toki (Armed)`, `Toki (Bunny)`, `Tomoe`, `Tomoe (Qipao)`, `Tsubaki (Guide)`, `Tsukuyo`, `Tsukuyo (Dress)`, `Tsurugi`, `Tsurugi (Swimsuit)`, `Ui (Swimsuit)`, `Umika`, `Utaha`, `Utaha (Cheer Squad)`, `Wakamo`, `Wakamo (Swimsuit)`, `Yakumo`, `Yoshimi`, `Yoshimi (Band)`, `Yukari`, `Yukari (Swimsuit)`, `Yuuka (Pajamas)`, `Yuuka (Track)`, `Yuzu (Armed)`

## 训练集覆盖

训练图粉框点击学生（65）：

`Aoba`, `Asuna (Bunny)`, `Asuna (School)`, `Atsuko`, `Atsuko (Swimsuit)`, `Cherino`, `Chihiro`, `Chinatsu (Hot Spring)`, `Chise (Swimsuit)`, `Hanae`, `Hanae (Christmas)`, `Hanako`, `Hanako (Swimsuit)`, `Hare`, `Haruna`, `Hasumi (Track)`, `Hibiki`, `Hina (Dress)`, `Hinata`, `Hinata (Swimsuit)`, `Hoshino (Battle)`, `Ibuki`, `Ichika`, `Iori`, `Iori (Swimsuit)`, `Izumi`, `Izumi (Swimsuit)`, `Izuna`, `Junko`, `Junko (New Year)`, `Kanna`, `Karin (School)`, `Kayoko`, `Kirino`, `Koharu (Swimsuit)`, `Kokona`, `Kotama`, `Kotama (Camp)`, `Meru`, `Midori (Maid)`, `Mimori`, `Miyako`, `Miyu`, `Mutsuki`, `Neru (School)`, `Nonomi (Swimsuit)`, `Pina`, `Rio`, `Saki (Swimsuit)`, `Sakurako (Pop Idol)`, `Saya (Casual)`, `Serika`, `Shiroko Terror`, `Shun (Small)`, `Sumire`, `Suzumi`, `Toki`, `Toki (Bunny)`, `Tsurugi (Swimsuit)`, `Ui`, `Utaha`, `Wakamo`, `Yoshimi (Band)`, `Yuzu`, `Yuzu (Maid)`

训练图仅灰框学生（9）：

`Chiaki`, `Maki (Camp)`, `Marina (Qipao)`, `Megu`, `Noa (Pajamas)`, `Reijo`, `Saki`, `Shigure (Hot Spring)`, `Tsukuyo`

训练回放不是独立验证；即使训练图71/71点击成功，没有独立粉框样本的学生仍归为uncertain。

## 如果未来把 independent_v1 加入训练

高概率改善的当前错误学生：

`Aru`, `Kanna (Swimsuit)`, `Kotori (Cheer Squad)`, `Marina`, `Mimori (Swimsuit)`, `Neru`, `Nozomi`, `Sena (Casual)`, `Shokuhou Misaki`

新增真实日程域覆盖：

`Ako (Dress)`, `Aru`, `Ayane`, `Chinatsu`, `Chise`, `Fuuka (New Year)`, `Haruna (New Year)`, `Hibiki (Cheer Squad)`, `Hifumi`, `Izuna (Swimsuit)`, `Kanna (Swimsuit)`, `Kayoko (New Year)`, `Kirino (Swimsuit)`, `Kotori (Cheer Squad)`, `Koyuki`, `Maki`, `Mari (Track)`, `Marina`, `Mashiro (Swimsuit)`, `Michiru`, `Midori`, `Mika`, `Mimori (Swimsuit)`, `Moe (Swimsuit)`, `Nagisa`, `Neru`, `Noa`, `Nonomi`, `Nozomi`, `Sakurako`, `Saten Ruiko`, `Sena (Casual)`, `Serika (Swimsuit)`, `Shiroko`, `Shiroko (Cycling)`, `Shokuhou Misaki`, `Tsubaki`, `Yuuka`, `Yuuka (Pajamas)`

这些是预期而非实测；加入训练后必须使用新的independent_v2才能确认。
