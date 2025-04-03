import importlib
import os
import cv2


image_x_y_range = {

}

image_dic = {

}

initialized_image = {
    'CN': False,
    'Global_zh-tw': False,
    'Global_en-us': False,
    'Global_ko-kr': False,
    'JP': False
}


def init_image_data(self):
    try:
        global image_x_y_range
        global image_dic
        identifier = self.identifier
        if initialized_image[identifier]:
            return True
        image_dic.setdefault(identifier, {})
        image_x_y_range.setdefault(identifier, {})
        initialized_image[identifier] = True
        path = 'src/images/' + identifier + '/x_y_range'
        for file_path, child_file_name, files in os.walk(path):
            if file_path.endswith('activity'):
                continue
            for filename in files:
                if filename.endswith('py'):
                    temp = file_path.replace('\\', '.')
                    temp = temp.replace('/', '.')
                    import_name = temp + '.' + filename.split('.')[0]
                    data = importlib.import_module(import_name)
                    x_y_range = getattr(data, 'x_y_range', None)
                    path = getattr(data, 'path', None)
                    prefix = getattr(data, 'prefix', None)
                    if prefix in image_x_y_range[identifier]:
                        image_x_y_range[identifier][prefix].update(x_y_range)
                    else:
                        image_x_y_range[identifier][prefix] = x_y_range
                    for key in x_y_range:
                        img_path = 'src/images/' + identifier + '/' + path + '/' + key + '.png'
                        if os.path.exists(img_path):
                            img = cv2.imread(img_path)
                            image_dic[identifier][prefix + '_' + key] = img
        if self.current_game_activity is not None:
            current_activity_img_data_path = 'src.images.' + identifier + '.x_y_range.activity.' \
                                             + self.current_game_activity
            data = importlib.import_module(current_activity_img_data_path)
            x_y_range = getattr(data, 'x_y_range', None)
            path = getattr(data, 'path', None)
            image_x_y_range[identifier]['activity'].update(**x_y_range)
            for key in x_y_range:
                img_path = 'src/images/' + identifier + '/' + path + '/' + key + '.png'
                if os.path.exists(img_path):
                    img = cv2.imread(img_path)
                    image_dic[identifier]['activity_' + key] = img
        if self.dailyGameActivity is not None:
            current_activity_img_data_path = 'src.images.' + identifier + '.x_y_range.dailyGameActivity.' \
                                             + self.dailyGameActivity
            data = importlib.import_module(current_activity_img_data_path)
            x_y_range = getattr(data, 'x_y_range', None)
            path = getattr(data, 'path', None)
            image_x_y_range[identifier]['dailyGameActivity'].update(**x_y_range)
            for key in x_y_range:
                img_path = 'src/images/' + identifier + '/' + path + '/' + key + '.png'
                if os.path.exists(img_path):
                    img = cv2.imread(img_path)
                    image_dic[identifier]['dailyGameActivity_' + key] = img
        self.logger.info(f"Image {identifier} count : {len(image_dic[identifier])}")
        return True
    except Exception as e:
        self.logger.error(e.__str__())
        self.logger.error("Failed to initialize image data.")
        return False


def alter_img_position(self, name, point):
    global image_x_y_range
    global image_dic
    if name in image_dic[self.identifier]:
        shape = image_dic[self.identifier][name].shape
        prefix, name = name.rsplit("_", 1)
        if image_x_y_range[self.identifier][prefix][name] is not None:
            self.logger.info("Alter position of : [ " + name + " ] --> " + str(point))
            image_x_y_range[self.identifier][prefix][name] = (point[0], point[1], point[0] + shape[1], point[1] + shape[0])


def get_area(identifier, name):
    global image_x_y_range
    global image_dic
    prefix, name = name.rsplit("_", 1)
    if image_x_y_range[identifier][prefix][name] is None:
        return False
    return image_x_y_range[identifier][prefix][name]
