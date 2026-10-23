#!/usr/bin/env python3
"""Convert `swift test --enable-code-coverage` LLVM JSON to Sonar line coverage."""
import argparse
import json
from pathlib import Path
from xml.etree import ElementTree as ET


def executable_lines(segments):
    """Follow LLVM LineCoverageStats: region entries plus the wrapped count."""
    previous = (0, 0)
    for segment in segments:
        if (len(segment) != 6 or any(type(n) is not int for n in segment[:3])
                or segment[0] < 1 or segment[1] < 1 or segment[2] < 0
                or any(type(flag) is not bool for flag in segment[3:])
                or tuple(segment[:2]) < previous):
            raise ValueError('Invalid or unordered LLVM coverage segment')
        previous = tuple(segment[:2])
    lines = {}
    if not segments:
        return lines
    index = 0
    wrapped = None
    for number in range(segments[0][0], segments[-1][0] + 1):
        current = []
        while index < len(segments) and segments[index][0] == number:
            current.append(segments[index])
            index += 1
        entries = [s for s in current if s[3] and s[4] and not s[5]]
        skipped = bool(current and not current[0][3] and current[0][4])
        mapped = (not skipped and (bool(wrapped and wrapped[3]) or bool(entries)))
        mapped = mapped or any(s[3] and s[4] for s in current)
        if mapped:
            counts = [s[2] for s in entries] + ([wrapped[2]] if wrapped else [0])
            lines[number] = max(counts) > 0
        if current:
            wrapped = current[-1]
    return lines


def convert(report, root):
    if (report.get('type') != 'llvm.coverage.json.export'
            or not str(report.get('version', '')).startswith('2.')
            or not isinstance(report.get('data'), list)):
        raise ValueError('Expected LLVM coverage JSON export version 2')
    root = root.resolve()
    files = {}
    for dataset in report['data']:
        for entry in dataset['files']:
            path = Path(entry['filename'])
            path = path if path.is_absolute() else root / path
            try:
                relative = path.resolve().relative_to(root)
            except ValueError:
                continue
            if (relative.parts[:2] != ('Sources', 'PiSDK') or relative.suffix != '.swift'
                    or relative.parts[:3] == ('Sources', 'PiSDK', 'Contract')):
                continue
            lines = files.setdefault(relative.as_posix(), {})
            for number, covered in executable_lines(entry['segments']).items():
                lines[number] = lines.get(number, False) or covered
    if not any(files.values()):
        raise ValueError('No SDK executable lines found in coverage export')
    coverage = ET.Element('coverage', version='1')
    for path, lines in sorted(files.items()):
        if not lines:
            continue
        file = ET.SubElement(coverage, 'file', path=path)
        for number, covered in sorted(lines.items()):
            ET.SubElement(file, 'lineToCover', lineNumber=str(number), covered=str(covered).lower())
    ET.indent(coverage)
    return ET.tostring(coverage, encoding='unicode') + '\n'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    try:
        xml = convert(json.loads(args.input.read_text()), args.root)
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.exit(1, f'Coverage conversion failed: {error}\n')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(xml, encoding='utf-8')
    print(f'Wrote Sonar coverage to {args.output}')
