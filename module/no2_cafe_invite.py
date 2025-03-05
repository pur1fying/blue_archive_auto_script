from module.cafe_reward import invite_girl, to_cafe, to_no2_cafe, interaction_for_cafe_solve_method3
from module.no1_cafe_invite import judge_use_invitation_ticket, delay_cafe_reward_execution_time


def implement(self):
    self.to_main_page()
    to_cafe(self, True)
    to_no2_cafe(self)
    if judge_use_invitation_ticket(self, 2):
        invite_girl(self, 2)
        interaction_for_cafe_solve_method3(self)
        delay_cafe_reward_execution_time(self)
    return True
