import importlib
import os
import cv2

image_x_y_range = {

}
image_dic = {

}


def init_image_data(self):
    try:
        global image_x_y_range
        global image_dic
        self.logger.info("Start initializing image data")
        path = 'src/images/' + self.server + '/x_y_range'
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
                    if prefix in image_x_y_range:
                        image_x_y_range[prefix].update(x_y_range)
                    else:
                        image_x_y_range[prefix] = x_y_range
                    for key in x_y_range:
                        img_path = 'src/images/' + self.server + '/' + path + '/' + key + '.png'
                        if os.path.exists(img_path):
                            img = cv2.imread(img_path)
                            image_dic[prefix + '_' + key] = img
        if self.current_game_activity is not None:
            current_activity_img_data_path = 'src.images.' + self.server + '.x_y_range.activity.' \
                                             + self.current_game_activity
            data = importlib.import_module(current_activity_img_data_path)
            x_y_range = getattr(data, 'x_y_range', None)
            path = getattr(data, 'path', None)
            image_x_y_range['activity'].update(**x_y_range)
            for key in x_y_range:
                img_path = 'src/images/CN/' + path + '/' + key + '.png'
                if os.path.exists(img_path):
                    img = cv2.imread(img_path)
                    image_dic['activity_' + key] = img
        self.logger.info("Image data successfully initialized total assets : " + str(len(image_dic)))
        return True
    except Exception as e:
        self.logger.error(e)
        self.logger.error("Failed to initialize image data")
        return False
