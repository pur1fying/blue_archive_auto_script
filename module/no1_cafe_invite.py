from datetime import datetime, timedelta, timezone

from core.utils import get_nearest_hour
from module.cafe_reward import invite_girl, to_cafe, get_invitation_ticket_status, interaction_for_cafe_solve_method3, \
    get_invitation_ticket_next_time


def implement(self):
    self.to_main_page()
    to_cafe(self, True)
    if judge_use_invitation_ticket(self, 1):
        invite_girl(self, 1)
        interaction_for_cafe_solve_method3(self)
        delay_cafe_reward_execution_time(self)
    return True


def judge_use_invitation_ticket(self, cafe_no=1):
    self.logger.info(f"Judge No.{cafe_no} Cafe Invite.")
    current_time = datetime.now(timezone.utc)
    current_time = current_time.replace(microsecond=0)
    flag = get_invitation_ticket_status(self)
    invitation_ticket_cool_time = 0
    if not flag:
        invitation_ticket_cool_time = get_invitation_ticket_next_time(self)
    invitation_ticket_next_usable_time = current_time + timedelta(seconds=invitation_ticket_cool_time)
    expected_hour = (20 if cafe_no == 1 else 8) - (self.server == 'Global' or self.server == 'JP')
    nearest_time = get_nearest_hour(expected_hour)
    self.logger.info(f"Next usable time     :{invitation_ticket_next_usable_time}")
    self.logger.info(f"Nearest expected time:{nearest_time}")
    if invitation_ticket_next_usable_time > nearest_time:
        if (invitation_ticket_next_usable_time - nearest_time).seconds < 9 * 3600:
            if flag:
                self.logger.info(f"Use Invitation Ticket.")
                return True
            else:
                self.logger.info(f"Use Invitation Ticket After Cool Down.")
                self.next_time = invitation_ticket_cool_time
    return False


def delay_cafe_reward_execution_time(self):
    self.logger.info("Refresh cafe_reward schedule.")
    self.scheduler.systole("cafe_reward", 0, True)
