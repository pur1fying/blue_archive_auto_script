from module.cafe_reward import invite_girl, to_cafe, get_invitation_ticket_status, interaction_for_cafe_solve_method3, get_invitation_ticket_next_time


def implement(self):
    self.quick_method_to_main_page()
    to_cafe(self, True)
    self.logger.info("No.1 Cafe Invite")
    if get_invitation_ticket_status(self):
        invite_girl(self, 1)
        interaction_for_cafe_solve_method3(self)
    else:
        t = get_invitation_ticket_next_time(self)
        if t is not None:
            self.next_time = t
    return True
