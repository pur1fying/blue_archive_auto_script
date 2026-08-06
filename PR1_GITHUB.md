# fix(ui): Card 弹窗草稿保存 + 去掉行内确定 + 商店滚动 UX

## Summary
Card 模式配置弹窗改为「确定才落盘 / 取消丢弃」；去掉各 Layout 行内「确定」；普通商店与竞技场商店统一宽度与视口高度，内容可滚、刷新次数描边置顶。

## 动机
- 原先 Card 弹窗里改一项就写盘，点取消也无法撤销。
- 多个展开页自带行内「确定」，和对话框 OK/Cancel 双重确认，体验乱。
- 商店固定高度裁切 / 或空白过大；竞技场商店被挡。

## 改动

### 1. 草稿保存（核心）
- 新增 `gui/util/config_draft.py`：`ConfigDraft` 代理 `get/set/update`
- Card 打开详情注入 draft
- 对话框 **确定** → flush 焦点 + `commit` + 右上角「已保存」
- 对话框 **取消** → `rollback`
- `ConfigDraft` 不对 list 等非字符串做 `bt.tr/undo`（避免商店 list 崩溃）

### 2. 去掉行内确定
以下改为失焦/变更写草稿，落盘仍靠对话框确定：
`arenaPriority` / `mainlinePriority` / `schedulePriority` / `cafeInvite` / `friendWhiteList` / `emulatorConfig` / 两商店刷新次数

### 3. 商店 UX
- 刷新次数 → 顶栏右侧 + 矩形描边
- `FlowLayout(..., needAni=False)`
- 两店统一宽 800、视口高 400；内容 `minimumHeight` 驱动纵向滚动

### 4. Review 修复
- `notification.saved` 直接 `_saved` + `get_window()`
- 修 `QVBoxLayout(wrapper.widget())`；刷新 `int()`；删空 `setChecked`
- 次数：`editingFinished`（避免 `@delay` 丢最后一次）
- 删 `confirmButton` 死代码；咖啡厅打开不假 dirty

## 测试计划
- [ ] Card：竞技场商店改勾选/刷新 → 取消 → 恢复
- [ ] 同上 → 确定 → 「已保存」→ 再开为新值
- [ ] 普通商店 / 竞技场商店弹窗高度一致，可滚到底
- [ ] 日程次数、咖啡厅摸头：改完立刻确定能写入
- [ ] 商店打开无 Flow 排列动画

## 范围
- 仅 Card + `config.json`
- List 模式 / featureSwitch event.json 事务不在本 PR

---

## PR2 愿景（本 PR 合并后）
商店改为 **BA 商店外框多选样式**：整卡点选变蓝、按最长文案统一卡宽、刷新独立右上 chrome、左上「请勾选购买物品」；共用面板 + 每日估算（竞技场 `币数+币数×刷新+刷新×10`）；咖啡厅减闪、长 Combo 更跟手。详见仓库根目录 `pr1-change.md` 愿景段。
