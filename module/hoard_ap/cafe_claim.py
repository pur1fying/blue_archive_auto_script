"""咖啡厅「只领小时奖励」独立动作。

调度名：cafe_reward_claim
- 进咖啡厅 → 领小时奖励 → 回主页
- 不邀请、不摸头
- 囤体活跃时由计划调用；原 cafe_reward 内 collect 仍被 guard 跳过
"""

from __future__ import annotations


def implement(self) -> bool:
    # 插件级守卫：非启用/删除（工具启用与修改）→ 跳过
    try:
        from module.tools.registry import tool_available

        if not tool_available("hoard_ap"):
            try:
                self.logger.info("[囤体] 插件已停用或删除，跳过咖啡厅领奖")
            except Exception:
                pass
            return True
    except Exception:
        pass
    try:
        from module.cafe_reward import to_cafe, collect, get_cafe_earning_status

        self.to_main_page()
        to_cafe(self, True)
        if get_cafe_earning_status(self):
            self.logger.info("[囤体] 咖啡厅领小时奖励")
            collect(self)
        else:
            self.logger.info("[囤体] 咖啡厅暂无可领，不记当日已领")
            try:
                self.to_main_page()
            except Exception:
                pass
            return False
        try:
            self.to_main_page()
        except Exception:
            pass
        return True
    except Exception as e:
        try:
            self.logger.error(f"[囤体] cafe_reward_claim 失败: {e}")
        except Exception:
            pass
        return False
