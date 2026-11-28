import json
from pathlib import Path
import tempfile
import unittest

from tests.tasks.ocr_catalog import scan, write_inventory


class OcrCatalogTests(unittest.TestCase):
    def test_ignored_sources_variants_callbacks_and_coverage_are_included(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'service/plugins').mkdir(parents=True)
            (root / '.git/info').mkdir(parents=True)
            (root / '.git/info/exclude').write_text('/*\n')
            (root / 'service/plugins/hoard_sample.py').write_text('''
def detect(baas, main):
    if main:
        region = {'CN': (10, 20, 30, 40), 'JP': (50, 60, 70, 80)}
    else:
        region = {'CN': (11, 21, 31, 41), 'JP': (51, 61, 71, 81)}
    return baas.ocr.get_region_res(baas=baas, region=region[baas.server], log_info='Count')

def parse(read_text):
    return read_text((100, 0, 190, 45), 'title')
''')
            (root / 'module').mkdir()
            (root / 'module/legacy.py').write_text('def old(self):\n    return self.ocr.recognize_number(self.latest_img_array, (1,2,3,4), int)\n')
            (root / '.venv').mkdir()
            (root / '.venv/not_project.py').write_text('x.ocr.get_region_res(x, (1,2,3,4))')
            inventory = scan(root)
            calls = inventory['calls']
            self.assertEqual(inventory['python_files_scanned'], 2)
            self.assertEqual(len(calls), 2)
            current = next(c for c in calls if c['method'] == 'get_region_res')
            self.assertEqual(len(current['coordinate_bindings']), 2)
            self.assertEqual(current['coordinate_bindings'][0]['conditions'], ['main'])
            self.assertEqual(current['coordinate_bindings'][1]['conditions'], ['not (main)'])
            self.assertEqual(len(inventory['coordinate_helpers']), 1)
            cases = [{'case_id': 'case-1', 'ocr_evidence': {'groups': [{'annotated': 'one.png', 'calls': [
                {'source': {'file': current['file'], 'line': current['line']}, 'label': 'Count'}]}]}}]
            result = write_inventory(root / 'report', inventory, cases)
            self.assertEqual({c['method']: c['coverage'] for c in result['calls']},
                             {'get_region_res': 'observed', 'recognize_number': 'not_observed'})
            self.assertIn('Legacy recognize_number', json.dumps(result))

    def test_parse_failure_and_comments_are_not_reported_as_real_calls(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'comment.py').write_text('# x.ocr.get_region_res(x, (1,2,3,4))\n')
            (root / 'broken.py').write_text('def invalid(:')
            result = scan(root)
            self.assertEqual(result['calls'], [])
            self.assertEqual(len(result['parse_errors']), 1)


if __name__ == '__main__':
    unittest.main()
