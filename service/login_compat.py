"""Bounded recovery when a CN service task is returned to the login screen."""

from __future__ import annotations

import time
from dataclasses import dataclass
from functools import wraps
from typing import Optional


LOGIN_RECOVERY_TIMEOUT = 90.0
_STATE_ATTRIBUTE = "_baas_service_login_recovery"


@dataclass
class _RecoveryState:
    attempts: int = 0
    recovering: bool = False
    deadline: Optional[float] = None
    recovered: bool = False


def install_login_compat() -> None:
    """Reuse task retry and home navigation without altering legacy GUI code."""
    from core import color, image, picture
    from core.Baas_thread import Baas_thread
    from core.exception import FunctionCallTimeout, PackageIncorrect, RequestHumanTakeOver

    original_solve = Baas_thread.solve
    if getattr(original_solve, "_baas_login_session_compat", False):
        return
    original_popups = picture.deal_with_pop_ups
    original_screenshot = Baas_thread.update_screenshot_array
    original_timeout = Baas_thread.deal_with_func_call_timeout

    @wraps(original_solve)
    def solve(context, *args, **kwargs):
        if context.identifier != "CN" or not context.is_android_device:
            return original_solve(context, *args, **kwargs)
        previous = getattr(context, _STATE_ATTRIBUTE, None)
        if previous is not None:
            return original_solve(context, *args, **kwargs)
        setattr(context, _STATE_ATTRIBUTE, _RecoveryState())
        try:
            return original_solve(context, *args, **kwargs)
        finally:
            delattr(context, _STATE_ATTRIBUTE)

    def check_recovery(context, state):
        if not context.flag_run:
            raise RequestHumanTakeOver("Login recovery cancelled by user.")
        if state.deadline is not None and time.monotonic() >= state.deadline:
            raise RuntimeError(
                "Login session recovery failed: home was not reached within 90 seconds; "
                "stopping this task instead of waiting for its normal 600-second timeout."
            )

    @wraps(original_screenshot)
    def update_screenshot_array(context, *args, **kwargs):
        state = getattr(context, _STATE_ATTRIBUTE, None)
        if state is not None and state.recovering:
            check_recovery(context, state)
        result = original_screenshot(context, *args, **kwargs)
        if state is not None and state.recovering:
            check_recovery(context, state)
        return result

    @wraps(original_popups)
    def deal_with_pop_ups(context, *args, **kwargs):
        state = getattr(context, _STATE_ATTRIBUTE, None)
        # co_detect handles its own reactions before common popups. A task which
        # already handles the login feature therefore keeps its existing flow.
        if (state is None or state.recovering or context.identifier != "CN"
                or not context.is_android_device
                or not image.compare_image(context, "main_page_login-feature", threshold=0.9, rgb_diff=12)):
            return original_popups(context, *args, **kwargs)
        if not context.flag_run:
            raise RequestHumanTakeOver("Login recovery cancelled by user.")
        if state.attempts >= 1:
            raise RuntimeError(
                "Login session recovery failed: the game returned to the login screen "
                "again during the same task; automatic recovery is limited to one attempt."
            )
        state.attempts += 1
        state.recovering = True
        state.deadline = time.monotonic() + LOGIN_RECOVERY_TIMEOUT
        context.logger.warning(
            "Game returned to the login screen during a task. "
            "Recovering the session once, with a 90-second limit."
        )
        try:
            context.to_main_page()
            check_recovery(context, state)
            if not color.match_rgb_feature(context, "main_page"):
                raise RuntimeError("Login session recovery failed: navigation did not reach home.")
        except FunctionCallTimeout as error:
            raise RuntimeError("Login session recovery failed: home navigation timed out.") from error
        except PackageIncorrect as error:
            raise RuntimeError(
                "Login session recovery failed: the foreground app changed during home navigation."
            ) from error
        finally:
            state.recovering = False
            state.deadline = None
        state.recovered = True
        context.logger.info("Login session recovered; retrying the current task from its entry point.")
        # The existing solve() catches this at the task boundary and retries the
        # complete task. Do not continue a half-finished stage after navigating home.
        raise FunctionCallTimeout("Login session recovered; retry the current task.")

    @wraps(original_timeout)
    def deal_with_func_call_timeout(context, *args, **kwargs):
        state = getattr(context, _STATE_ATTRIBUTE, None)
        if state is not None and state.recovered:
            state.recovered = False
            return True
        return original_timeout(context, *args, **kwargs)

    solve._baas_login_session_compat = True
    Baas_thread.solve = solve
    Baas_thread.update_screenshot_array = update_screenshot_array
    Baas_thread.deal_with_func_call_timeout = deal_with_func_call_timeout
    picture.deal_with_pop_ups = deal_with_pop_ups
