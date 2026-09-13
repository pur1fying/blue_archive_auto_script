"""Offline lesson catalog, preference migration and settings-dialog regressions."""

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from core.config.config_set import ConfigSet
from core.config.generated_static_config import StaticConfig
from PyQt5.QtWidgets import QApplication
from gui.util.config_draft import ConfigDraft
from core.utils import build_possible_string_dict_and_length
from module.lesson import pre_process_lesson_name, get_lesson_region_num
from types import SimpleNamespace

from core.config.default_config import DEFAULT_CONFIG, STATIC_DEFAULT_CONFIG
from gui.components.expand import schedulePriority as panel

class LessonCatalogTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'config.json'
        self.catalog = json.loads(STATIC_DEFAULT_CONFIG)
        self.static = StaticConfig(**self.catalog)
        p = patch.object(ConfigSet, 'static_config', self.static)
        p.start()
        self.addCleanup(p.stop)

    def make_config(self, count=11, server='国际服'):
        self.original = json.loads(DEFAULT_CONFIG)
        self.original.update(server=server, lesson_times=[i % 4 for i in range(count)],
                             lesson_each_region_object_priority=[['superior'] if i % 2 else [] for i in range(count)])
        self.path.write_text(json.dumps(self.original, ensure_ascii=False), encoding='utf-8')
        return ConfigSet(self.directory.name)

    def test_catalog_languages(self):
        names = self.catalog['lesson_region_name']
        for key, name in [('Global_en-us', 'Wildhunt Integrated Arts District'),
                          ('Global_zh-tw', '狂獵綜合藝術區'), ('Global_ko-kr', '와일드헌트 종합 예술 지구')]:
            self.assertEqual(len(names[key]), 12)
            self.assertEqual(names[key][11], name)
        self.assertEqual(names['Global_zh-tw'][5], '三一廣場')
        self.assertEqual(len(names['CN']), 11)
        self.assertEqual(len(names['JP']), 12)

    def test_load_migrates_only_lesson_fields_and_is_idempotent(self):
        config = self.make_config()
        expected = dict(self.original)
        expected['lesson_times'] = self.original['lesson_times'] + [0]
        expected['lesson_each_region_object_priority'] = self.original['lesson_each_region_object_priority'] + [['primary', 'normal', 'advanced', 'superior']]
        self.assertEqual(json.loads(self.path.read_text(encoding='utf-8')), expected)
        with patch.object(ConfigSet, 'save') as save:
            config._init_config()
            save.assert_not_called()

    def test_gui_preserves_existing_choices_when_catalog_grows(self):
        # Also exercise GUI validation with a stale draft, independently of load migration.
        config = self.make_config()
        draft = ConfigDraft(config)
        draft.set('lesson_times', self.original['lesson_times'])
        draft.set('lesson_each_region_object_priority', self.original['lesson_each_region_object_priority'])
        # Baseline has only 11 regions; supply the actual game's twelfth row.
        names = self.static.lesson_region_name['Global_en-us']
        if len(names) == 11:
            names.append('Wildhunt Integrated Arts District')
        widget = panel.Layout(config=draft)
        try:
            self.assertEqual(len(widget.lesson_time_input), 12)
            self.assertEqual(widget.priority_list, self.original['lesson_times'] + [0])
            self.assertEqual(widget.needed_levels[:11], self.original['lesson_each_region_object_priority'])
            self.assertEqual(widget.lesson_names[-1], 'Wildhunt Integrated Arts District')
            widget.lesson_time_input[11].setText('2')
            widget.Slot_for_lesson_time_change()
            draft.commit()
            self.assertEqual(config.get('lesson_times'), self.original['lesson_times'] + [2])
        finally:
            widget.close()
            widget.deleteLater()
            self.app.processEvents()

    def test_current_configs_and_other_servers_keep_preferences(self):
        for server, count in [('国际服', 12), ('国际服', 6), ('官服', 11), ('日服', 12)]:
            config = self.make_config(count, server)
            self.assertEqual(config.config.lesson_times, self.original['lesson_times'])
            self.assertEqual(config.config.lesson_each_region_object_priority, self.original['lesson_each_region_object_priority'])

    def test_traditional_chinese_runtime_resolves_twelfth_region(self):
        f = SimpleNamespace(server='Global', identifier='Global_zh-tw', flag_run=True, ocr_language='zh-tw',
                            logger=SimpleNamespace(info=lambda *a: None, warning=lambda *a: None),
                            update_screenshot_array=lambda: None,
                            ocr=SimpleNamespace(get_region_res=lambda **kw: '狂獵綜合藝術區'))
        names = [pre_process_lesson_name(f, name) for name in self.static.lesson_region_name[f.identifier]]
        f.lesson_letter_dict, f.lesson_region_name_len = build_possible_string_dict_and_length(names)
        self.assertEqual(get_lesson_region_num(f), 11)

if __name__ == '__main__':
    unittest.main(verbosity=2)
