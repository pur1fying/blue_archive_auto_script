from module.cafe_reward import invite_girl, to_cafe, to_no2_cafe, get_invitation_ticket_status


def implement(self):
    self.quick_method_to_main_page()
    to_cafe(self, True)
    self.logger.info("Start Cafe Invite")
    if get_invitation_ticket_status(self):
        invite_girl(self, 1)
    if self.server == 'JP' or self.server == 'Global' and self.config['cafe_reward_has_no2_cafe']:
        self.logger.info("Start No.2 Cafe Invite")
        to_no2_cafe(self)
        if self.config['cafe_reward_use_invitation_ticket']:
            invite_girl(self, 2)
    return True
