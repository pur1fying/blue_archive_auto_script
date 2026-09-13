"""Replay Traditional Chinese invitation sorting without connecting to a device.

Fixtures contain only the sorting header at (640, 130, 865, 175), captured
at 2560x1440. No account information or student list is included.
"""

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import cv2
import numpy as np

from core import image, position
from module import cafe_reward as cafe


FIXTURES = Path(__file__).parent / 'fixtures' / 'cafe_global_zh_tw'


class SortReplay:
    identifier = 'Global_zh-tw'
    server = 'Global'
    current_game_activity = None
    dailyGameActivity = None
    flag_run = True
    is_android_device = False
    logger = SimpleNamespace(info=lambda *args: None, error=lambda *args: None)

    def __init__(self, direction, ratio):
        self.direction = direction
        self.ratio = ratio
        self.clicks = []
        self.updates = 0
        self.update_screenshot_array()

    def update_screenshot_array(self):
        self.updates += 1
        if self.updates > 4:
            raise AssertionError('Sorting did not reach the requested direction')
        screenshot = np.zeros((1440, 2560, 3), dtype=np.uint8)
        header = cv2.imread(str(FIXTURES / (self.direction + '.png')))
        screenshot[260:350, 1280:1730] = header
        self.latest_img_array = screenshot if self.ratio == 2 else cv2.resize(
            screenshot, (1280, 720), interpolation=cv2.INTER_AREA
        )

    def click(self, x, y, *args, **kwargs):
        if (x, y) != (815, 151):
            raise AssertionError(f'Unexpected sorting click: {(x, y)}')
        self.clicks.append((x, y))
        self.direction = 'ascending' if self.direction == 'descending' else 'descending'


class GlobalCafeSortTest(unittest.TestCase):
    def setUp(self):
        for name in ('image_dic', 'image_x_y_range', 'initialized_image'):
            guard = patch.object(position, name, getattr(position, name).copy())
            guard.start()
            self.addCleanup(guard.stop)
        position.initialized_image['Global_zh-tw'] = False
        position.image_dic['Global_zh-tw'] = {}
        position.image_x_y_range['Global_zh-tw'] = {}
        self.assertTrue(position.init_image_data(SortReplay('ascending', 1)))

    def test_affection_label_and_both_directions(self):
        for direction, order in [('ascending', 'up'), ('descending', 'down')]:
            for ratio in (1, 2):
                with self.subTest(direction=direction, ratio=ratio):
                    replay = SortReplay(direction, ratio)
                    self.assertTrue(image.compare_image(
                        replay, 'cafe_invitation-ticket-order-affection', threshold=0.9
                    ))
                    self.assertTrue(image.compare_image(
                        replay, 'cafe_invitation-ticket-order-' + order
                    ))
                    opposite = 'down' if order == 'up' else 'up'
                    self.assertFalse(image.compare_image(
                        replay, 'cafe_invitation-ticket-order-' + opposite
                    ))

    def test_lowest_affection_reaches_first_student(self):
        for direction in ('ascending', 'descending'):
            for ratio in (1, 2):
                with self.subTest(direction=direction, ratio=ratio):
                    replay = SortReplay(direction, ratio)
                    # Isolate entry/confirmation and loading; sorting and image
                    # recognition run unchanged against the captured header.
                    with patch.object(cafe, 'to_invitation_ticket', return_value='cafe_invitation-ticket'), \
                            patch.object(cafe, 'checkConfirmInvite', return_value=True) as confirm, \
                            patch.object(cafe.color, 'wait_loading'), \
                            patch.object(cafe, 'to_revise_order_type', side_effect=AssertionError(
                                'Already selected affection sorting was not recognized'
                            )):
                        cafe.invite_by_affection(replay, 'lowest')
                    confirm.assert_called_once_with(replay, 226)
                    self.assertEqual(replay.clicks, [(815, 151)] if direction == 'descending' else [])


if __name__ == '__main__':
    unittest.main()
