import os
import time

import cv2
import numpy as np

from core import picture, image, color


def implement(self):
    self.to_main_page()
    startGame(self)
    chooseLoop(self)
    collectDailyReward(self)
    returnToMainPage(self)
    return True


def startGame(self):
    img_possibles = {
        "dailyGameActivity_enter1": (1190, 119),
        "dailyGameActivity_enter2": (110, 169),
        "dailyGameActivity_start-game": (637, 451)
    }
    img_ends = "dailyGameActivity_game-playing-feature"
    rgb_possibles = {
        "main_page": (1195, 574),
    }
    picture.co_detect(self, None, rgb_possibles, img_ends, img_possibles, skip_first_screenshot=True)


def chooseLoop(self):
    regions = [
        [250, 73, 470, 407],
        [494, 52, 841, 422],
        [847, 65, 1107, 415]
    ]
    materialClickPosition = [
        [],
        [144, 498],
        [383, 490],
        [540, 490],
        [689, 490],
        [802, 490],
        [900, 490],
        [1130, 480],
        [1190, 582]
    ]
    personPosition = [
        [371, 354],
        [676, 366],
        [961, 353]
    ]
    possibleMaterial = []
    imgDir = "src/images/CN/dailyGameActivity/serikaSummerRamenStall/noodles"
    imgDic = {}
    for img in os.listdir(imgDir):
        material = img.split(".")[0]
        possibleMaterial.append(material)
        img = cv2.imread(imgDir + "/" + material + ".png", cv2.IMREAD_UNCHANGED)
        if img.shape[2] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            cv2.imwrite(imgDir + "/" + material + ".png", img)
        imgDic[material] = img
    startTime = time.time()
    totalTime = 115
    while time.time() - startTime < totalTime:
        self.latest_img_array = self.get_screenshot_array()
        if not image.compare_image(self, "dailyGameActivity_game-playing-feature"):
            break
        for i in range(0, 3):
            region = regions[i]
            croppedImg = self.latest_img_array[region[1]:region[3], region[0]:region[2]]
            cv2.imwrite("croppedImg.png", croppedImg)
            mostPossibleMaterial = None
            maxThreshold = 0.85
            for material in possibleMaterial:
                templateImg = imgDic[material]
                res = cv2.matchTemplate(croppedImg, templateImg, cv2.TM_SQDIFF)
                temp = np.unravel_index(res.argmin(), res.shape)
                correspondingImage = croppedImg[temp[0]:temp[0] + templateImg.shape[0], temp[1]:temp[1] + templateImg.shape[1]]
                rgb1 = color.getRegionMeanRGB(correspondingImage, 0, 0, correspondingImage.shape[1], correspondingImage.shape[0])
                rgb2 = color.getRegionMeanRGB(templateImg, 0, 0, templateImg.shape[1], templateImg.shape[0])
                if color.compareTotalRGBDiff(rgb1, rgb2, 15):
                    resMatchTemplate = cv2.matchTemplate(croppedImg, templateImg, cv2.TM_CCOEFF_NORMED)
                    maxRes = cv2.minMaxLoc(resMatchTemplate)
                    if maxRes[1] > maxThreshold:
                        mostPossibleMaterial = material
                        maxThreshold = maxRes[1]
                        if maxThreshold > 0.98:
                            break
            if mostPossibleMaterial is not None:
                self.logger.info("At Position " + str(i + 1))
                self.logger.info("Most possible material : " + mostPossibleMaterial)
                mostPossibleMaterial = mostPossibleMaterial.split("_")[0].split("-")
                for material in mostPossibleMaterial:
                    self.click(materialClickPosition[int(material)][0], materialClickPosition[int(material)][1], duration=0.1, wait_over=True)
                self.click(personPosition[i][0], personPosition[i][1], duration=0.1, wait_over=True)
                self.logger.info("Clear material")
                self.click(47, 624, duration=0.1, wait_over=True)


def collectDailyReward(self):
    img_possibles = {
        "dailyGameActivity_final-result": (634, 479),
        "dailyGameActivity_collect-reward-bright": (637, 480)
    }
    img_ends = ["dailyGameActivity_collect-reward-grey", "dailyGameActivity_daily-task-grey"]
    picture.co_detect(self, None, None, img_ends, img_possibles, skip_first_screenshot=True)


def returnToMainPage(self):
    img_possibles = {
        "dailyGameActivity_daily-task": (922, 222),
        "dailyGameActivity_final-result": (815, 471),
        "dailyGameActivity_exit": (1190, 119),
        "dailyGameActivity_start-game": (1228, 132),
        "main_page_quick-home": (1225, 31)
    }
    rgb_ends = "main_page"
    picture.co_detect(self, rgb_ends, None, None, img_possibles, skip_first_screenshot=True)
