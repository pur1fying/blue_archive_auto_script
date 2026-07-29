class FakeConfig:
    def __init__(self, values):
        self.values = dict(values)
        self.writes = []

    def get(self, key, default=None):
        return self.values.get(key, default)

    def set(self, key, value):
        self.values[key] = value
        self.writes.append((key, value))


class SettingsConfig(FakeConfig):
    def inject(self, component, text, attribute="setText"):
        getattr(component, attribute)(text.replace("{name}", "Test"))

    def get_window(self):
        return None
