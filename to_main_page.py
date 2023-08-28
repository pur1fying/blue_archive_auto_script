from get_location import Location
import log


def pd(template, t):
    for i in range(0, len(template)):
        if t == template[i]:
            return True
    return False


class to_main_pg(Location):

    def to_main(self):
        while 1:
            lo = self.return_location()
            if lo == "main_page":
                return
            elif pd(["log_in", "sign_up", "click_forward"], lo):
                self.device.click(1, 1)
                log.o_p("click anywhere", 1)
            elif lo == "notice":
                self.clicker("src/notice/notice.png")
            elif lo == "cafe_notice1":
                self.clicker("src/cafe/cafenotice1.png")
            elif pd(["UNKNOWN UI PAGE", "mail", "group", "shop", "schedule", "create", "location_select",
                          "request_select", "road", "railway", "church", "operational_area", "task"], lo):
                self.clicker("src/common_button/back.png")
            elif pd(["task_information"], lo):
                self.clicker("src/common_button/cross1.png")


if __name__ == '__main__':
    ins = to_main_pg()
    ins.to_main()
