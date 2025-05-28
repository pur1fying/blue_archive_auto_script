# Blue Archive Auto Script
![Python](https://img.shields.io/badge/-Python-000000?style=flat&logo=python)

**BAAS**,一个带GUI的蔚蓝档案（全服支持），为屏幕分辨率为 16:9 (1280x720 最佳) 运行的场景而设计 最终目的是接管一切蔚蓝档案任务 实现完全自动化

GUI预览图：

<img src="https://github.com/pur1fying/blue_archive_auto_script/blob/master/docs/assets/ui.png" alt="gui" width="50%">
<img src="https://github.com/pur1fying/blue_archive_auto_script/blob/master/docs/assets/ui2.png" alt="gui" width="50%">
<img src="https://github.com/pur1fying/blue_archive_auto_script/blob/master/docs/assets/ui3.png" alt="gui" width="50%">

## 功能 Features
- **角色好感度**: 咖啡厅一日8摸, 日程自动找指定学生, 每日最大限度提升好感度
- **主线**: 自动推图(普通4-28，困难1-28，最新主线<28>已适配)
- **咖啡厅**: 邀请券可选择指定学生 咖啡厅摸头 咖啡厅奖励
- **商店**: 支持指定普通物品商店 以及竞技场商店自动购买和刷新次数
- **收获**: 每日小组体力 邮箱 竞技场每日领奖 总力战累计积分领奖 每日任务领奖
- **体力清理**: 可指定任意主线关卡(普通困难) 特别委托 活动关卡 扫荡任意次数
- **日程**: 优先做指定角色存在的日程, 可优先做加好感度多的日程, 指定每个区域日程次数
- **竞技场**: 清理到没有竞技场挑战券为止，自动领取每日奖励
- **制造**: 无缝制造三解 指定制造优先级 次数 是否使用加速券 
- **momotalk**: 自动完成所有未结束对话 完成剧情 领取青辉石
- **总力战**: 清空总力战挑战券并领取奖励(自动凹分功已在[该仓库](https://github.com/pur1fying/BAAS_Cpp)适配, 正在接入**BAAS**)
- **战术综合测试**: 在考试开启期间自动清票
- **剧情**: 一键清理主线剧情，小组剧情, 迷你剧情
- **活动**: 一键活动推剧情，任务，挑战，走格子(三服活动稳定更新)

### 突出特性：

- **16:9分辨率模拟器都可以运行，不局限于1280x720**
- **在低配电脑上运行也不会出现问题** 处理器速度低的电脑可以手动调小截图速度 增长运行时间
- **自定义调度(每日固定刷新时间，执行间隔)**

## 安装 Installation 
  **请确保安装路径没有中文(QT框架限制)**
  解压Release或qq交流群中的下载包，双击`BlueArchiveAutoScript.exe`安装环境，请耐心等待。
  安装完成后，BAAS 的ui界面将自动启动。同时，我们提供了pyinstaller可使用的打包脚本，您可以自
  行打包，具体内容在`deploy/installer`文件夹中。
  [安装相关文档](https://blog.lzwi.fun/blue_archive_auto_script/usage_doc/install/choose_platform)
## 如何使用
用户文档见[wiki](https://blog.lzwi.fun/blue_archive_auto_script/), 有详细的BAAS配置教程和使用方法

## 如何上报bug How to Report Bugs
在提问题之前至少花费 5 分钟来思考和准备，才会有人花费他的 5 分钟来帮助你。

在提问题前，请先。
检查 BAAS 的更新，确认使用的是最新版(重启程序自动更新至最新版本)。
如果是非预期的行为，请提供非预期行为发生时UI界面的日志,模拟器截图或视频。

## 开发
我们会在github issue和开发文档中发布一些需求,如果您有兴趣可以参与开发, 欢迎向**BAAS**提交pull request,我们会仔细阅读你的每一行代码, 哦对了,别忘了阅读[开发文档](https://blog.lzwi.fun/blue_archive_auto_script/develop_doc/develop_guide)

1. 如果你会使用yolo目标检测,请联系作者,我们需要一个检测模型以供自动总力战使用
2. 欢迎将gui适配其他语言(目前有English,简体中文,日本語, 한국말)
3. 本项目尝试支持Docker部署，但目前仍无法运行，目前在`deploy/docker`文件夹中，如有解决方案，请提交PR

## 已知问题 Known Issues
- **ocr字符识别精度尚可,但对一些特殊字符会有误识别**
- **在使用本软件时请勿游玩游戏瓦洛兰特(可能会受到若干小时的封号处罚)**

## 联系我们 Contact Us
- QQ 
  - 1群: 658302636
  - 2群: 1027430247
- 有开发意向请加作者 Email pur1fying at 2274916027@qq.com）
- BiliBili: 
  - [BAAS-Official](https://space.bilibili.com/259089751)
  - [益生君-1208](https://space.bilibili.com/496075546)(一些视频教程)
## 未来目标 Future Goals
- **学生党，痛苦喵，大家一起来开源喵**
- **使用C++重构一部分功能(正在进行中https://github.com/pur1fying/BAAS_Cpp)**
- **使用yolo目标检测训练所有学生追踪模型, 完成自动总力战功能**
- **完善体力规划模块,使脚本可以在二/三倍活动掉落期间刷不同图，购买体力等，使刷体力更灵活可变**
- **增加竞技场新赛季碎石挖矿功能**
- **构建一套完善的图像识别+模拟器交互系统**

## [致谢名单](https://blog.lzwi.fun/blue_archive_auto_script/thanks)

![Contributors](https://contrib.rocks/image?repo=pur1fying/blue_archive_auto_script)
