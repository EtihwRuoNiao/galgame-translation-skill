#!/usr/bin/env python3
"""
path_resolver.py - Path resolution and file collection for galgame-translation-skill

Usage:
    python path_resolver.py <path_spec> [--output-dir <output_dir>]

Examples:
    python path_resolver.py /path/to/input/              # Directory
    python path_resolver.py /path/to/file.txt            # Single file
    python path_resolver.py "*.txt"                      # Wildcard pattern
    python path_resolver.py /path/to/input/ --output-dir /custom/output

Output:
    JSON with structure:
    {
        "input_paths": [...],      # List of input file paths
        "output_dir": "...",       # Output directory path
        "base_input_dir": "...",   # Base directory for relative structure preservation
        "files": [                 # Detailed file info
            {
                "input": "...",
                "output": "...",
                "relative": "..."  # Relative path from base_input_dir
            }
        ]
    }
"""

import os
import sys
import json
import glob
import argparse
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')


def normalize_path(path_str: str) -> str:
    """Normalize path to use forward slashes, expand user home, resolve dot paths."""
    expanded = os.path.expanduser(path_str)
    path = Path(expanded)
    if path.name in ('.', '..') or str(path) in ('.', '..'):
        path = path.resolve()
    return str(path).replace(os.sep, '/')


def is_wildcard_pattern(path_str: str) -> bool:
    """Check if path contains wildcard characters."""
    return '*' in path_str or '?' in path_str or '[' in path_str


def collect_files_from_pattern(pattern: str) -> list:
    """Collect files matching a wildcard pattern."""
    matches = glob.glob(pattern, recursive=True)
    files = [f for f in matches if os.path.isfile(f)]
    return sorted(set(files))


def collect_files_from_dir(dir_path: str) -> list:
    """Recursively collect all files from a directory."""
    dir_path = Path(dir_path)
    if not dir_path.is_dir():
        return []

    files = []
    for item in dir_path.rglob('*'):
        if item.is_file():
            files.append(str(item))
    return sorted(files)


def collect_single_file(file_path: str) -> list:
    """Validate and return single file path."""
    path = Path(file_path)
    if path.is_file():
        return [str(path)]
    return []


def determine_input_paths(path_spec: str) -> tuple:
    """
    Determine input paths based on path specification.
    Returns: (input_paths_list, base_input_dir)
    """
    normalized = normalize_path(path_spec)

    if is_wildcard_pattern(path_spec):
        files = collect_files_from_pattern(path_spec)
        base_dir = os.getcwd()
        return files, base_dir

    path = Path(normalized)

    if path.is_file():
        return [normalized], str(path.parent)

    if path.is_dir():
        files = collect_files_from_dir(normalized)
        return files, normalized

    # Try as wildcard pattern if direct match fails
    if '*' in path_spec or '?' in path_spec:
        files = collect_files_from_pattern(path_spec)
        base_dir = os.getcwd()
        return files, base_dir

    raise ValueError(f"Path not found: {path_spec}")


def generate_output_dir(input_path: str, is_dir: bool) -> str:
    """
    Generate output directory path.
    - Single file: /path/to/file.txt → /path/to/translated/
    - Directory: /path/to/folder/ → /path/to/folder-translated/
    """
    path = Path(input_path)

    if is_dir:
        parent = path.parent
        folder_name = path.name + "-translated"
        return str(parent / folder_name)
    else:
        return str(path / "translated")


def generate_file_output_path(input_file: str, base_input_dir: str, output_dir: str) -> str:
    """Generate output path for a single file, preserving directory structure."""
    input_path = Path(input_file)
    base_path = Path(base_input_dir)

    try:
        rel_path = input_path.relative_to(base_path)
    except ValueError:
        rel_path = Path(input_path.name)

    return str(Path(output_dir) / rel_path)


def resolve_paths(path_spec: str, custom_output_dir: str = None) -> dict:
    """
    Main function to resolve paths and generate file mappings.
    """
    input_files, base_input_dir = determine_input_paths(path_spec)

    if not input_files:
        raise ValueError(f"No files found for path specification: {path_spec}")

    normalized_spec = normalize_path(path_spec)
    is_dir_input = Path(normalized_spec).is_dir()

    if custom_output_dir:
        output_dir = normalize_path(custom_output_dir)
    else:
        if is_dir_input:
            output_dir = generate_output_dir(normalized_spec, is_dir=True)
        else:
            first_file_dir = str(Path(input_files[0]).parent)
            output_dir = generate_output_dir(first_file_dir, is_dir=False)

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    files_info = []
    for input_file in input_files:
        output_file = generate_file_output_path(input_file, base_input_dir, output_dir)
        files_info.append({
            "input": input_file,
            "output": output_file,
            "relative": (
                str(Path(input_file).relative_to(Path(base_input_dir)))
                if Path(input_file).is_relative_to(Path(base_input_dir))
                else Path(input_file).name
            ),
        })

    return {
        "input_paths": input_files,
        "output_dir": output_dir,
        "base_input_dir": base_input_dir,
        "is_dir_input": is_dir_input,
        "files": files_info,
        "total_files": len(files_info)
    }


def main() -> None:
    """CLI entry point: resolve file paths for translation."""
    parser = argparse.ArgumentParser(description="Path resolver for galgame-translation-skill")
    parser.add_argument("path_spec", help="Path specification (file, directory, or wildcard pattern)")
    parser.add_argument("--output-dir", "-o", help="Custom output directory (optional)")

    args = parser.parse_args()

    try:
        result = resolve_paths(args.path_spec, args.output_dir)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        error_result = {
            "error": str(e),
            "input_paths": [],
            "output_dir": "",
            "files": []
        }
        print(json.dumps(error_result, indent=2, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
