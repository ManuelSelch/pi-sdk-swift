"""Regression tests for SwiftPM LLVM coverage conversion."""
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from coverage_to_sonar import convert


class CoverageTests(unittest.TestCase):
    root = Path('/checkout')

    def report(self, segments, filename='Sources/PiSDK/Example.swift'):
        return {'type': 'llvm.coverage.json.export', 'version': '2.0.1', 'data': [
            {'files': [{'filename': str(self.root / filename), 'segments': segments}]}]}

    def lines(self, report):
        xml = ET.fromstring(convert(report, self.root))
        return {int(line.attrib['lineNumber']): line.attrib['covered']
                for line in xml.findall('file/lineToCover')}

    def test_covered_uncovered_and_non_executable_lines(self):
        report = self.report([
            [2, 1, 3, True, True, False], [4, 1, 0, True, True, False],
            [5, 2, 0, False, False, False]])
        self.assertEqual(self.lines(report), {2: 'true', 3: 'true', 4: 'true', 5: 'false'})

    def test_regions_on_same_line_merge_without_losing_a_hit(self):
        report = self.report([
            [1, 2, 0, True, True, False], [1, 5, 3, True, True, False],
            [1, 8, 0, True, True, False], [1, 10, 0, False, False, False]])
        self.assertEqual(self.lines(report), {1: 'true'})

    def test_gap_entries_do_not_override_line_counts(self):
        report = self.report([
            [1, 2, 0, True, True, False], [1, 4, 2, True, True, True],
            [1, 6, 0, False, False, False]])
        self.assertEqual(self.lines(report), {1: 'false'})

    def test_skipped_region_does_not_inherit_wrapped_count(self):
        report = self.report([
            [1, 2, 2, True, True, False], [2, 1, 0, False, True, False],
            [4, 1, 1, True, True, False], [4, 2, 0, False, False, False]])
        self.assertEqual(self.lines(report), {1: 'true', 4: 'true'})

    def test_duplicate_file_entries_merge_coverage(self):
        report = self.report([[2, 1, 0, True, True, False], [2, 4, 0, False, False, False]])
        report['data'] += self.report([
            [2, 1, 8, True, True, False], [2, 4, 0, False, False, False]])['data']
        self.assertEqual(self.lines(report), {2: 'true'})

    def test_xml_escapes_filenames_and_uses_relative_paths(self):
        report = self.report([[1, 1, 1, True, True, False], [1, 2, 0, False, False, False]],
                             'Sources/PiSDK/A&B.swift')
        xml = convert(report, self.root)
        self.assertIn('A&amp;B.swift', xml)
        self.assertEqual(ET.fromstring(xml).find('file').attrib['path'], 'Sources/PiSDK/A&B.swift')

    def test_ignores_files_outside_sdk_and_contract(self):
        report = self.report([[1, 1, 1, True, True, False], [1, 2, 0, False, False, False]])
        for filename in ['Tests/Test.swift', 'experiments/Probe.swift', '../Elsewhere.swift',
                         'Sources/PiSDK/Contract/Generated.swift']:
            report['data'] += self.report([], filename)['data']
        self.assertEqual(len(ET.fromstring(convert(report, self.root)).findall('file')), 1)

    def test_rejects_missing_or_unsupported_data(self):
        for report in [{}, {'type': 'other', 'data': []}, self.report([])]:
            with self.subTest(report=report), self.assertRaises(ValueError):
                convert(report, self.root)

    def test_rejects_invalid_segments(self):
        for segments in [[[1]], [[0, 1, 1, True, True, False]],
                         [[2, 1, 1, True, True, False], [1, 1, 0, False, False, False]]]:
            with self.subTest(segments=segments), self.assertRaises(ValueError):
                convert(self.report(segments), self.root)


if __name__ == '__main__':
    unittest.main()
