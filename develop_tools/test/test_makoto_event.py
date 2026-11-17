"""Native English Makoto event resources, no device or AP required."""
import importlib
import json
import os
from pathlib import Path
import runpy
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import cv2
from core import image, position

ROOT=Path(__file__).resolve().parents[2]
EVENT='ChairMakotosLuxSummerGetaway'

class MakotoEventTests(unittest.TestCase):
    def setUp(self):
        self.mapping=runpy.run_path(str(ROOT/'src/images/Global_en-us/x_y_range/activity'/(EVENT+'.py')))
        self.old_ranges=position.image_x_y_range
        self.old_images=position.image_dic
        self.addCleanup(setattr,position,'image_x_y_range',self.old_ranges)
        self.addCleanup(setattr,position,'image_dic',self.old_images)
        common=runpy.run_path(str(ROOT/'src/images/Global_en-us/x_y_range/activity_common.py'))
        ranges=dict(common['x_y_range'],**self.mapping['x_y_range'])
        position.image_x_y_range={'Global_en-us':{'activity':ranges}}
        templates={}
        for data in [common,self.mapping]:
            for key in data['x_y_range']:
                path=ROOT/'src/images/Global_en-us'/data['path']/(key+'.png')
                if path.exists(): templates['activity_'+key]=cv2.imread(str(path))
        position.image_dic={'Global_en-us':templates}

    def test_defaults_and_stage_data(self):
        default=runpy.run_path(str(ROOT/'core/config/default_config.py'))
        self.assertEqual(json.loads(default['STATIC_DEFAULT_CONFIG'])['current_game_activity']['Global'],EVENT)
        data=json.loads((ROOT/'src/explore_task_data/activities'/(EVENT+'.json')).read_text())
        self.assertEqual(len(data['mission']),12)
        self.assertEqual(data['sweep_ap_cost_mission'],[0]+[10]*4+[15]*4+[20]*4)

    def test_only_native_sweeping_is_exposed(self):
        module=importlib.import_module('module.activities.'+EVENT)
        device=Mock()
        with patch.object(module,'activity_sweep',return_value=True) as call:
            self.assertTrue(module.sweep(device))
            call.assert_called_once_with(device)
        for unsupported in ['explore_story','explore_mission','explore_challenge']:
            self.assertFalse(hasattr(module,unsupported))

    def test_all_resources_exist_and_do_not_bind_minigame_as_entry(self):
        self.assertEqual(self.mapping['path'],'activity/'+EVENT)
        self.assertNotIn('enter2',self.mapping['x_y_range'])
        for key,(x1,y1,x2,y2) in self.mapping['x_y_range'].items():
            template=position.image_dic['Global_en-us']['activity_'+key]
            self.assertEqual(template.shape[:2],(y2-y1,x2-x1))

    def test_native_resource_loader_for_each_global_locale(self):
        old=position.initialized_image.copy()
        self.addCleanup(setattr,position,'initialized_image',old)
        for locale in ['Global_en-us','Global_zh-tw','Global_ko-kr']:
            position.initialized_image[locale]=False
            device=SimpleNamespace(identifier=locale,current_game_activity=EVENT,
                                   dailyGameActivity=None,logger=Mock())
            self.assertTrue(position.init_image_data(device),locale)
            self.assertIn('activity_enter1',position.image_dic[locale])
            self.assertIn('activity_enter3',position.image_dic[locale])
            self.assertNotIn('activity_enter2',position.image_dic[locale])

    def test_user_screenshots_with_native_comparison(self):
        directory=os.environ.get('BAAS_MAKOTO_SCREENSHOTS')
        if not directory: self.skipTest('Set BAAS_MAKOTO_SCREENSHOTS to local reference screenshot folder')
        expected={'home':['enter1','enter3'], 'story':['menu','mission-not-chosen-1'], 'quest':['menu','mission-chosen-1']}
        for screen,positive in expected.items():
            frame=cv2.imread(str(Path(directory)/('makoto-ref-'+screen+'.png')))
            self.assertIsNotNone(frame)
            for ratio in [1,1.5,2]:
                screenshot=cv2.resize(frame,(int(1280*ratio),int(720*ratio)))
                device=SimpleNamespace(identifier='Global_en-us',ratio=ratio,latest_img_array=screenshot)
                for key in positive:
                    with self.subTest(screen=screen,key=key,ratio=ratio): self.assertTrue(image.compare_image(device,'activity_'+key))
                for key in ['enter1','enter3']:
                    if screen!='home': self.assertFalse(image.compare_image(device,'activity_'+key))

if __name__=='__main__': unittest.main()
