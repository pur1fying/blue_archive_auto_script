from module.cafe_reward import invite_girl, to_cafe, get_invitation_ticket_status, interaction_for_cafe_solve_method3


def implement(self):
    self.quick_method_to_main_page()
    to_cafe(self, True)
    self.logger.info("No.1 Cafe Invite")
    if get_invitation_ticket_status(self):
        invite_girl(self, 1)
        interaction_for_cafe_solve_method3(self)
    return True
