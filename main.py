import uiautomator2 as u2
import definemytime
import os
import log
import time


class loop(get_location):
main_activity = ["schedule", "energy_clear", "cafe", "collect_daily_reward", "momo_talk", "create", "story", "combat_power_fight", "arena", "rewarded_task"]


for i in range(0,len(main_activity)):
    activity_status[i] = 0
# url = "com.RoamingStar.BlueArchive/com.yostar.sdk.bridge.YoStarUnityPlayerActivity"

package_name='com.RoamingStar.BlueArchive'
device = u2.connect()
device.screen_on = True
device.press("volume_mute")

log.o_p("Screen Size  " + str(device.window_size()), 1)

# device(text='蔚蓝档案').click()

screen_size = device.info["displaySizeDpX"], device.info["displaySizeDpY"]
device.app_start(package_name)
time.sleep(10)

screenshot = device.screenshot()
save_folder = "logs"
t = mytime.mytime().return_current_time()
file_name = t + ".jpg"
os.makedirs(save_folder, exist_ok=True)
save_path = os.path.join(save_folder, file_name)
screenshot.save(save_path)
log.o_p("screenshot saved", 1)

device.app_stop(package_name)
