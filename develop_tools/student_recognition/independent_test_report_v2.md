# independent_v2 正式测试报告

> 状态：`completed`；
> 该集合未进入训练、图库、阈值或模型选择。

## 总结

- 定位：86/86个卡片，182/182个头像。
- 普通状态身份：164/164；selected身份：14/18；总计：178/182。
- 普通状态粉灰：157/164；selected粉灰：18/18；总计：175/182。
- 普通彩框正确卡片：137/137。
- 普通灰框正确阻止：20/27；点击风险：7。
- selected来源卡片阻止：18/18；实际来源卡片点击：0。

## 身份错误（全部位于selected卡片）

| 图片 | 位置 | 真值 | Top-1 | 分数 | 分差 |
|---|---:|---|---|---:|---:|
| MuMu-20260806-231258-968.png | 7-1 | Sumire (Part-Timer) | Shun | 0.639 | 0.008 |
| MuMu-20260806-231304-820.png | 6-2 | Kasumi | Tsukuyo | 0.538 | 0.035 |
| MuMu-20260806-231311-941.png | 4-2 | Ui (Swimsuit) | Ui | 0.710 | 0.044 |
| MuMu-20260806-231317-557.png | 8-1 | Ui (Swimsuit) | Ui | 0.732 | 0.026 |

## 普通灰框误判与点击风险

| 图片 | 位置 | 学生 | 预测粉灰 | 模拟点击卡片 |
|---|---:|---|---|---:|
| MuMu-20260806-231304-820.png | 7-1 | Kirara | 彩框 | 7 |
| MuMu-20260806-231311-941.png | 7-2 | Sena (Casual) | 彩框 | 7 |
| MuMu-20260806-231317-557.png | 1-2 | Kirara | 彩框 | 1 |
| MuMu-20260806-231317-557.png | 4-2 | Serina (Christmas) | 彩框 | 4 |
| MuMu-20260806-231317-557.png | 6-2 | Serika (Swimsuit) | 彩框 | 6 |
| MuMu-20260806-231322-679.png | 4-2 | Yuuka (Pajamas) | 彩框 | 4 |
| MuMu-20260806-231322-679.png | 7-3 | Serina (Christmas) | 彩框 | 7 |

## 全部头像

| 图片 | 位置 | 状态 | 真值 | Top-1 | 身份 | 真值粉灰 | 预测粉灰 | 模拟卡片 |
|---|---:|---|---|---|---|---|---|---:|
| MuMu-20260806-231258-968.png | 1-1 | available | Juri (Part-Timer) | Juri (Part-Timer) | 正确 | 灰框 | 灰框 | - |
| MuMu-20260806-231258-968.png | 1-2 | available | Saya (Casual) | Saya (Casual) | 正确 | 彩框 | 彩框 | 1 |
| MuMu-20260806-231258-968.png | 1-3 | available | Junko | Junko | 正确 | 彩框 | 彩框 | 1 |
| MuMu-20260806-231258-968.png | 2-1 | available | Marina (Qipao) | Marina (Qipao) | 正确 | 灰框 | 灰框 | - |
| MuMu-20260806-231258-968.png | 2-2 | available | Kayoko | Kayoko | 正确 | 彩框 | 彩框 | 2 |
| MuMu-20260806-231258-968.png | 2-3 | available | Himari | Himari | 正确 | 彩框 | 彩框 | 2 |
| MuMu-20260806-231258-968.png | 3-1 | available | Hanae | Hanae | 正确 | 彩框 | 彩框 | 3 |
| MuMu-20260806-231258-968.png | 4-1 | available | Maki (Camp) | Maki (Camp) | 正确 | 灰框 | 灰框 | - |
| MuMu-20260806-231258-968.png | 4-2 | available | Mashiro | Mashiro | 正确 | 彩框 | 彩框 | 4 |
| MuMu-20260806-231258-968.png | 5-1 | available | Mutsuki | Mutsuki | 正确 | 彩框 | 彩框 | 5 |
| MuMu-20260806-231258-968.png | 5-2 | available | Umika | Umika | 正确 | 灰框 | 灰框 | - |
| MuMu-20260806-231258-968.png | 6-1 | available | Kanna (Swimsuit) | Kanna (Swimsuit) | 正确 | 灰框 | 灰框 | - |
| MuMu-20260806-231258-968.png | 6-2 | available | Sakurako (Pop Idol) | Sakurako (Pop Idol) | 正确 | 彩框 | 彩框 | 6 |
| MuMu-20260806-231258-968.png | 6-3 | available | Yukari | Yukari | 正确 | 彩框 | 彩框 | 6 |
| MuMu-20260806-231258-968.png | 7-1 | selected | Sumire (Part-Timer) | Shun | 错误 | 灰框 | 灰框 | - |
| MuMu-20260806-231258-968.png | 7-2 | selected | Aru (Dress) | Aru (Dress) | 正确 | 彩框 | 彩框 | - |
| MuMu-20260806-231258-968.png | 7-3 | selected | Tsurugi | Tsurugi | 正确 | 彩框 | 彩框 | - |
| MuMu-20260806-231304-820.png | 1-1 | available | Moe (Swimsuit) | Moe (Swimsuit) | 正确 | 灰框 | 灰框 | - |
| MuMu-20260806-231304-820.png | 1-2 | available | Iroha | Iroha | 正确 | 彩框 | 彩框 | 1 |
| MuMu-20260806-231304-820.png | 2-1 | available | Sumire | Sumire | 正确 | 彩框 | 彩框 | 2 |
| MuMu-20260806-231304-820.png | 2-2 | available | Saki (Swimsuit) | Saki (Swimsuit) | 正确 | 彩框 | 彩框 | 2 |
| MuMu-20260806-231304-820.png | 3-1 | available | Yoshimi | Yoshimi | 正确 | 彩框 | 彩框 | 3 |
| MuMu-20260806-231304-820.png | 3-2 | available | Ibuki | Ibuki | 正确 | 彩框 | 彩框 | 3 |
| MuMu-20260806-231304-820.png | 3-3 | available | Kayoko (New Year) | Kayoko (New Year) | 正确 | 彩框 | 彩框 | 3 |
| MuMu-20260806-231304-820.png | 4-1 | available | Pina | Pina | 正确 | 彩框 | 彩框 | 4 |
| MuMu-20260806-231304-820.png | 5-1 | available | Aris | Aris | 正确 | 彩框 | 彩框 | 5 |
| MuMu-20260806-231304-820.png | 5-2 | available | Shizuko | Shizuko | 正确 | 彩框 | 彩框 | 5 |
| MuMu-20260806-231304-820.png | 6-1 | selected | Shiroko Terror | Shiroko Terror | 正确 | 彩框 | 彩框 | - |
| MuMu-20260806-231304-820.png | 6-2 | selected | Kasumi | Tsukuyo | 错误 | 彩框 | 彩框 | - |
| MuMu-20260806-231304-820.png | 6-3 | selected | Fubuki | Fubuki | 正确 | 彩框 | 彩框 | - |
| MuMu-20260806-231304-820.png | 7-1 | available | Kirara | Kirara | 正确 | 灰框 | 彩框 | 7 |
| MuMu-20260806-231304-820.png | 7-2 | available | Hoshino (Battle) | Hoshino (Battle) | 正确 | 彩框 | 彩框 | 7 |
| MuMu-20260806-231311-941.png | 1-1 | available | Miyako | Miyako | 正确 | 彩框 | 彩框 | 1 |
| MuMu-20260806-231311-941.png | 1-2 | available | Himari | Himari | 正确 | 彩框 | 彩框 | 1 |
| MuMu-20260806-231311-941.png | 1-3 | available | Fuuka | Fuuka | 正确 | 彩框 | 彩框 | 1 |
| MuMu-20260806-231311-941.png | 2-1 | available | Shiroko | Shiroko | 正确 | 彩框 | 彩框 | 2 |
| MuMu-20260806-231311-941.png | 2-2 | available | Nodoka (Hot Spring) | Nodoka (Hot Spring) | 正确 | 彩框 | 彩框 | 2 |
| MuMu-20260806-231311-941.png | 3-1 | available | Haruna (New Year) | Haruna (New Year) | 正确 | 彩框 | 彩框 | 3 |
| MuMu-20260806-231311-941.png | 3-2 | available | Mutsuki (New Year) | Mutsuki (New Year) | 正确 | 彩框 | 彩框 | 3 |
| MuMu-20260806-231311-941.png | 4-1 | selected | Miyu (Swimsuit) | Miyu (Swimsuit) | 正确 | 彩框 | 彩框 | - |
| MuMu-20260806-231311-941.png | 4-2 | selected | Ui (Swimsuit) | Ui | 错误 | 彩框 | 彩框 | - |
| MuMu-20260806-231311-941.png | 4-3 | selected | Kayoko | Kayoko | 正确 | 彩框 | 彩框 | - |
| MuMu-20260806-231311-941.png | 5-1 | available | Yoshimi | Yoshimi | 正确 | 彩框 | 彩框 | 5 |
| MuMu-20260806-231311-941.png | 5-2 | available | Hifumi (Swimsuit) | Hifumi (Swimsuit) | 正确 | 彩框 | 彩框 | 5 |
| MuMu-20260806-231311-941.png | 6-1 | available | Makoto | Makoto | 正确 | 彩框 | 彩框 | 6 |
| MuMu-20260806-231311-941.png | 6-2 | available | Saten Ruiko | Saten Ruiko | 正确 | 彩框 | 彩框 | 6 |
| MuMu-20260806-231311-941.png | 7-1 | available | Kokona | Kokona | 正确 | 彩框 | 彩框 | 7 |
| MuMu-20260806-231311-941.png | 7-2 | available | Sena (Casual) | Sena (Casual) | 正确 | 灰框 | 彩框 | 7 |
| MuMu-20260806-231311-941.png | 8-1 | available | Tsukuyo | Tsukuyo | 正确 | 灰框 | 灰框 | - |
| MuMu-20260806-231311-941.png | 8-2 | available | Kanna (Swimsuit) | Kanna (Swimsuit) | 正确 | 灰框 | 灰框 | - |
| MuMu-20260806-231317-557.png | 1-1 | available | Neru (Bunny) | Neru (Bunny) | 正确 | 彩框 | 彩框 | 1 |
| MuMu-20260806-231317-557.png | 1-2 | available | Kirara | Kirara | 正确 | 灰框 | 彩框 | 1 |
| MuMu-20260806-231317-557.png | 2-1 | available | Izumi (Swimsuit) | Izumi (Swimsuit) | 正确 | 彩框 | 彩框 | 2 |
| MuMu-20260806-231317-557.png | 2-2 | available | Hatsune Miku | Hatsune Miku | 正确 | 彩框 | 彩框 | 2 |
| MuMu-20260806-231317-557.png | 3-1 | available | Mari (Track) | Mari (Track) | 正确 | 彩框 | 彩框 | 3 |
| MuMu-20260806-231317-557.png | 3-2 | available | Eimi | Eimi | 正确 | 彩框 | 彩框 | 3 |
| MuMu-20260806-231317-557.png | 3-3 | available | Nonomi (Swimsuit) | Nonomi (Swimsuit) | 正确 | 彩框 | 彩框 | 3 |
| MuMu-20260806-231317-557.png | 4-1 | available | Kikyou | Kikyou | 正确 | 彩框 | 彩框 | 4 |
| MuMu-20260806-231317-557.png | 4-2 | available | Serina (Christmas) | Serina (Christmas) | 正确 | 灰框 | 彩框 | 4 |
| MuMu-20260806-231317-557.png | 5-1 | available | Shiroko | Shiroko | 正确 | 彩框 | 彩框 | 5 |
| MuMu-20260806-231317-557.png | 6-1 | available | Makoto | Makoto | 正确 | 彩框 | 彩框 | 6 |
| MuMu-20260806-231317-557.png | 6-2 | available | Serika (Swimsuit) | Serika (Swimsuit) | 正确 | 灰框 | 彩框 | 6 |
| MuMu-20260806-231317-557.png | 7-1 | available | Moe | Moe | 正确 | 彩框 | 彩框 | 7 |
| MuMu-20260806-231317-557.png | 7-2 | available | Shigure (Hot Spring) | Shigure (Hot Spring) | 正确 | 灰框 | 灰框 | - |
| MuMu-20260806-231317-557.png | 8-1 | selected | Ui (Swimsuit) | Ui | 错误 | 彩框 | 彩框 | - |
| MuMu-20260806-231317-557.png | 8-2 | selected | Nodoka | Nodoka | 正确 | 彩框 | 彩框 | - |
| MuMu-20260806-231322-679.png | 1-1 | selected | Kisaki | Kisaki | 正确 | 彩框 | 彩框 | - |
| MuMu-20260806-231322-679.png | 1-2 | selected | Midori (Maid) | Midori (Maid) | 正确 | 彩框 | 彩框 | - |
| MuMu-20260806-231322-679.png | 1-3 | selected | Eimi (Swimsuit) | Eimi (Swimsuit) | 正确 | 彩框 | 彩框 | - |
| MuMu-20260806-231322-679.png | 2-1 | available | Noa | Noa | 正确 | 彩框 | 彩框 | 2 |
| MuMu-20260806-231322-679.png | 2-2 | available | Tsurugi | Tsurugi | 正确 | 彩框 | 彩框 | 2 |
| MuMu-20260806-231322-679.png | 3-1 | available | Chiaki | Chiaki | 正确 | 灰框 | 灰框 | - |
| MuMu-20260806-231322-679.png | 3-2 | available | Azusa (Swimsuit) | Azusa (Swimsuit) | 正确 | 彩框 | 彩框 | 3 |
| MuMu-20260806-231322-679.png | 4-1 | available | Shiroko (Cycling) | Shiroko (Cycling) | 正确 | 彩框 | 彩框 | 4 |
| MuMu-20260806-231322-679.png | 4-2 | available | Yuuka (Pajamas) | Yuuka (Pajamas) | 正确 | 灰框 | 彩框 | 4 |
| MuMu-20260806-231322-679.png | 5-1 | available | Saori (Swimsuit) | Saori (Swimsuit) | 正确 | 彩框 | 彩框 | 5 |
| MuMu-20260806-231322-679.png | 6-1 | available | Akari | Akari | 正确 | 彩框 | 彩框 | 6 |
| MuMu-20260806-231322-679.png | 6-2 | available | Chihiro | Chihiro | 正确 | 彩框 | 彩框 | 6 |
| MuMu-20260806-231322-679.png | 7-1 | available | Mimori | Mimori | 正确 | 彩框 | 彩框 | 7 |
| MuMu-20260806-231322-679.png | 7-2 | available | Himari | Himari | 正确 | 彩框 | 彩框 | 7 |
| MuMu-20260806-231322-679.png | 7-3 | available | Serina (Christmas) | Serina (Christmas) | 正确 | 灰框 | 彩框 | 7 |
| MuMu-20260806-231322-679.png | 8-1 | available | Yoshimi (Band) | Yoshimi (Band) | 正确 | 彩框 | 彩框 | 8 |
| MuMu-20260806-231322-679.png | 8-2 | available | Mari | Mari | 正确 | 彩框 | 彩框 | 8 |
| MuMu-20260806-231327-489.png | 1-1 | available | Haruna | Haruna | 正确 | 彩框 | 彩框 | 1 |
| MuMu-20260806-231327-489.png | 1-2 | available | Tsurugi | Tsurugi | 正确 | 彩框 | 彩框 | 1 |
| MuMu-20260806-231327-489.png | 1-3 | available | Mutsuki | Mutsuki | 正确 | 彩框 | 彩框 | 1 |
| MuMu-20260806-231327-489.png | 2-1 | available | Hatsune Miku | Hatsune Miku | 正确 | 彩框 | 彩框 | 2 |
| MuMu-20260806-231327-489.png | 2-2 | available | Michiru | Michiru | 正确 | 彩框 | 彩框 | 2 |
| MuMu-20260806-231327-489.png | 2-3 | available | Ui | Ui | 正确 | 彩框 | 彩框 | 2 |
| MuMu-20260806-231327-489.png | 3-1 | available | Hibiki | Hibiki | 正确 | 彩框 | 彩框 | 3 |
| MuMu-20260806-231327-489.png | 3-2 | available | Tsubaki | Tsubaki | 正确 | 彩框 | 彩框 | 3 |
| MuMu-20260806-231327-489.png | 3-3 | available | Sumire | Sumire | 正确 | 彩框 | 彩框 | 3 |
| MuMu-20260806-231327-489.png | 4-1 | available | Marina (Qipao) | Marina (Qipao) | 正确 | 灰框 | 灰框 | - |
| MuMu-20260806-231327-489.png | 4-2 | available | Miyako (Swimsuit) | Miyako (Swimsuit) | 正确 | 彩框 | 彩框 | 4 |
| MuMu-20260806-231327-489.png | 5-1 | available | Moe | Moe | 正确 | 彩框 | 彩框 | 5 |
| MuMu-20260806-231327-489.png | 5-2 | available | Nagisa | Nagisa | 正确 | 彩框 | 彩框 | 5 |
| MuMu-20260806-231327-489.png | 6-1 | available | Akane | Akane | 正确 | 彩框 | 彩框 | 6 |
| MuMu-20260806-231327-489.png | 6-2 | available | Chise | Chise | 正确 | 彩框 | 彩框 | 6 |
| MuMu-20260806-231327-489.png | 7-1 | available | Kayoko (Dress) | Kayoko (Dress) | 正确 | 灰框 | 灰框 | - |
| MuMu-20260806-231327-489.png | 8-1 | available | Midori | Midori | 正确 | 彩框 | 彩框 | 8 |
| MuMu-20260806-231332-087.png | 1-1 | available | Chiaki | Chiaki | 正确 | 灰框 | 灰框 | - |
| MuMu-20260806-231332-087.png | 1-2 | available | Noa | Noa | 正确 | 彩框 | 彩框 | 1 |
| MuMu-20260806-231332-087.png | 1-3 | available | Izumi | Izumi | 正确 | 彩框 | 彩框 | 1 |
| MuMu-20260806-231332-087.png | 2-1 | available | Asuna (School) | Asuna (School) | 正确 | 彩框 | 彩框 | 2 |
| MuMu-20260806-231332-087.png | 2-2 | available | Miyako | Miyako | 正确 | 彩框 | 彩框 | 2 |
| MuMu-20260806-231332-087.png | 2-3 | available | Aris (Maid) | Aris (Maid) | 正确 | 彩框 | 彩框 | 2 |
| MuMu-20260806-231332-087.png | 3-1 | available | Marina | Marina | 正确 | 灰框 | 灰框 | - |
| MuMu-20260806-231332-087.png | 4-1 | available | Aoba | Aoba | 正确 | 彩框 | 彩框 | 4 |
| MuMu-20260806-231332-087.png | 4-2 | available | Hatsune Miku | Hatsune Miku | 正确 | 彩框 | 彩框 | 4 |
| MuMu-20260806-231332-087.png | 5-1 | selected | Eimi (Swimsuit) | Eimi (Swimsuit) | 正确 | 彩框 | 彩框 | - |
| MuMu-20260806-231332-087.png | 5-2 | selected | Yuzu (Maid) | Yuzu (Maid) | 正确 | 彩框 | 彩框 | - |
| MuMu-20260806-231332-087.png | 5-3 | selected | Serina | Serina | 正确 | 彩框 | 彩框 | - |
| MuMu-20260806-231332-087.png | 6-1 | available | Fubuki | Fubuki | 正确 | 彩框 | 彩框 | 6 |
| MuMu-20260806-231332-087.png | 6-2 | available | Hina | Hina | 正确 | 彩框 | 彩框 | 6 |
| MuMu-20260806-231332-087.png | 7-1 | available | Nagisa | Nagisa | 正确 | 彩框 | 彩框 | 7 |
| MuMu-20260806-231332-087.png | 8-1 | available | Kirino | Kirino | 正确 | 彩框 | 彩框 | 8 |
| MuMu-20260806-231332-087.png | 8-2 | available | Tsubaki | Tsubaki | 正确 | 彩框 | 彩框 | 8 |
| MuMu-20260806-231336-603.png | 1-1 | available | Fubuki | Fubuki | 正确 | 彩框 | 彩框 | 1 |
| MuMu-20260806-231336-603.png | 1-2 | available | Hiyori | Hiyori | 正确 | 彩框 | 彩框 | 1 |
| MuMu-20260806-231336-603.png | 1-3 | available | Mashiro | Mashiro | 正确 | 彩框 | 彩框 | 1 |
| MuMu-20260806-231336-603.png | 2-1 | available | Miyako | Miyako | 正确 | 彩框 | 彩框 | 2 |
| MuMu-20260806-231336-603.png | 2-2 | available | Izumi | Izumi | 正确 | 彩框 | 彩框 | 2 |
| MuMu-20260806-231336-603.png | 3-1 | available | Yuuka (Pajamas) | Yuuka (Pajamas) | 正确 | 灰框 | 灰框 | - |
| MuMu-20260806-231336-603.png | 4-1 | available | Hatsune Miku | Hatsune Miku | 正确 | 彩框 | 彩框 | 4 |
| MuMu-20260806-231336-603.png | 4-2 | available | Umika | Umika | 正确 | 灰框 | 灰框 | - |
| MuMu-20260806-231336-603.png | 4-3 | available | Hifumi (Swimsuit) | Hifumi (Swimsuit) | 正确 | 彩框 | 彩框 | 4 |
| MuMu-20260806-231336-603.png | 5-1 | available | Atsuko (Swimsuit) | Atsuko (Swimsuit) | 正确 | 彩框 | 彩框 | 5 |
| MuMu-20260806-231336-603.png | 5-2 | available | Chise (Swimsuit) | Chise (Swimsuit) | 正确 | 彩框 | 彩框 | 5 |
| MuMu-20260806-231336-603.png | 5-3 | available | Juri | Juri | 正确 | 彩框 | 彩框 | 5 |
| MuMu-20260806-231336-603.png | 6-1 | available | Wakamo (Swimsuit) | Wakamo (Swimsuit) | 正确 | 彩框 | 彩框 | 6 |
| MuMu-20260806-231336-603.png | 7-1 | available | Renge | Renge | 正确 | 彩框 | 彩框 | 7 |
| MuMu-20260806-231336-603.png | 7-2 | available | Kaede | Kaede | 正确 | 彩框 | 彩框 | 7 |
| MuMu-20260806-231336-603.png | 8-1 | available | Mine (Pop Idol) | Mine (Pop Idol) | 正确 | 彩框 | 彩框 | 8 |
| MuMu-20260806-231336-603.png | 8-2 | available | Eimi (Swimsuit) | Eimi (Swimsuit) | 正确 | 彩框 | 彩框 | 8 |
| MuMu-20260806-231341-107.png | 1-1 | available | Mari (Pop Idol) | Mari (Pop Idol) | 正确 | 彩框 | 彩框 | 1 |
| MuMu-20260806-231341-107.png | 1-2 | available | Hinata | Hinata | 正确 | 彩框 | 彩框 | 1 |
| MuMu-20260806-231341-107.png | 2-1 | available | Tsubaki (Guide) | Tsubaki (Guide) | 正确 | 灰框 | 灰框 | - |
| MuMu-20260806-231341-107.png | 2-2 | available | Natsu | Natsu | 正确 | 彩框 | 彩框 | 2 |
| MuMu-20260806-231341-107.png | 3-1 | available | Mina | Mina | 正确 | 彩框 | 彩框 | 3 |
| MuMu-20260806-231341-107.png | 4-1 | available | Ibuki | Ibuki | 正确 | 彩框 | 彩框 | 4 |
| MuMu-20260806-231341-107.png | 4-2 | available | Cherino (Hot Spring) | Cherino (Hot Spring) | 正确 | 彩框 | 彩框 | 4 |
| MuMu-20260806-231341-107.png | 5-1 | available | Koharu (Swimsuit) | Koharu (Swimsuit) | 正确 | 彩框 | 彩框 | 5 |
| MuMu-20260806-231341-107.png | 5-2 | available | Meru | Meru | 正确 | 彩框 | 彩框 | 5 |
| MuMu-20260806-231341-107.png | 6-1 | available | Fubuki | Fubuki | 正确 | 彩框 | 彩框 | 6 |
| MuMu-20260806-231341-107.png | 6-2 | available | Karin | Karin | 正确 | 彩框 | 彩框 | 6 |
| MuMu-20260806-231341-107.png | 6-3 | available | Yuuka (Track) | Yuuka (Track) | 正确 | 彩框 | 彩框 | 6 |
| MuMu-20260806-231341-107.png | 7-1 | available | Saori | Saori | 正确 | 灰框 | 灰框 | - |
| MuMu-20260806-231341-107.png | 7-2 | available | Shizuko (Swimsuit) | Shizuko (Swimsuit) | 正确 | 彩框 | 彩框 | 7 |
| MuMu-20260806-231341-107.png | 8-1 | available | Shiroko (Swimsuit) | Shiroko (Swimsuit) | 正确 | 彩框 | 彩框 | 8 |
| MuMu-20260806-231341-107.png | 8-2 | available | Tomoe (Qipao) | Tomoe (Qipao) | 正确 | 彩框 | 彩框 | 8 |
| MuMu-20260806-231345-085.png | 1-1 | available | Fubuki (Swimsuit) | Fubuki (Swimsuit) | 正确 | 彩框 | 彩框 | 1 |
| MuMu-20260806-231345-085.png | 1-2 | available | Aru (Dress) | Aru (Dress) | 正确 | 彩框 | 彩框 | 1 |
| MuMu-20260806-231345-085.png | 1-3 | available | Yukari | Yukari | 正确 | 彩框 | 彩框 | 1 |
| MuMu-20260806-231345-085.png | 2-1 | available | Moe | Moe | 正确 | 彩框 | 彩框 | 2 |
| MuMu-20260806-231345-085.png | 2-2 | available | Haruna (Track) | Haruna (Track) | 正确 | 彩框 | 彩框 | 2 |
| MuMu-20260806-231345-085.png | 2-3 | available | Shun (Small) | Shun (Small) | 正确 | 彩框 | 彩框 | 2 |
| MuMu-20260806-231345-085.png | 3-1 | available | Mari | Mari | 正确 | 彩框 | 彩框 | 3 |
| MuMu-20260806-231345-085.png | 4-1 | available | Shizuko | Shizuko | 正确 | 彩框 | 彩框 | 4 |
| MuMu-20260806-231345-085.png | 4-2 | available | Koharu (Swimsuit) | Koharu (Swimsuit) | 正确 | 彩框 | 彩框 | 4 |
| MuMu-20260806-231345-085.png | 4-3 | available | Aoba | Aoba | 正确 | 彩框 | 彩框 | 4 |
| MuMu-20260806-231345-085.png | 5-1 | available | Hatsune Miku | Hatsune Miku | 正确 | 彩框 | 彩框 | 5 |
| MuMu-20260806-231345-085.png | 6-1 | available | Utaha | Utaha | 正确 | 彩框 | 彩框 | 6 |
| MuMu-20260806-231345-085.png | 7-1 | available | Shiroko Terror | Shiroko Terror | 正确 | 彩框 | 彩框 | 7 |
| MuMu-20260806-231345-085.png | 7-2 | available | Hina (Dress) | Hina (Dress) | 正确 | 彩框 | 彩框 | 7 |
| MuMu-20260806-231345-085.png | 7-3 | available | Karin (Bunny) | Karin (Bunny) | 正确 | 彩框 | 彩框 | 7 |
| MuMu-20260806-231345-085.png | 8-1 | available | Tomoe (Qipao) | Tomoe (Qipao) | 正确 | 彩框 | 彩框 | 8 |
| MuMu-20260806-231349-471.png | 1-1 | available | Mika | Mika | 正确 | 彩框 | 彩框 | 1 |
| MuMu-20260806-231349-471.png | 1-2 | available | Reijo | Reijo | 正确 | 灰框 | 灰框 | - |
| MuMu-20260806-231349-471.png | 2-1 | available | Karin | Karin | 正确 | 彩框 | 彩框 | 2 |
| MuMu-20260806-231349-471.png | 3-1 | available | Toki (Bunny) | Toki (Bunny) | 正确 | 彩框 | 彩框 | 3 |
| MuMu-20260806-231349-471.png | 3-2 | available | Shiroko | Shiroko | 正确 | 彩框 | 彩框 | 3 |
| MuMu-20260806-231349-471.png | 3-3 | available | Eimi | Eimi | 正确 | 彩框 | 彩框 | 3 |
| MuMu-20260806-231349-471.png | 4-1 | available | Midori (Maid) | Midori (Maid) | 正确 | 彩框 | 彩框 | 4 |
| MuMu-20260806-231349-471.png | 4-2 | available | Cherino (Hot Spring) | Cherino (Hot Spring) | 正确 | 彩框 | 彩框 | 4 |
| MuMu-20260806-231349-471.png | 4-3 | available | Hatsune Miku | Hatsune Miku | 正确 | 彩框 | 彩框 | 4 |
| MuMu-20260806-231349-471.png | 5-1 | selected | Yuzu (Maid) | Yuzu (Maid) | 正确 | 彩框 | 彩框 | - |
| MuMu-20260806-231349-471.png | 6-1 | available | Umika | Umika | 正确 | 灰框 | 灰框 | - |
| MuMu-20260806-231349-471.png | 6-2 | available | Kikyou | Kikyou | 正确 | 彩框 | 彩框 | 6 |
| MuMu-20260806-231349-471.png | 7-1 | available | Maki | Maki | 正确 | 彩框 | 彩框 | 7 |
| MuMu-20260806-231349-471.png | 7-2 | available | Wakamo (Swimsuit) | Wakamo (Swimsuit) | 正确 | 彩框 | 彩框 | 7 |
| MuMu-20260806-231349-471.png | 8-1 | available | Mari | Mari | 正确 | 彩框 | 彩框 | 8 |
| MuMu-20260806-231349-471.png | 8-2 | available | Kotama (Camp) | Kotama (Camp) | 正确 | 彩框 | 彩框 | 8 |
