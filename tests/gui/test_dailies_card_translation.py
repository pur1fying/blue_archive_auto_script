from gui.components import expand
from gui.components.template_card import TemplateSettingCardForClick
import gui.components.template_card as template_card
from tests.gui.helpers import FakeConfig


def test_card_mode_translates_json_backed_text(qapp, monkeypatch):
    calls = []

    def fake_translate(context, text):
        calls.append((context, text))
        return f"translated:{text}"

    monkeypatch.setattr(template_card.bt, "tr", fake_translate)
    card = TemplateSettingCardForClick(
        title="无限制决战",
        content="设置编队方式及复制通关队伍限制",
        setting_name="finalRestrictionRls",
        sub_view=expand.finalRestrictionRls,
        config=FakeConfig({}),
        context="ConfigTranslation",
    )

    assert card.title == "translated:无限制决战"
    assert card.content == "translated:设置编队方式及复制通关队伍限制"
    assert calls == [
        ("ConfigTranslation", "无限制决战"),
        ("ConfigTranslation", "设置编队方式及复制通关队伍限制"),
    ]
