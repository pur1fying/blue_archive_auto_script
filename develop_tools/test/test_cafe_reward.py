import unittest
from types import SimpleNamespace
from unittest.mock import Mock, call, patch

from module import cafe_reward


class CafeRewardTest(unittest.TestCase):
    def test_desktop_zoom_scrolls_at_scaled_window_center(self):
        for resolution, center in (
            ((1280, 720), (640, 360)),
            ((1920, 1080), (960, 540)),
            ((2560, 1440), (1280, 720)),
            ((1600, 920), (800, 460)),
        ):
            with self.subTest(resolution=resolution):
                bot = Mock(is_android_device=False, resolution=resolution)

                cafe_reward.zoom_out(bot)

                self.assertEqual(bot.control.scroll.call_args_list, [call(*center, 10)] * 15)

    def test_android_releases_gift_after_capture_even_if_capture_fails(self):
        for ratio, y, positions in (
            (1, 660, (131, 151, 173, 203)),
            (1.25, 825, (163, 188, 216, 253)),
            (1.5, 990, (196, 226, 259, 304)),
            (2, 1320, (262, 302, 346, 406)),
        ):
            with self.subTest(ratio=ratio):
                bot = Mock(is_android_device=True, ratio=ratio)
                bot.get_screenshot_array.side_effect = RuntimeError("capture failed")

                with patch.object(cafe_reward.time, "sleep"):
                    with self.assertRaisesRegex(RuntimeError, "capture failed"):
                        cafe_reward.capture_gift_drag(bot)

                self.assertEqual(
                    bot.mock_calls,
                    [
                        call.u2.touch.down(positions[0], y),
                        *(call.u2.touch.move(x, y) for x in positions[1:]),
                        call.get_screenshot_array(),
                        call.u2.touch.up(positions[-1], y),
                    ],
                )

    def test_pat_rounds_scan_different_areas_even_after_an_empty_view(self):
        bot = Mock()
        bot.config = SimpleNamespace(cafe_reward_affection_pat_round=4)
        students_by_view = [[], [(320, 210)], [(830, 300), (900, 642)], [(470, 490)]]
        scans = []

        def scan(_):
            self.assertEqual(bot.swipe.call_count, len(scans) + 1)
            x1, y1, x2, y2 = bot.swipe.call_args.args[:4]
            scans.append((x2 - x1, y2 - y1))
            return students_by_view[len(scans) - 1]

        with (
            patch.object(cafe_reward, "zoom_out"),
            patch.object(cafe_reward, "to_cafe"),
            patch.object(cafe_reward, "cafe_to_gift"),
            patch.object(cafe_reward, "find_student_position", side_effect=scan),
            patch.object(cafe_reward.time, "sleep"),
        ):
            cafe_reward.interaction_for_cafe_solve_method3(bot)

        self.assertEqual(len(set(scans)), 4)
        self.assertTrue(any(dx > 0 for dx, _ in scans))
        self.assertTrue(any(dx < 0 for dx, _ in scans))
        self.assertTrue(any(dy > 0 for _, dy in scans))
        self.assertTrue(any(dy < 0 for _, dy in scans))
        self.assertEqual(
            bot.click.call_args_list,
            [
                call(320, 210, wait_over=True),
                call(830, 300, wait_over=True),
                call(470, 490, wait_over=True),
            ],
        )
