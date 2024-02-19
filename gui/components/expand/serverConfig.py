from .expandTemplate import TemplateLayout


class Layout(TemplateLayout):
    def __init__(self, parent=None, config=None):
        configItems = [
            {
                'label': '请选择您的服务器，请慎重切换服务器，切换服务器后请重新启动脚本',
                'type': 'combo',
                'key': 'server',
                'selection': ['官服', 'B服', '国际服', '日服']
            },
            {
                'label': '常用端口号一览，请根据你的模拟器设置端口，多开请自行查询。',
                'type': 'label'
            },
            {
                'label': 'MuMu：7555；蓝叠/雷电：5555；夜神：62001或59865；',
                'type': 'label'
            },
            {
                'label': 'Mumu12：16384；逍遥：21503；',
                'type': 'label'
            },
            {
                'label': '请填写您的adb端口号',
                'type': 'text',
                'key': 'adbPort'
            }
        ]
        super().__init__(parent=parent, configItems=configItems, config=config)
