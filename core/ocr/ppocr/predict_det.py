# Copyright (c) 2020 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import copy
import time
import numpy as np
import core.ocr.ppocr.utility as utility
from core.ocr.ppocr.db_postprocess import DBPostProcess
from core.ocr.ppocr.operators import ToCHWImage, NormalizeImage, KeepKeys, DetResizeForTest


def create_operators(op_param_list, global_config=None):
    """
    create operators based on the config

    Args:
        params(list): a dict list, used to create some operators
    """
    assert isinstance(op_param_list, list), ('operator config should be a list')
    ops = []
    for operator in op_param_list:
        assert isinstance(operator,
                          dict) and len(operator) == 1, "yaml format error"
        op_name = list(operator)[0]
        param = {} if operator[op_name] is None else operator[op_name]
        if global_config is not None:
            param.update(global_config)
        op = eval(op_name)(**param)
        ops.append(op)
    return ops


def transform(data, ops=None):
    """ transform """
    if ops is None:
        ops = []
    for op in ops:
        data = op(data)
    return data


class TextDetector(object):
    def __init__(self, args):
        self.args = args
        self.det_algorithm = args.det_algorithm
        pre_process_list = [{
            'DetResizeForTest': {
                'limit_side_len': args.det_limit_side_len,
                'limit_type': args.det_limit_type,
            }
        }, {
            'NormalizeImage': {
                'std': [0.229, 0.224, 0.225],
                'mean': [0.485, 0.456, 0.406],
                'scale': '1./255.',
                'order': 'hwc'
            }
        }, {
            'ToCHWImage': None
        }, {
            'KeepKeys': {
                'keep_keys': ['image', 'shape']
            }
        }]
        postprocess_params = {}
        postprocess_params['name'] = 'DBPostProcess'
        postprocess_params["thresh"] = args.det_db_thresh
        postprocess_params["box_thresh"] = args.det_db_box_thresh
        postprocess_params["max_candidates"] = 1000
        postprocess_params["unclip_ratio"] = args.det_db_unclip_ratio
        postprocess_params["use_dilation"] = args.use_dilation
        postprocess_params["score_mode"] = args.det_db_score_mode
        postprocess_params["box_type"] = args.det_box_type

        self.preprocess_op = create_operators(pre_process_list)
        config = copy.deepcopy(postprocess_params)
        config.pop("name")
        self.postprocess_op = DBPostProcess(**config)
        self.predictor, self.input_tensor, self.output_tensors, self.config = utility.create_predictor(
            args, 'det')
        self.preprocess_op = create_operators(pre_process_list)

    def order_points_clockwise(self, pts):
        rect = np.zeros((4, 2), dtype="float32")
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        tmp = np.delete(pts, (np.argmin(s), np.argmax(s)), axis=0)
        diff = np.diff(np.array(tmp), axis=1)
        rect[1] = tmp[np.argmin(diff)]
        rect[3] = tmp[np.argmax(diff)]
        return rect

    def clip_det_res(self, points, img_height, img_width):
        for pno in range(points.shape[0]):
            points[pno, 0] = int(min(max(points[pno, 0], 0), img_width - 1))
            points[pno, 1] = int(min(max(points[pno, 1], 0), img_height - 1))
        return points

    def filter_tag_det_res(self, dt_boxes, image_shape):
        img_height, img_width = image_shape[0:2]
        dt_boxes_new = []
        for box in dt_boxes:
            if type(box) is list:
                box = np.array(box)
            box = self.order_points_clockwise(box)
            box = self.clip_det_res(box, img_height, img_width)
            rect_width = int(np.linalg.norm(box[0] - box[1]))
            rect_height = int(np.linalg.norm(box[0] - box[3]))
            if rect_width <= 3 or rect_height <= 3:
                continue
            dt_boxes_new.append(box)
        dt_boxes = np.array(dt_boxes_new)
        return dt_boxes

    def filter_tag_det_res_only_clip(self, dt_boxes, image_shape):
        img_height, img_width = image_shape[0:2]
        dt_boxes_new = []
        for box in dt_boxes:
            if type(box) is list:
                box = np.array(box)
            box = self.clip_det_res(box, img_height, img_width)
            dt_boxes_new.append(box)
        dt_boxes = np.array(dt_boxes_new)
        return dt_boxes

    def __call__(self, img):
        ori_im = img.copy()
        data = {'image': img}

        st = time.time()

        if self.args.benchmark:
            self.autolog.times.start()

        data = transform(data, self.preprocess_op)
        img, shape_list = data
        if img is None:
            return None, 0
        img = np.expand_dims(img, axis=0)
        shape_list = np.expand_dims(shape_list, axis=0)
        img = img.copy()

        self.input_tensor.copy_from_cpu(img)
        self.predictor.run()
        outputs = []
        for output_tensor in self.output_tensors:
            output = output_tensor.copy_to_cpu()
            outputs.append(output)

        preds = {}
        if self.det_algorithm == "EAST":
            preds['f_geo'] = outputs[0]
            preds['f_score'] = outputs[1]
        elif self.det_algorithm == 'SAST':
            preds['f_border'] = outputs[0]
            preds['f_score'] = outputs[1]
            preds['f_tco'] = outputs[2]
            preds['f_tvo'] = outputs[3]
        elif self.det_algorithm in ['DB', 'PSE', 'DB++']:
            preds['maps'] = outputs[0]
        elif self.det_algorithm == 'FCE':
            for i, output in enumerate(outputs):
                preds['level_{}'.format(i)] = output
        elif self.det_algorithm == "CT":
            preds['maps'] = outputs[0]
            preds['score'] = outputs[1]
        else:
            raise NotImplementedError

        post_result = self.postprocess_op(preds, shape_list)
        dt_boxes = post_result[0]['points']

        if self.args.det_box_type == 'poly':
            dt_boxes = self.filter_tag_det_res_only_clip(dt_boxes, ori_im.shape)
        else:
            dt_boxes = self.filter_tag_det_res(dt_boxes, ori_im.shape)

        if self.args.benchmark:
            self.autolog.times.end(stamp=True)
        et = time.time()
        return dt_boxes, et - st
