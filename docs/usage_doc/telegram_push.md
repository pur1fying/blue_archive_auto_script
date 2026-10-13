# Telegram 推送

BAAS 支持把 **运行出错** 和 **任务完成** 的通知推送到 Telegram 机器人会话，适合挂机时用手机接收状态。

## 功能入口

GUI: 主界面 -> 设置 -> **推送配置**，在底部四个 Telegram 字段中填写：

| 字段 | 说明 |
| --- | --- |
| Telegram Bot Token | 机器人的 Token，形如 `123456:ABC-DEF...`；留空则不启用 |
| Telegram Chat ID | 接收消息的会话 ID |
| Telegram 代理 | 形如 `http://127.0.0.1:7890`；国内直连通常不可达，一般需要填 |
| Telegram API 地址 | 自定义 API 域名，留空使用 `https://api.telegram.org` |

只有 **Bot Token 和 Chat ID 同时填写** 时，Telegram 推送才会生效；其他推送渠道（Server酱 / 飞书 / 企业微信）互不影响，可以同时启用。

## 获取 Bot Token

1. 在 Telegram 中搜索 **@BotFather** 并关注。
2. 发送 `/newbot`，按提示为机器人取名。
3. 创建成功后 BotFather 会返回一段 Bot Token，复制保存。

## 获取 Chat ID

1. 给你刚创建的机器人发送任意一条消息（例如 `/start`）。
2. 在浏览器打开 `https://api.telegram.org/bot<你的Token>/getUpdates`。
3. 在返回的 JSON 中找到 `message.chat.id`，这个数字就是 Chat ID。

> 注意：必须是你**发给机器人**的会话；机器人不会主动发消息，如果 `getUpdates` 返回 `[]`，说明还没有给它发过消息。

## 本地验证（不依赖游戏）

在项目根目录用 `.venv` 的 Python 跑 demo，真实发送一条测试消息：

```bat
.venv\Scripts\python.exe develop_tools\demo_telegram_push.py --offline
.venv\Scripts\python.exe develop_tools\demo_telegram_push.py
.venv\Scripts\python.exe develop_tools\demo_telegram_push.py --token <TOKEN> --chat-id <CHAT_ID> --proxy http://127.0.0.1:7890
```

凭证来源优先级：命令行参数 > 环境变量（`BAAS_TELEGRAM_BOT_TOKEN` / `BAAS_TELEGRAM_CHAT_ID` / `BAAS_TELEGRAM_PROXY` / `BAAS_TELEGRAM_API`）> `config/<region>/config.json`。

跑离线单元测试（不需要网络）：

```bat
.venv\Scripts\python.exe -m unittest develop_tools.test.test_telegram_push -v
```

## 常见问题

- **发送失败，日志只有 `push exception: ConnectionError`**：网络到不了 Telegram，填代理；日志中不会打印 Token / URL，便于排查。
- **日志 `push failed: chat not found`**：Chat ID 填错，或该会话是群组但机器人不在群里。
- **日志 `push failed: Unauthorized`**：Token 错误或被 BotFather 重置过。
- **代理有效但偶尔超时**：脚本默认 30 秒超时，超时只记一条错误日志，不会阻塞任务运行。
