import cv2

from .expandTemplate import TemplateLayout


def screenshot():
    from main import Main
    main = Main()
    test_img = main.get_screenshot_array()
    cv2.imshow('Test Screenshot', test_img)
    cv2.waitKey(-1)


class Layout(TemplateLayout):
    def __init__(self, parent=None):
        configItems = [
            {
                'label': '请选择您的服务器',
                'type': 'combo',
                'key': 'server',
                'selection': ['官服', 'B服', '国际服']
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
            },
            {
                'label': '截图测试',
                'type': 'button',
                'selection': screenshot
            }
        ]
        super().__init__(parent=parent, configItems=configItems)
