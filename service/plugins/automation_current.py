"""Bounded takeover of recognized game pages using the host's route engines.

Behavior adapted from pur1fying/blue_archive_auto_script PR #583 (GPL-3.0),
without Qt, duplicated handlers, input monkey patches or generic color clicks.
Unknown screens stop before taking any action.
"""
from __future__ import annotations

import re

from .errors import PluginError, require


def push_current_story(baas) -> bool:
    from core import picture
    from module import main_story, mini_story, group_story
    modules = {'main_story': main_story, 'mini_story': mini_story, 'group_story': group_story}
    endings = ['main_story_plot-not-open', 'main_story_plot-index']
    for family in modules:
        endings.extend(family + suffix for suffix in ('_menu', '_select-episode', '_episode-info', '_episode-cleared-feature'))
    # These are explicit activity story tabs, not arbitrary blue buttons.
    endings.extend(['activity_story-chosen-0', 'activity_story-chosen-1'])
    no_new = 0
    for _ in range(120):
        if not baas.flag_run:
            return False
        screen = picture.co_detect(baas, img_ends=endings, skip_first_screenshot=False, time_out=8)
        if screen.startswith('activity_story-chosen'):
            from module.activities import activity_utils
            require(bool(baas.current_game_activity), 'UNSUPPORTED_PAGE', 'This activity has no supported story route.')
            count = int(activity_utils.get_stage_data(baas).get('total_story', 0))
            require(0 < count <= 100, 'UNSUPPORTED_PAGE', 'This activity has no supported story route.')
            for chapter in range(1, count + 1):
                plot = activity_utils.to_story_task_info(baas, chapter, count)
                if not plot:
                    return True
                if activity_utils.check_sweep_availability(baas, plot) != 'sss':
                    activity_utils.start_story(baas)
                    activity_utils.to_activity(baas, 'story', True)
            return True
        if screen == 'main_story_plot-not-open':
            return True
        family = next((name for name in modules if screen.startswith(name)), None)
        require(family is not None, 'UNSUPPORTED_PAGE', 'Open a supported story menu or episode page first.')
        module = modules[family]
        if screen.endswith('_episode-info'):
            if family == 'main_story':
                baas.main_story_stage_data = main_story.get_stage_data()
            require(module.clear_current_plot(baas, True) is not False, 'DEVICE_TASK_FAILED', 'Story playback did not finish.')
            no_new = 0
        elif screen.endswith('_episode-cleared-feature'):
            baas.click(56, 40, wait_over=True)
        elif screen.endswith('_menu'):
            if family == 'main_story':
                position = main_story.check_episode(baas)
                if position == 'ALL_CLEAR':
                    return True
            else:
                statuses = mini_story.check_6_region_status(baas)
                index = next((i for i, available in enumerate(statuses) if available), None)
                if index is None:
                    return True
                position = ((352, 240), (931, 240), (352, 396), (931, 396), (352, 537), (931, 537))[index]
            baas.click(*position, wait_over=True)
        else:
            if family == 'main_story':
                position = next((p for p in ((728, 257), (668, 362))
                                 if main_story.check_current_plot_status(baas, p) == 'UNCLEAR'), None)
            else:
                position = module.one_detect(baas)
            if position:
                module.to_episode_info(baas, position, True)
                no_new = 0
            else:
                no_new += 1
                if no_new >= 3:
                    return True
                baas.swipe(907, 520, 907, 200, 0.5, post_sleep_time=1)
    raise PluginError('TAKEOVER_LIMIT', 'Story takeover reached its safety limit; check the game before continuing.')


def mission_label(value: str) -> tuple[int, int] | None:
    match = re.fullmatch(r'\s*(\d{1,2})\s*-\s*([1-5A])\s*', value)
    if match is None:
        return None
    return int(match[1]), 6 if match[2] == 'A' else int(match[2])


def push_current_stage(baas) -> bool:
    from core import image, picture
    from module.explore_tasks.explore_task import need_fight, extract_first_team, set_explore_task_mode
    from module.explore_tasks.task_utils import convert_team_config, employ_units, execute_grid_task, get_stage_data, to_normal_event, to_hard_event
    from module.main_story import auto_fight
    seen = set()
    empty_pages = 0
    # Establish the page identity before clicking a label or an entry button.
    page = picture.co_detect(baas, rgb_ends=['event_normal', 'event_hard'],
                             img_ends=['normal_task_task-info', 'normal_task_formation-menu'],
                             time_out=8)
    if page == 'normal_task_formation-menu':
        require(baas.config.choose_team_method == 'order', 'TEAM_PLAN_REQUIRED',
                'For an existing formation screen, select the current team in profile settings before takeover.')
        auto_fight(baas)
        to_normal_event(baas, True)
        return True
    require(page in {'event_normal', 'event_hard'}, 'UNSUPPORTED_PAGE',
            'Open the normal or hard mission list before takeover. Use the activity actions for activity pages.')
    normal = page == 'event_normal'
    navigate = to_normal_event if normal else to_hard_event
    for _ in range(60):
        if not baas.flag_run:
            return False
        baas.update_screenshot_array()
        positions = image.get_image_all_appear_position(baas, 'normal_task_enter-task-button', (1055, 191, 1201, 632), 0.8)
        candidates, distinct = [], []
        for position in sorted(positions, key=lambda point: (point[1], point[0])):
            x, y = position[:2]
            if any(abs(x - old_x) < 20 and abs(y - old_y) < 20 for old_x, old_y in distinct):
                continue
            distinct.append((x, y))
            raw = baas.ocr.get_region_res(baas, (x - 396, y - 7, x + 60, y + 33), 'en-us', 'Mission', '0123456789-A')
            label = mission_label(str(raw))
            if label and label not in seen:
                candidates.append((y, label))
        if not candidates:
            empty_pages += 1
            if empty_pages >= 3:
                require(bool(seen), 'UNRECOGNIZED_MISSIONS', 'No supported mission labels were recognized; no battles were started.')
                return True
            baas.swipe(917, 552, 917, 220, 0.2, post_sleep_time=1)
            continue
        empty_pages = 0
        y, (region, mission) = min(candidates)
        seen.add((region, mission))
        routes = {name: route for name, route in get_stage_data(region, normal).items()
                  if name == f'{region}-{mission}' or name.startswith(f'{region}-{mission}-')}
        require(bool(routes), 'UNSUPPORTED_MISSION', 'The selected mission has no supported host route.')
        from module.explore_tasks.task_utils import to_mission_info
        require(to_mission_info(baas, y), 'UNSUPPORTED_PAGE', 'The selected mission could not be opened.')
        opened = True
        for name, route in routes.items():
            if not opened:
                require(to_mission_info(baas, y), 'UNSUPPORTED_PAGE', 'The next mission route could not be opened.')
                opened = True
            if not need_fight(baas, name, normal):
                continue
            if mission != 6:
                set_explore_task_mode(baas)
            if baas.config.explore_task_use_simple_mode or mission == 6:
                picture.co_detect(baas, img_ends='normal_task_formation-menu',
                                  img_reactions={'normal_task_task-info': (946, 540), 'normal_task_task-A-info': (946, 540)},
                                  skip_first_screenshot=True, time_out=15)
                require(employ_units(baas, baas.config.choose_team_method, extract_first_team(route), convert_team_config(baas)),
                        'TEAM_PLAN_REQUIRED', 'The configured team plan cannot satisfy this mission.')
            else:
                require(execute_grid_task(baas, route), 'DEVICE_TASK_FAILED', 'The mission grid route did not complete.')
            auto_fight(baas)
            # auto_fight returns when the fight begins. Settle and reopen the
            # mission before inspecting another objective of this same stage.
            if normal:
                to_hard_event(baas, True)
                to_normal_event(baas, True)
            else:
                to_normal_event(baas, True)
                to_hard_event(baas, True)
            opened = False
        if opened:
            navigate(baas, True)
    raise PluginError('TAKEOVER_LIMIT', 'Mission takeover reached its safety limit; check the game before continuing.')
