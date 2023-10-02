import cv2
import definemytime
import os
import ocr
import numpy as np
import random

img1 = cv2.imread("test_pictures_for_common_fight_solve/3.png")
#print(img1.shape)
#cv2.imshow("Image",img1)
#edge = cv2.Canny(img1, 200, 100)
kernel = (5,5)
#print(ocr.ocr_character().img_ocr(edge))
#edge = cv2.dilate(edge,kernel,iterations=1)
edge = img1
mean = 0
stddev = 2
noise = np.random.normal(mean,stddev,edge.shape).astype(np.uint8)
edge = cv2.add(edge,noise)
edge1 = cv2.GaussianBlur(edge,kernel,2)
edge2 = cv2.blur(edge,(3,3))
cv2.imshow("edge", edge)
cv2.imshow("edge1", edge1)
cv2.imshow("edge2", edge2)

cv2.waitKey(0)
cv2.destroyAllWindows()
t = definemytime.my_time()
path = os.path.join("test_pictures_for_common_fight_solve",t.return_current_time()+".jpg")
cv2.imwrite(path,edge)
