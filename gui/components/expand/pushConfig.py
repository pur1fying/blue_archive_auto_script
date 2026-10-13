from .expandTemplate import TemplateLayout
from PyQt5.QtCore import QObject


class Layout(TemplateLayout):
    def __init__(self, parent=None, config=None):
        PushConfig = QObject()
        configItems = [            {
                'label': PushConfig.tr('在运行出错时推送'),
                'key': 'push_after_error',
                'type': 'switch'
            },
            {
                'label': PushConfig.tr('在全部任务完成时推送'),
                'key': 'push_after_completion',
                'type': 'switch'
            },
            {
                'label': PushConfig.tr('json 推送'),
                'type': 'text',
                'key': 'push_json'
            },
            {
                'label': PushConfig.tr('ServerChan推送'),
                'type': 'text',
                'key': 'push_serverchan'
            },
            {
                'label': PushConfig.tr('飞书推送'),
                'type': 'text',
                'key': 'push_feishu'
            },
            {
                'label': PushConfig.tr('企业微信推送'),
                'type': 'text',
                'key': 'push_wecom'
            },
            {
                'label': PushConfig.tr('Telegram Bot Token'),
                'type': 'text',
                'key': 'push_telegram_bot_token',
                'tip': '通过 Telegram 中的 @BotFather 创建机器人后获得；与 Chat ID 任一为空则不启用 Telegram 推送'
            },
            {
                'label': PushConfig.tr('Telegram Chat ID'),
                'type': 'text',
                'key': 'push_telegram_chat_id',
                'tip': '私聊中先给机器人发一条消息，然后访问 https://api.telegram.org/bot<你的token>/getUpdates 查看 message.chat.id'
            },
            {
                'label': PushConfig.tr('Telegram 代理'),
                'type': 'text',
                'key': 'push_telegram_proxy',
                'tip': '例如 http://127.0.0.1:7890；国内直连 Telegram API 不通时填写本机代理，留空表示不使用代理'
            },
            {
                'label': PushConfig.tr('Telegram API 地址'),
                'type': 'text',
                'key': 'push_telegram_api',
                'tip': '自定义 API 域名，留空使用 https://api.telegram.org'
            }
        ]

        super().__init__(parent=parent, configItems=configItems, config=config, context="PushConfig")
