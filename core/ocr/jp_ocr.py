from core.ocr.ppocr import utility
from core.ocr.ppocr.predict_rec import TextRecognizer
from core.ocr.ppocr.predict_det import TextDetector


class PPOCR_JP:
    def __init__(self):
        self.text_detector = None
        self.text_recognizer = None
        self.args = utility.parse_args()
        self.init_text_detector()
        self.init_text_recognizer()

    def init_text_detector(self):
        self.text_detector = TextDetector(self.args)

    def init_text_recognizer(self):
        self.text_recognizer = TextRecognizer(self.args)

    def ocr_for_single_line(self, img):
        res, _ = self.text_recognizer([img])
        return {"text": res[0][0], "score": res[0][1]}

    def ocr(self, img):
        dt_boxes, _ = self.text_detector(img)
        rectangles = []
        img_list = []
        for box in dt_boxes:
            max_x = 0
            min_x = 1280
            max_y = 0
            min_y = 720
            for i in range(4):
                max_x = max(max_x, box[i][0])
                min_x = min(min_x, box[i][0])
                max_y = max(max_y, box[i][1])
                min_y = min(min_y, box[i][1])
            upper_left = [int(min_x), int(min_y)]
            lower_right = [int(max_x), int(max_y)]
            rectangles.append((upper_left, lower_right))
        rectangles.sort(key=lambda x: x[0][1])
        for upper_left, lower_right in rectangles:
            img_list.append(img[upper_left[1]:lower_right[1], upper_left[0]:lower_right[0]])
        res, _ = self.text_recognizer(img_list)
        res_list = []
        for i in range(len(res)):
            info_dict = {
                "position": rectangles[i],
                "text": res[i][0],
                "score": res[i][1]
            }
            res_list.append(info_dict)
        return res_list
