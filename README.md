# Blue Archive Auto Script
![Python](https://img.shields.io/badge/-Python-000000?style=flat&logo=python)

baas，一个带GUI(简体中文 English 日本語)的蔚蓝档案（全服支持），为屏幕分辨率为 16：9 (1280x720 最佳) 运行的场景而设计 最终目的是接管一切蔚蓝档案任务 实现完全自动化

关于安装，您可以参考我们的演示视频：[视频链接](https://www.bilibili.com/video/BV19y421e7XF/?spm_id_from=333.337.search-card.all.click)



baas 是一款免费开源软件，地址：https://github.com/pur1fying/blue_archive_auto_script


GUI预览图：

<img src="https://github.com/pur1fying/blue_archive_auto_script/blob/master/docs/assets/ui.png" alt="gui" width="50%">
<img src="https://github.com/pur1fying/blue_archive_auto_script/blob/master/docs/assets/ui2.png" alt="gui" width="50%">
<img src="https://github.com/pur1fying/blue_archive_auto_script/blob/master/docs/assets/ui3.png" alt="gui" width="50%">

## 功能 Features
- **主线**: 自动推图(普通4-26，困难1-26，最新主线<26>已适配)
- **咖啡厅**: 邀请券可选择指定学生 咖啡厅摸头 咖啡厅奖励
- **商店**: 支持指定普通物品商店 以及竞技场商店自动购买和刷新次数
- **收获**: 每日小组体力 邮箱 竞技场每日领奖 总力战累计积分领奖 每日任务领奖
- **体力清理**: 可指定任意主线关卡(普通困难) 特别委托 活动关卡 扫荡任意次数
- **日程**: 指定每个区域日程次数，可优先做加好感度多的日程
- **竞技场**: 清理到没有竞技场挑战券为止，自动领取每日奖励
- **制造**: 可选择制造物品优先级 制造次数 (可选择是否使用加速券)
- **momo_talk**: 自动完成所有未结束对话 完成剧情 领取青辉石
- **总力战**: 清空总力战挑战券并领取奖励(auto, **功能不完善**, 自动总力功能开发中)
- **战术综合测试**: 在考试开启期间自动清票
- **剧情**: 一键清理主线剧情，小组剧情
- **活动**: 一键活动推剧情，任务，挑战，走格子(国服活动稳定更新, 其他服务器随缘)

#### 突出特性：

- **16:9分辨率模拟器都可以运行，不局限于1280x720**
- **在低配电脑上运行也不会出现问题** 处理器速度低的电脑可以手动调小截图速度 增长运行时间
- **自定义调度(每日固定刷新时间，执行间隔)**
## 安装 Installation 
  **请确保安装路径没有中文(QT框架限制)**
  解压Release或qq交流群中的下载包，双击`BlueArchiveAutoScript.exe`安装环境，请耐心等待。
  安装完成后，BAAS 的ui界面将自动启动。同时，我们提供了pyinstaller可使用的打包脚本，您可以自
  行打包，具体内容在`deploy/installer`文件夹中。此外，本项目尝试支持Docker部署，但目前仍无法
  运行，目前在`deploy/docker`文件夹中，如有解决方案，请提交PR。

## 如何使用
一些关键的参数
- **模拟器最佳是mumu模拟器 16：9尺寸 1280x720 60帧**
- **服务器：官服/b服/国际服/日服**
- **连接安卓模拟器：请设置端口号(模拟器多开请自行查询对应端口号)**
- **截图间隔：0.3s (CPU性能高)  /  0.5s - 2s(CPU性能较低)**
  **国际服必须使用英文语言**

推送设置
- **serverchan：填写ServerChan提供的SendKey**
- **json：填写自定义的完整地址（如http://127.0.0.1:8081/）**
- **推送的json格式为:**
`{"title":"Baas Error","desp":"error..."}`

### CLI 使用方法

CLI 用法及 macOS 支持，参考 [CLI.md](CLI.md)。

## 如何上报bug How to Report Bugs
在提问题之前至少花费 5 分钟来思考和准备，才会有人花费他的 5 分钟来帮助你。

在提问题前，请先。
检查 BAAS 的更新，确认使用的是最新版(重启程序自动更新至最新版本)。
如果是非预期的行为，请提供非预期行为发生时UI界面的日志,模拟器截图或视频。

## 已知问题 Known Issues

- **ocr中文文字识别精度尚可,但不是特别高**
- **截图速度过快可能导致问题**
- **在使用本软件时请勿游玩游戏瓦洛兰特(可能会受到若干小时的封号处罚)**
## 联系我们 Contact Us

- QQ群：658302636 （有开发意向请加作者 Email pur1fying at 2274916027@qq.com）
- 欢迎将gui适配其他语言

## 未来目标 Future Goals
- **学生党，痛苦喵，大家一起来开源喵**
- **使用C++重构一部分功能(正在进行中https://github.com/pur1fying/BAAS_Cpp)**
- **使用yolo目标检测训练所有学生追踪模型，完成自动总力战功能**
- **完善体力规划模块,使脚本可以在二/三倍活动掉落期间刷不同图，购买体力等，使刷体力更灵活可变**
- **增加竞技场新赛季碎石挖矿功能**
- **构建一套完善的图像识别+模拟器交互系统**
## 致谢
1.GUI 支持, 感谢 

**[@キラメイ Kiramei](https://github.com/Kiramei)**

**[@Scxppp](https://github.com/Scxppp)** 

2.模拟器启动支持, 感谢 

**[@Daodanfd5](https://github.com/Daodanfd5)**

**[@Drstargaze](https://github.com/Drstargaze)**

3.英文GUI支持, 感谢 

**[@RedDeadDepresso](https://github.com/RedDeadDepresso)**

4.一些bug的修复, 感谢 

**[@2meito](https://github.com/2meito)** 

**[@walkonbothsides](https://github.com/walkonbothsides)** 

**[@misaka10843](https://github.com/misaka10843)**

**[@kibokiboki](https://github.com/kibokiboki)**

**[@Poke Chen](https://github.com/Popopopoke)**

5.推送信息支持, 感谢

**[@wyeeeee](https://github.com/wyeeeee)**

6.帮助文档网站支持, 感谢

**[@lzw-723](https://github.com/lzw-723)**

7.日文GUI支持,同样感谢

**[@キラメイ Kiramei](https://github.com/Kiramei)**

8.韩文GUI支持,感谢
**[@VoltIcaRus](https://github.com/VoltIcaRus) && [@RedDeadDepresso](https://github.com/RedDeadDepresso)**

9.日服活动维护,感谢
**[@shenxianjiejie](https://github.com/shenxian66ya)**

10. 国际服活动维护,感谢
**[@beihaihaihai](https://github.com/beihaihaihai)**

