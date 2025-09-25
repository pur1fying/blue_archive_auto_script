import cv2
import os

def main():
    server_list = ["CN", "Global", "JP"]
    server = server_list[int(input("Select server (1:CN/2:Global/3:JP):"))-1]
    image_path = input("Enter image path:").replace("\"", "").replace("\'", "")
    if not os.path.isfile(image_path):
        raise FileNotFoundError("Image does not exist")

    image = cv2.imread(image_path)

    # resize to 1280x720
    image = cv2.resize(image, (1280, 720))

    # capture entry 1 starting from (36,490) size 295x104
    entry_1 = image[490:594, 36:331]
    cv2.imwrite(f"../module/activities/activity_data/{server}_event_entry_1.png", entry_1)

    # capture entry 2 starting from (1158,166) size 70x70
    entry_2 = image[166:236, 1158:1228]
    cv2.imwrite(f"../module/activities/activity_data/{server}_event_entry_2.png", entry_2)
    print(f"Images saved to module/activities/activity_data/{server}_event_entry_1.png and {server}_event_entry_2.png")

if __name__ == '__main__':
    main()
