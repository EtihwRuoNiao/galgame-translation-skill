#!/usr/bin/env python3
"""
normalize_output.py — Post-process translation output to fix \n expansion.

When translation sub-agents write dual-line format files, they sometimes
convert literal \n escape sequences into actual newlines, breaking the
3-line-per-entry structure (address, source//, target).

This script detects and repairs such files by:
1. Reading the original file to get the correct entry structure
2. Scanning the output file for target lines whose text was split across
   multiple physical lines (expanded \n)
3. Joining those lines back into single lines with literal \n

Usage:
    python normalize_output.py <original_dir> <output_dir>

Output:
    Files in <output_dir> are fixed in-place.
    Prints status for each file processed.
"""

import os
import sys
import json
import argparse

sys.stdout.reconfigure(encoding='utf-8')


def normalize_file(orig_path: str, out_path: str) -> dict:
    """Normalize a single output file to match the original line structure."""
    result = {"file": os.path.basename(out_path), "status": "ok", "entries_fixed": 0}

    # Read original file and detect EOL + encoding
    with open(orig_path, 'rb') as f:
        raw = f.read()
    if b'\r\n' in raw:
        eol_str = '\r\n'
    elif b'\r' in raw:
        eol_str = '\r'
    else:
        eol_str = '\n'
    for enc in ('utf-8', 'shift_jis', 'cp932', 'utf-16'):
        try:
            text = raw.decode(enc)
            break
        except (UnicodeDecodeError, LookupError):
            continue
    else:
        text = raw.decode('utf-8', errors='replace')
    orig_lines = text.split(eol_str)
    if orig_lines and orig_lines[-1] == '':
        has_trail_eol = True
        orig_lines = orig_lines[:-1]
    else:
        has_trail_eol = False

    # Read output file
    with open(out_path, 'r', encoding='utf-8') as f:
        out_raw = f.read()
    out_lines = out_raw.splitlines()
    if out_lines and out_lines[-1] == '':
        out_lines = out_lines[:-1]

    new_out = []
    out_i = 0

    for line in orig_lines:
        stripped = line.strip()

        if stripped == '':
            new_out.append('')
            if out_i < len(out_lines) and out_lines[out_i].strip() == '':
                out_i += 1
            continue

        if line.startswith('#0x'):
            new_out.append(line)
            if out_i < len(out_lines):
                out_i += 1
            continue

        if '★◎' in line and '◎★//' in line:
            if out_i < len(out_lines) and '★◎' in out_lines[out_i] and '◎★//' in out_lines[out_i]:
                new_out.append(out_lines[out_i])
            else:
                new_out.append(line)
            out_i += 1
            continue

        if '★◎' in line and '◎★' in line and '//' not in line:
            prefix = line.split('◎★')[0] + '◎★'
            orig_content = line[len(prefix):]

            trans_parts = []
            if out_i < len(out_lines) and '★◎' in out_lines[out_i] and '◎★' in out_lines[out_i] and '//' not in out_lines[out_i]:
                p_end = out_lines[out_i].index('◎★') + 2
                remaining = out_lines[out_i][p_end:]
                if remaining.strip():
                    trans_parts.append(remaining)
                out_i += 1

                while (out_i < len(out_lines) and
                       out_lines[out_i].strip() != '' and
                       not out_lines[out_i].startswith('#0x') and
                       '★◎' not in out_lines[out_i]):
                    trans_parts.append(out_lines[out_i].strip())
                    out_i += 1

            if trans_parts:
                trans_text = '\\n'.join(trans_parts)
            else:
                trans_text = orig_content

            new_out.append(prefix + trans_text)
            result["entries_fixed"] += 1
            continue

        new_out.append(line)
        if out_i < len(out_lines):
            out_i += 1

    result_lines = eol_str.join(new_out)
    if has_trail_eol:
        result_lines += eol_str

    with open(out_path, 'wb') as f:
        f.write(result_lines.encode('utf-8'))

    # Verify
    final_count = len(result_lines.split(eol_str))
    if final_count - (1 if has_trail_eol else 0) == len(orig_lines):
        result["status"] = "ok"
    else:
        result["status"] = f"line_count_mismatch"

    return result


def collect_files(input_dir: str, output_dir: str) -> list:
    """Collect matching file pairs from input and output directories."""
    pairs = []
    if not os.path.isdir(output_dir):
        return pairs
    for fname in os.listdir(output_dir):
        in_path = os.path.join(input_dir, fname)
        out_path = os.path.join(output_dir, fname)
        if os.path.isfile(in_path) and os.path.isfile(out_path):
            pairs.append((in_path, out_path))
    return sorted(pairs)


def main() -> None:
    """CLI entry point: normalize translated output."""
    parser = argparse.ArgumentParser(description="Normalize translation output line structure")
    parser.add_argument("input_dir", help="Directory with original Japanese files")
    parser.add_argument("output_dir", help="Directory with translated output files")

    args = parser.parse_args()

    pairs = collect_files(args.input_dir, args.output_dir)
    if not pairs:
        print(json.dumps({"error": f"No file pairs found between {args.input_dir} and {args.output_dir}"}))
        sys.exit(1)

    results = []
    for orig, out in pairs:
        r = normalize_file(orig, out)
        results.append(r)

    total_fixed = sum(r["entries_fixed"] for r in results)
    failed = [r for r in results if r["status"] != "ok"]

    summary = {
        "files_processed": len(results),
        "total_entries_fixed": total_fixed,
        "ok": len(results) - len(failed),
        "failed": len(failed)
    }

    print(json.dumps({
        "summary": summary,
        "details": results
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
