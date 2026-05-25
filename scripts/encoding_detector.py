#!/usr/bin/env python3
"""
encoding_detector.py - File encoding, line ending, and format detection

Usage:
    python encoding_detector.py <file_path>

Output (JSON):
    {
        "encoding": "utf-8",           # Detected encoding
        "confidence": 0.99,            # Confidence level (0.0-1.0)
        "line_ending": "lf",           # "crlf" or "lf"
        "format_type": "double-line",   # "double-line", "single-line", or "unknown"
        "has_format_markers": true,    # Whether ★◎...◎★// pattern found
        "sample_lines": [...],         # First few lines for inspection
        "error": null                  # Error message if any
    }
"""

import sys
import json
import os
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')


def detect_encoding(file_path: str) -> tuple:
    """
    Detect file encoding.
    Returns: (encoding_name, confidence)
    """
    encodings_to_try = [
        ('utf-8', 'utf-8-sig'),
        ('shift_jis', 'shift-jis'),
        ('utf-16', 'utf-16-le', 'utf-16-be'),
        ('euc-jp', 'euc_jp'),
        ('iso-2022-jp', 'iso2022_jp'),
        ('cp932', 'ms932'),
        ('latin-1', 'iso-8859-1'),
    ]

    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read(65536)
    except Exception as e:
        return ('unknown', 0.0, str(e))

    # Check for BOM first
    if raw_data.startswith(b'\xef\xbb\xbf'):
        return ('utf-8-sig', 1.0, None)
    if raw_data.startswith(b'\xff\xfe'):
        return ('utf-16-le', 1.0, None)
    if raw_data.startswith(b'\xfe\xff'):
        return ('utf-16-be', 1.0, None)

    # Detect BOM-less UTF-16: check for alternating null bytes
    if len(raw_data) >= 20:
        le_nulls = sum(1 for i in range(0, min(100, len(raw_data)-1), 2) if raw_data[i+1] == 0)
        be_nulls = sum(1 for i in range(0, min(100, len(raw_data)-1), 2) if raw_data[i] == 0)
        # UTF-16 LE: many even-positioned (second byte) nulls, odd-positioned (first byte) never null
        if le_nulls > 10 and be_nulls == 0:
            return ('utf-16-le', 0.95, None)
        # UTF-16 BE: many odd-positioned (first byte) nulls, even-positioned (second byte) never null
        if be_nulls > 10 and le_nulls == 0:
            return ('utf-16-be', 0.95, None)

    best_encoding = 'utf-8'
    best_confidence = 0.0

    for encoding_group in encodings_to_try:
        for encoding in encoding_group:
            # Skip latin-1 in main loop (fallback only)
            if encoding.startswith('latin'):
                continue
            try:
                text = raw_data.decode(encoding)
            except (UnicodeDecodeError, LookupError):
                # Truncation at buffer boundary; retry with shortened data
                for trim in range(1, min(5, len(raw_data))):
                    try:
                        text = raw_data[:-trim].decode(encoding)
                        break
                    except (UnicodeDecodeError, LookupError):
                        continue
                else:
                    continue

            confidence = 0.9

            if b'\x00' in raw_data[:1000]:
                confidence -= 0.3

            printable_count = sum(1 for c in text if c.isprintable() or c in '\n\r\t')
            if len(text) > 0:
                printable_ratio = printable_count / len(text)
                confidence = confidence * printable_ratio

            if confidence > best_confidence:
                best_confidence = confidence
                best_encoding = encoding

            break

    # Fallback: try latin-1 only if nothing else succeeded meaningfully
    if best_confidence < 0.5:
        try:
            text = raw_data.decode('latin-1')
            confidence = 0.5
            printable_count = sum(1 for c in text if c.isprintable() or c in '\n\r\t')
            if len(text) > 0:
                printable_ratio = printable_count / len(text)
                confidence = 0.5 * printable_ratio
            if confidence > best_confidence:
                best_confidence = confidence
                best_encoding = 'latin-1'
        except Exception:
            pass

    return (best_encoding, best_confidence, None)


def detect_line_ending(file_path: str) -> str:
    """Detect line ending type (CRLF, LF, or CR)."""
    try:
        with open(file_path, 'rb') as f:
            content = f.read(10000)

        if b'\r\n' in content:
            return 'crlf'
        elif b'\n' in content:
            return 'lf'
        elif b'\r' in content:
            return 'cr'
        else:
            return 'lf'
    except Exception:
        return 'lf'


def detect_format_type(file_path: str, encoding: str) -> tuple:
    """Detect galgame text format type."""
    try:
        with open(file_path, 'r', encoding=encoding, errors='replace') as f:
            lines = f.readlines(10000)
    except Exception:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines(10000)
        except Exception:
            return ('unknown', False)

    has_source_marker = False
    has_target_marker = False

    for line in lines:
        stripped = line.strip()

        if '★◎' in stripped and '◎★//' in stripped:
            has_source_marker = True

        elif '★◎' in stripped and '◎★' in stripped and '//' not in stripped:
            has_target_marker = True

    if has_source_marker and has_target_marker:
        return ('double-line', True)
    elif has_source_marker:
        return ('single-line', True)
    else:
        return ('unknown', False)


def get_sample_lines(file_path: str, encoding: str, num_lines: int = 5) -> list:
    """Get first few lines of file for inspection."""
    try:
        with open(file_path, 'r', encoding=encoding, errors='replace') as f:
            lines = []
            for i, line in enumerate(f):
                if i >= num_lines:
                    break
                lines.append(line.rstrip('\n\r'))
            return lines
    except Exception:
        return []


def detect_file_properties(file_path: str) -> dict:
    """Main function to detect all file properties."""
    result = {
        "encoding": "unknown",
        "confidence": 0.0,
        "line_ending": "lf",
        "format_type": "unknown",
        "has_format_markers": False,
        "sample_lines": [],
        "error": None
    }

    if not os.path.isfile(file_path):
        result["error"] = f"File not found: {file_path}"
        return result

    try:
        encoding, confidence, error = detect_encoding(file_path)
        result["encoding"] = encoding
        result["confidence"] = confidence

        if error:
            result["error"] = error

        result["line_ending"] = detect_line_ending(file_path)

        format_type, has_markers = detect_format_type(file_path, encoding)
        result["format_type"] = format_type
        result["has_format_markers"] = has_markers

        result["sample_lines"] = get_sample_lines(file_path, encoding)

    except Exception as e:
        result["error"] = str(e)

    return result


def main() -> None:
    """CLI entry point: detect file encoding."""
    if len(sys.argv) < 2:
        print(json.dumps({
            "error": "Usage: python encoding_detector.py <file_path>",
            "encoding": "unknown",
            "line_ending": "lf",
            "format_type": "unknown",
            "has_format_markers": False
        }, indent=2, ensure_ascii=False))
        sys.exit(1)

    file_path = sys.argv[1]
    result = detect_file_properties(file_path)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
