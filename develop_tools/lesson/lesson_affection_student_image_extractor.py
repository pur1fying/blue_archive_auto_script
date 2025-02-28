import cv2
import importlib
import os
import json

# ---------------------------------------------------- Modify these variables
image_path = 'develop_tools/lesson/example.png'
student_names = ['Natsu', 'Cherino']
server = 'CN'  # 'CN', 'JP', 'Global'
position_id = [(3, 2), (4, 3)]
# ----------------------------------------------------


save_image_path = f"src/images/{server}/lesson_affection/"
module = importlib.import_module(f"src.images.{server}.x_y_range.lesson_affection")
all_x_y_range = getattr(module, 'x_y_range')

img = cv2.imread(image_path)


def img_cut(img, x1, y1, x2, y2):
    return img[y1:y2, x1:x2]


for i in range(0, len(position_id)):
    position_id[i] = (position_id[i][0] - 1) * 3 + position_id[i][1]

_y = [256, 408, 558]
dy = 30
_x = [295, 639, 984]
dx1 = 9
dx2 = 42
dx3 = 52

cnt = 1
for y in _y:
    for x in _x:
        x_start = x
        for i in range(0, 3):
            if cnt not in position_id:
                cnt += 1
                continue
            idx = position_id.index(cnt)
            current_name = student_names[idx]
            if current_name in all_x_y_range:
                print(f'name {current_name} already exists in x_y_range')
                cnt += 1
                continue
            p = save_image_path + current_name + '.png'
            if os.path.exists(p):
                print(f'image {p} already exists')
                cnt += 1
                continue

            y1 = y
            y2 = y + dy
            x1 = x_start + i * dx3 + dx1
            x2 = x_start + i * dx3 + dx2
            img_ = img_cut(img, x1, y1, x2, y2)
            print(f'write image {p}')
            cv2.imwrite(p, img_)
            all_x_y_range[current_name] = ()
            cnt += 1

print(json.dumps(all_x_y_range, indent=4))
