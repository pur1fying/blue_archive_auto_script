import importlib
import os
import cv2

"""
    This module is used to control image used by baas.

    Rules:
    1.Image has server,group,name,position which are stored in src/image/server/x_y_range/*.py
    Example(src/image/CN/x_y_range/arena.py):

        prefix = "arena"    # group
        path = "arena"      # path of image
        x_y_range = {
            'menu': (107, 9, 162, 36)
            'edit-force': (107, 9, 162, 36)
            # name : position
        }

    Then put clipped screenshot image.
    resource/image/server/arena
    │
    ├── menu.png
    └── edit-force.png

    2. image group can contain " _ " character, but name must not.
    Reason: get_area(server, name) use rsplit.

    3. Get image
    img = image_dic[server][group_name]

    4. Get image area
    area =
    (1) image_x_y_range[server][group_name][image_name]
    (2) get_area(server, group_name)
"""

image_x_y_range = {

}

image_dic = {

}

initialized_image = {
    'CN': False,
    'Global': False,
    'JP': False
}


def init_image_data(self):
    """
    param self: baas object (load image for baas.server)
    """
    try:
        global image_x_y_range
        global image_dic
        if not initialized_image[self.server]:
            image_dic.setdefault(self.server, {})
            image_x_y_range.setdefault(self.server, {})
            initialized_image[self.server] = True
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
                        if prefix in image_x_y_range[self.server]:
                            image_x_y_range[self.server][prefix].update(x_y_range)
                        else:
                            image_x_y_range[self.server][prefix] = x_y_range
                        for key in x_y_range:
                            img_path = 'src/images/' + self.server + '/' + path + '/' + key + '.png'
                            if os.path.exists(img_path):
                                img = cv2.imread(img_path)
                                image_dic[self.server][prefix + '_' + key] = img
            if self.current_game_activity is not None:
                current_activity_img_data_path = 'src.images.' + self.server + '.x_y_range.activity.' \
                                                 + self.current_game_activity
                data = importlib.import_module(current_activity_img_data_path)
                x_y_range = getattr(data, 'x_y_range', None)
                path = getattr(data, 'path', None)
                image_x_y_range[self.server]['activity'].update(**x_y_range)
                for key in x_y_range:
                    img_path = 'src/images/' + self.server + '/' + path + '/' + key + '.png'
                    if os.path.exists(img_path):
                        img = cv2.imread(img_path)
                        image_dic[self.server]['activity_' + key] = img
            if self.dailyGameActivity is not None:
                current_activity_img_data_path = 'src.images.' + self.server + '.x_y_range.dailyGameActivity.' \
                                                 + self.dailyGameActivity
                data = importlib.import_module(current_activity_img_data_path)
                x_y_range = getattr(data, 'x_y_range', None)
                path = getattr(data, 'path', None)
                image_x_y_range[self.server]['dailyGameActivity'].update(**x_y_range)
                for key in x_y_range:
                    img_path = 'src/images/' + self.server + '/' + path + '/' + key + '.png'
                    if os.path.exists(img_path):
                        img = cv2.imread(img_path)
                        image_dic[self.server]['dailyGameActivity_' + key] = img
            return True
        else:
            return True
    except Exception as e:
        self.logger.error(e.__str__())
        self.logger.error("Failed to initialize image data")
        return False


def alter_img_position(self, name, point):
    global image_x_y_range
    global image_dic
    if name in image_dic[self.server]:
        shape = image_dic[self.server][name].shape
        module, name = name.rsplit("_", 1)
        if image_x_y_range[self.server][module][name] is not None:
            self.logger.info("Alter position of : [ " + name + " ] --> " + str(point))
            image_x_y_range[self.server][module][name] = (point[0], point[1], point[0] + shape[1], point[1] + shape[0])


def get_area(server, name):
    global image_x_y_range
    global image_dic
    module, name = name.rsplit("_", 1)
    if image_x_y_range[server][module][name] is None:
        return False
    return image_x_y_range[server][module][name]
