# coding:utf-8
"""Telegram 推送本地 Demo。

不依赖游戏 / 模拟器，直接验证 core/pushkit.py 里的 Telegram 推送链路。

凭证优先级: 命令行参数 > 环境变量 > config/<region>/config.json

用法（在项目根目录下，使用 .venv 的 Python）:
    .venv\\Scripts\\python.exe develop_tools\\demo_telegram_push.py --help
    .venv\\Scripts\\python.exe develop_tools\\demo_telegram_push.py --offline
    .venv\\Scripts\\python.exe develop_tools\\demo_telegram_push.py --region cn
    .venv\\Scripts\\python.exe develop_tools\\demo_telegram_push.py --token <BOT_TOKEN> --chat-id <CHAT_ID> [--proxy http://127.0.0.1:7890]

环境变量（可选）:
    BAAS_TELEGRAM_BOT_TOKEN / BAAS_TELEGRAM_CHAT_ID / BAAS_TELEGRAM_PROXY / BAAS_TELEGRAM_API

退出码: 0=发送成功(或离线自检完成) 1=发送失败 2=未找到可用凭证
"""
import argparse
import json
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

REGION_CANDIDATES = ("cn", "global", "jp", "steam")


class PrintLogger:
    """把 pushkit 的日志打到控制台，方便观察 demo 结果。"""

    def __init__(self):
        self.infos = []
        self.errors = []

    def info(self, message):
        self.infos.append(str(message))
        print(f"  [INFO ] {message}")

    def error(self, message):
        self.errors.append(str(message))
        print(f"  [ERROR] {message}")

    def warning(self, message):
        print(f"  [WARN ] {message}")


def load_from_config(region):
    path = os.path.join(PROJECT_ROOT, "config", region, "config.json")
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def resolve_credentials(args):
    cfg = load_from_config(args.region) if args.region else {}
    if not cfg:
        for region in REGION_CANDIDATES:
            cfg = load_from_config(region)
            if cfg:
                args.region = region
                break

    token = args.token or os.environ.get("BAAS_TELEGRAM_BOT_TOKEN") or cfg.get("push_telegram_bot_token", "")
    chat_id = args.chat_id or os.environ.get("BAAS_TELEGRAM_CHAT_ID") or cfg.get("push_telegram_chat_id", "")
    if args.proxy is not None:  # --proxy "" 表示强制直连，忽略 config 里的代理
        proxy = args.proxy
    else:
        proxy = os.environ.get("BAAS_TELEGRAM_PROXY") or cfg.get("push_telegram_proxy", "")
    api = args.api or os.environ.get("BAAS_TELEGRAM_API") or cfg.get("push_telegram_api", "")
    return token.strip(), chat_id.strip(), proxy.strip(), api.strip()


def print_checklist():
    print("""
还没有可用的 Telegram 凭证，按下面步骤配置后重跑:

1. 创建机器人
   在 Telegram 中搜索 @BotFather -> 发送 /newbot -> 按提示起名
   -> 得到形如 123456:ABC-DEF... 的 Bot Token

2. 获取 Chat ID
   给你刚创建的机器人随便发一条消息（例如 /start）
   然后访问 https://api.telegram.org/bot<你的Token>/getUpdates
   在返回 JSON 的 message.chat.id 字段里找到你的 chat id
   （注意: 必须是你发给机器人的会话，机器人不会主动给你发消息）

3. 填入凭证（任选其一）
   - GUI: 主界面 -> 设置 -> 推送配置，填写四个 Telegram 字段
   - 本脚本: --token / --chat-id 参数，或环境变量 BAAS_TELEGRAM_BOT_TOKEN / BAAS_TELEGRAM_CHAT_ID
   - 配置文件: config/<region>/config.json 的 push_telegram_* 字段

4. 国内网络
   直连 api.telegram.org 通常不可达，需要代理。
   填写形如 http://127.0.0.1:7890 的本地代理地址到 --proxy 或 push_telegram_proxy。

5. 重跑
   .venv\\Scripts\\python.exe develop_tools\\demo_telegram_push.py --offline   # 只自检不发送
   .venv\\Scripts\\python.exe develop_tools\\demo_telegram_push.py             # 真实发送
""")


def main():
    parser = argparse.ArgumentParser(description="Blue Archive Auto Script - Telegram push demo")
    parser.add_argument("--token", help="Bot Token（默认读环境变量 / config.json）")
    parser.add_argument("--chat-id", help="Chat ID（默认读环境变量 / config.json）")
    parser.add_argument("--proxy", help="HTTP 代理，例如 http://127.0.0.1:7890")
    parser.add_argument("--api", help="自定义 Telegram API 地址，默认 https://api.telegram.org")
    parser.add_argument("--region", choices=REGION_CANDIDATES, help="从哪个 config/<region>/config.json 读默认值")
    parser.add_argument("--offline", action="store_true", help="不真正发送，只打印将要发送的消息")
    args = parser.parse_args()

    token, chat_id, proxy, api = resolve_credentials(args)

    from core import pushkit

    data = {
        "title": "Baas Demo",
        "desp": "这是来自 develop_tools/demo_telegram_push.py 的测试消息，收到说明 Telegram 推送配置成功。",
    }
    target = api.rstrip("/") if api else "https://api.telegram.org"

    print("== Telegram 推送 Demo ==")
    print(f"  API 地址 : {target}")
    print(f"  Bot Token: {'已配置' if token else '未配置'}")
    print(f"  Chat ID  : {'已配置' if chat_id else '未配置'}")
    print(f"  代理     : {proxy or '无（直连）'}")
    print("  将发送    :")
    print(f"    {data['title']}\n    {data['desp']}")
    print()

    if args.offline:
        print("[离线模式] 未发送任何消息，代码路径自检完成。")
        return 0

    if not token or not chat_id:
        print_checklist()
        return 2

    logger = PrintLogger()
    pushkit.push_telegram(logger, token, chat_id, data, proxy, api)

    if any("push success" in m for m in logger.infos):
        print("\n发送成功！去 Telegram 查看你机器人的会话即可。")
        return 0
    print("\n发送失败，请根据上面的 [ERROR] 信息排查（代理 / 凭证 / API 地址）。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
