from module.cafe_reward import invite_girl, to_cafe, to_no2_cafe, get_invitation_ticket_status, interaction_for_cafe_solve_method3, get_invitation_ticket_next_time


def implement(self):
    self.quick_method_to_main_page()
    to_cafe(self, True)
    self.logger.info("No.2 Cafe Invite")
    to_no2_cafe(self)
    if get_invitation_ticket_status(self):
        invite_girl(self, 2)
        interaction_for_cafe_solve_method3(self)
    else:
        t = get_invitation_ticket_next_time(self)
        if t is not None:
            self.next_time = t
    return True
