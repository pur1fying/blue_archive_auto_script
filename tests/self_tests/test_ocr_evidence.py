import json
from pathlib import Path
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
import unittest

import cv2
import numpy as np

from core.ocr.ocr import Baas_ocr
from tests.runner.evidence import Recorder
from tests.runner.executor import cases_for
from tests.runner.model import Job
from tests.runner.report import write_report
from tests.support.ocr_evidence import OcrObserver


class OcrEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.cases = cases_for([Job('cn', ('lesson',)), Job('jppc', ('lesson',))])
        self.recorder = Recorder(self.root, self.cases)
        self.logger = SimpleNamespace(info=lambda *a: None, error=lambda *a: None)
        self.ocr = Baas_ocr.__new__(Baas_ocr)
        self.ocr.logger = self.logger
        self.on_call = lambda: None

        def recognize(*args, **kwargs):
            self.on_call()
            return SimpleNamespace(status_code=200, text=json.dumps({'text': '123', 'char_scores': [1, 1, 1], 'time': 1}))

        self.ocr.client = SimpleNamespace(ocr_for_single_line=recognize, ocr=recognize)
        self.observer = OcrObserver(self.ocr, self.recorder, self.root).install()
        self.baas = self.session('cn', np.full((720, 1280, 3), 80, dtype=np.uint8))

    def session(self, config, frame):
        baas = SimpleNamespace(latest_img_array=frame, ratio=frame.shape[1] / 1280, logger=self.logger,
                               ocr_img_pass_method=1, shared_memory_name='')
        self.observer.register(config, baas)
        case = next(c for c in self.cases if c['config_id'] == config)
        self.recorder.bind(config, case['case_id'])
        return baas

    def tearDown(self):
        self.observer.close()
        self.recorder.close()
        self.temp.cleanup()

    def finish(self, index=0):
        self.recorder.queue.join()
        return self.cases[index]['ocr_evidence']

    def test_three_regions_share_original_720p_frame(self):
        original = self.baas.latest_img_array.copy()
        for name, region in [('AP', (485, 23, 586, 54)), ('Credit Points', (699, 20, 832, 52)), ('Pyroxene', (871, 25, 967, 52))]:
            result = self.ocr.get_region_res(self.baas, region, log_info=name)
            self.assertEqual(result, '123')
        evidence = self.finish()
        self.assertEqual(evidence['calls'], 3)
        self.assertEqual(len(evidence['groups']), 1)
        group = evidence['groups'][0]
        self.assertEqual([c['label'] for c in group['calls']], ['AP', 'Credit Points', 'Pyroxene'])
        self.assertTrue(np.array_equal(cv2.imread(str(self.root / group['original'])), original))
        annotated = cv2.imread(str(self.root / group['annotated']))
        self.assertEqual(annotated.shape, (720, 1280, 3))
        for call in group['calls']:
            x, y, _, _ = call['display_region']
            self.assertFalse(np.array_equal(annotated[y, x], original[y, x]))
        self.assertTrue(np.array_equal(self.baas.latest_img_array, original))
        write_report(self.root, {'cases': self.cases})
        page = (self.root / 'report.html').read_text(encoding='utf-8')
        self.assertIn('OCR regions: captured', page)
        self.assertIn('Credit Points', page)

    def test_frame_is_copied_before_ocr_can_change_latest_image(self):
        self.on_call = lambda: self.baas.latest_img_array.fill(190)
        self.ocr.get_region_res(self.baas, (0, 0, 100, 100), log_info='AP')
        group = self.finish()['groups'][0]
        self.assertEqual(int(cv2.imread(str(self.root / group['original']))[0, 0, 0]), 80)

    def test_new_frame_is_not_merged_with_previous_scene(self):
        self.ocr.get_region_res(self.baas, (0, 0, 100, 100), log_info='AP')
        self.baas.latest_img_array[:] = 150
        self.ocr.get_region_res(self.baas, (0, 0, 100, 100), log_info='AP')
        self.assertEqual(len(self.finish()['groups']), 2)

    def test_numpy_dynamic_coordinates_remain_numeric_and_report_serializable(self):
        region = tuple(np.int64(v) for v in (691, 212, 751, 245))
        self.ocr.get_region_res(self.baas, region, log_info='Dynamic task region')
        evidence = self.finish()
        coords = evidence['groups'][0]['calls'][0]['requested_region']
        self.assertEqual(coords, [691, 212, 751, 245])
        self.assertTrue(all(type(v) is int for v in coords))
        write_report(self.root, {'cases': self.cases, 'measurement': np.int64(3)})
        saved = json.loads((self.root / 'result.json').read_text(encoding='utf-8'))
        self.assertEqual(saved['measurement'], 3)

    def test_high_resolution_original_is_preserved_and_boxes_are_scaled(self):
        self.baas.latest_img_array = np.full((1440, 2560, 3), 80, dtype=np.uint8)
        self.baas.ratio = 2
        self.ocr.get_region_res(self.baas, (100, 50, 200, 90), log_info='AP')
        group = self.finish()['groups'][0]
        self.assertEqual(group['calls'][0]['effective_source_region'], [200, 100, 400, 180])
        self.assertEqual(group['calls'][0]['display_region'], [100, 50, 200, 90])
        self.assertTrue(group['resized_for_display'])
        self.assertEqual(cv2.imread(str(self.root / group['original'])).shape[:2], (1440, 2560))

    def test_direct_crop_view_is_located_but_transformed_crop_is_missing(self):
        crop = self.baas.latest_img_array[20:40, 100:200]
        self.ocr.ocr_for_single_line('en-us', 'Direct view', crop)
        self.ocr.ocr_for_single_line('en-us', 'Detached input', crop.copy())
        evidence = self.finish()
        self.assertEqual(evidence['calls'], 2)
        self.assertEqual(evidence['missing'], 1)
        self.assertEqual(evidence['status'], 'incomplete')
        self.assertEqual(evidence['groups'][0]['calls'][0]['source_region'], [100, 20, 200, 40])

    def test_exception_and_result_are_unchanged(self):
        error = RuntimeError('OCR transport unavailable')
        def fail():
            raise error
        self.on_call = fail
        with self.assertRaises(RuntimeError) as caught:
            self.ocr.get_region_res(self.baas, (100, 20, 200, 40), log_info='Failing OCR')
        self.assertIs(caught.exception, error)
        call = self.finish()['groups'][0]['calls'][0]
        self.assertEqual(call['error']['type'], 'RuntimeError')

    def test_parallel_configs_keep_their_own_frame_and_labels(self):
        other = self.session('jppc', np.full((720, 1280, 3), 170, dtype=np.uint8))
        gate = threading.Barrier(2)
        self.on_call = lambda: gate.wait(timeout=2)
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(self.ocr.get_region_res, b, (10, 10, 100, 40), log_info=name)
                       for b, name in [(self.baas, 'CN AP'), (other, 'JP AP')]]
            self.assertEqual([f.result(timeout=3) for f in futures], ['123', '123'])
        self.assertEqual(self.finish(0)['groups'][0]['calls'][0]['label'], 'CN AP')
        self.assertEqual(self.finish(1)['groups'][0]['calls'][0]['label'], 'JP AP')

    def test_integer_and_raw_apis_do_not_duplicate_nested_calls(self):
        self.assertEqual(self.ocr.recognize_int(self.baas, (10, 10, 100, 40), 'Count'), 123)
        result = self.ocr.get_region_raw_res(self.baas.latest_img_array, (10, 10, 100, 40))
        self.assertEqual(json.loads(result)['text'], '123')
        self.assertEqual(self.finish()['calls'], 2)


if __name__ == '__main__':
    unittest.main()
