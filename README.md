# Blue Archive Auto Script
![Python](https://img.shields.io/badge/-Python-000000?style=flat&logo=python)

baas，一个带GUI的蔚蓝档案（支持国服），为屏幕分辨率为1280x720 运行的场景而设计 最终目的是接管一切蔚蓝档案任务 实现完全自动化

baas 是一款免费开源软件，地址：https://github.com/pur1fying/blue_archive_auto_script

GUI support, thanks **[@キラメイ Kiramei](https://github.com/Kiramei)** 

GUI预览图：
![gui]()

## 功能 Features

- **咖啡厅** 邀请券可选择指定学生 咖啡厅好感 咖啡厅奖励
- **商店** 支持基物品商店16个商品自动购买 以及竞技场商店13个商品自动购买
- **收获**：每日小组体力 邮箱 竞技场每日领奖 总力战累计积分领奖 每日任务领奖
- **体力清理**：可指定任意主线关卡(普通困难) 特别委托 扫荡任意次数 
- **竞技场** 清理到没有竞技场挑战券为止
- **制造** 可选择制造物品优先级 制造次数 (确保加速券充足)
- **momo talk** 自动完成所有未结束对话 完成剧情 领取青辉石




#### 突出特性：

- **异常检测**：baas有大量监测机制来降低非法操作的影响 但无法完全避免人为操作的影响 确保你选择任务的选项是合法的 并在运行期间不要点击屏幕
- **在低配电脑上运行也不会出现问题** 处理器速度低的电脑可以手动调小截图速度 增长运行时间

## 安装 Installation 


## 如何使用 
- **由于 GUI 未完全开发完毕 一些参数设置**
/module

1."arena.py" line 38

2."cafe_reward.py" line 35

3."clear_special_task_power.py" line 5,6

4."shop.py" line 11 29

/core

  "setup.py" line 13,17

项目目录下

"main.py" line 31,32

- **连接安卓模拟器**
- **打开exe点击启动即可**

## 正确地使用调度器



- ## 如何上报bug How to Report Bugs
- 在qq群内上传出错日志

## 已知问题 Known Issues

- **ocr文字识别不稳定**
- **ioERROR** 截图太快导致 降低截图速度 （>=0.5s为合适）
- **短时间连续的点击操作 模拟器卡顿的情况下会被识别为未被点到**



## 联系我们 Contact Us

- QQ群：658302636 （有开发意向请加作者 Email pur1fying at 2274916027@qq.com）

## 未来目标 Future Goals

- **加入自动推图 自动过剧情模块**
- **完善异常检测机制**
- **训练一个高精度ocr模型**
