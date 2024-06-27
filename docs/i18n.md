# i18n Guide

## Requirements

- [Qt Linguist](https://github.com/thurask/Qt-Linguist/releases)
- [OPTIONAL]
```
pip install -r requirements-i18n.txt
```

## Translation

### Adding a New Language
To include a new language, add a new member to the Language enum representing the language with its corresponding QLocale object. Then, update the combobox method to return a list of language names based on the enum members order. For example, to add Japanese:
```
class Language(Enum):
    """ Language enumeration """

    CHINESE_SIMPLIFIED = QLocale(QLocale.Chinese, QLocale.China)
    ENGLISH = QLocale(QLocale.English, QLocale.UnitedStates)
    JAPANESE = QLocale(QLocale.Japanese, QLocale.Japan)

    def combobox():
        return ['简体中文', 'English', '日本語']
```

Run the Python file; it will print the language acronym:

```
ja_JP
```

Open `i18n.pro` and modify the `TRANSLATION` variable by appending `gui/i18n/` + acronym:

```pro
TRANSLATIONS += gui/i18n/en_US.ts \
        gui/i18n/ja_JP.ts \
```

Execute the following command to generate `.ts` files:

```
pylupdate5 i18n.pro
```

OPTIONAL: `auto_translate.py`

Utilize `argostranslate` to accelerate translations after installing the necessary packages from `requirements-i18n.txt`. Note that while translations may not be perfect, they can speed up the process.

Simply create a new `Request` instance at the end of `auto_translate.py` and invoke its `process` method.

The `Request` constructor is as follows:

```python
class Request:
    from_code = "zh"

    def __init__(self, handlers: list[Handler], language: Language, argos_model: str):
        """
        Parameters
        ----------
        handlers: list[Handler]
            a list of handlers that represent the files to translate. 

        language: Language
            the memeber of the enum Language to translate

        argos_model: str 
            The argos model to load for translation
        """
```

Then:

```python
model = ModelHandler()
ts = XmlHandler()
descriptions = HtmlHandler()

request_jp = Request([model, ts, descriptions], Language.JAPANESE, 'ja')
request_jp.process()
```

This means that `.ts` and description files will be generated. You can adjust the list of handlers as needed, but `model` must always be the first element. 

Also, in case no model exists for your language, you could create a new subclass of Request, override its translate method to use another Python library, and omit ModelHandler from the list of handlers.

Open `Qt Linguist`, load the `.ts` file, and manually translate. This step will require some time.

Afterward, navigate to `gui/i18n` and execute the following command:

```
lrelease ja_JP.ts
```

This will produce the `.qm` files.

## `baasTranslator`

### Problems
In normal scenarios, the `tr` method of `QObject` is used for translation, inherited by most PyQt5 classes. However, this approach isn't always possible for `baas` due to:

- Widget text being generated from JSON files
- Need to retain user input (e.g., combobox selections) in Chinese within config files

### Solution
To address this:

- `ConfigTranslation`: a `QObject` subclass with a dictionary attribute mapping text enclosed in `self.tr` to itself:

```python
...
self.entries = {
    # display
    self.tr("每日特别委托"): "每日特别委托",
...
```

- Utilize a specific instance of `QTranslator` named `baasTranslator` from `gui/util/translator.py` as `bt`, employing its methods:

  - `tr(context, sourceText)`
  - `undo(text)`

For instance, `bt.tr('ConfigTranslation', '国际服')` will produce its translation, 'Global', and `bt.undo('Global')` will revert it to '国际服'. This functionality is already implemented in `get` and `set` method of `ConfigSet`.

In essence, `tr` accesses the `.qm` file to retrieve translations based on the `ConfigTranslation` context, while `undo` retrieves the value from the mapped dictionary where the translation was stored.

Note that contexts other than `'ConfigTranslation'` are accessible. For example:

```python
class Layout(TemplateLayout):
    def __init__(self, parent=None, config=None):
        configItems = [
            {
                'label': '一键反和谐',
                'type': 'button',
                'selection': self.fhx,
                'key': None
            },
...
        super().__init__(parent=parent, configItems=configItems, config=config)
```

Suppose you want to translate the `label` and `selection` but can't access the `tr` method directly since you must first invoke the parent constructor and wish to avoid extensive modifications. Here's a solution:

```python
class Layout(TemplateLayout):
    def __init__(self, parent=None, config=None):
        OtherConfig = QObject()
        configItems = [
            {
                'label': OtherConfig.tr('一键反和谐'),
                'type': 'button',
                'selection': self.fhx,
                'key': None
            },
...
        super().__init__(parent=parent, configItems=configItems, config=config, context="OtherConfig")
```

1. Add a new `context` parameter to the `TemplateLayout` constructor.
2. Create an instance of `QObject` named `OtherConfig`. This establishes a new context when generating the `.ts` files, allowing you to pass `'OtherConfig'` to the `TemplateLayout` constructor.

Now, accessing translations in `TemplateLayout` becomes straightforward:

```python
class TemplateLayout(QWidget):
    patch_signal = pyqtSignal(str)

    def __init__(self, configItems: Union[list[ConfigItem], list[dict]], parent=None, config=None, context=None):
...
    labelComponent = QLabel(bt.tr(context, cfg.label), self)
```

## Adding new GUI .py files
Please ensure to include the file path of the new GUI .py files into the `i18n.pro` file's `SOURCES` variable, taking care to use the correct slashes. For instance, if you're adding `table.py` located in `gui/components`, it should be appended like this:

```
SOURCES += \
    gui/components/table.py \
```

## Adding new Config value
When adding a new config value that appears on the GUI and needs translation, update the `ConfigTranslation` dictionary by adding a new key-value pair. For comboboxes, make sure to include all options.
