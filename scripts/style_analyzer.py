#!/usr/bin/env python3
"""
style_analyzer.py — Style profile cache management for galgame-translation-skill

Subcommands:
    check   Verify cache validity against current example files
    get     Read cached style summary
    save    Write/update style cache file
    hash    Print current example file hashes (for debugging)

Usage:
    python style_analyzer.py check --examples <dir> --cache <path>
    python style_analyzer.py get <cache_path>
    python style_analyzer.py save <cache_path> --summary "<text>" --examples <dir>
"""

import sys
import io
import json
import hashlib
import argparse
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def file_sha256(file_path: str) -> str:
    h = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def compute_source_hash(examples_dir: str) -> dict:
    """
    Returns:
        {
            "source_count": 3,
            "source_hash": "<combined_sha256>",
            "files": {"file1.txt": "<sha256>", ...}
        }
    """
    ex_path = Path(examples_dir)
    if not ex_path.is_dir():
        return {"source_count": 0, "source_hash": "", "files": {}}

    txt_files = sorted([p for p in ex_path.iterdir() if p.is_file()])
    file_hashes = {}
    combined = hashlib.sha256()

    for f in txt_files:
        h = file_sha256(str(f))
        file_hashes[f.name] = h
        combined.update(f.name.encode('utf-8'))
        combined.update(h.encode('utf-8'))

    return {
        "source_count": len(txt_files),
        "source_hash": combined.hexdigest(),
        "files": file_hashes
    }


def cache_is_valid(examples_dir: str, cache_path: str) -> dict:
    """Check whether the cache file matches the current example directory.

    Returns:
        {"valid": true/false, "reason": "<why>"}
    """
    cache_file = Path(cache_path)
    if not cache_file.is_file():
        return {"valid": False, "reason": "no_cache"}

    try:
        text = cache_file.read_text(encoding='utf-8')
    except Exception:
        return {"valid": False, "reason": "unreadable_cache"}

    # Extract source_hash from cache frontmatter
    cached_hash = ""
    for line in text.splitlines():
        if line.startswith("source_hash:"):
            cached_hash = line.split(":", 1)[1].strip()
            break

    if not cached_hash:
        return {"valid": False, "reason": "missing_hash"}

    current = compute_source_hash(examples_dir)
    if current["source_count"] == 0:
        return {"valid": False, "reason": "empty_examples_dir"}

    if current["source_hash"] != cached_hash:
        return {"valid": False, "reason": "hash_mismatch"}

    return {"valid": True, "reason": "hash_match"}


def read_cache(cache_path: str) -> dict:
    """Read and return the full cache file content."""
    cache_file = Path(cache_path)
    if not cache_file.is_file():
        return {"exists": False, "content": "", "summary": ""}

    content = cache_file.read_text(encoding='utf-8')

    # Extract the summary section (everything after ## Style Summary)
    summary = ""
    in_summary = False
    for line in content.splitlines():
        if line.strip() == "## Style Summary":
            in_summary = True
            continue
        if in_summary:
            if line.startswith("## "):
                break
            summary += line + "\n"
    summary = summary.strip()

    return {"exists": True, "content": content, "summary": summary}


def write_cache(cache_path: str, summary: str, examples_dir: str) -> dict:
    """Generate and write the style cache file."""
    source_info = compute_source_hash(examples_dir)

    lines = []
    lines.append("# Style Profile: galgame-translation-skill")
    lines.append("")
    lines.append(f"generated_at: {datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}")
    lines.append(f"source_count: {source_info['source_count']}")
    lines.append(f"source_hash: {source_info['source_hash']}")
    lines.append("")
    lines.append("## Source Files")
    for fname, fhash in source_info["files"].items():
        lines.append(f"- {fname} (sha256: {fhash})")
    lines.append("")
    lines.append("## Style Summary")
    lines.append("")
    lines.append(summary.strip())
    lines.append("")

    content = "\n".join(lines)
    Path(cache_path).parent.mkdir(parents=True, exist_ok=True)
    Path(cache_path).write_text(content, encoding='utf-8')

    return {"status": "saved", "path": str(cache_path), "source_hash": source_info["source_hash"]}


def main() -> None:
    """CLI entry point: manage style cache."""
    parser = argparse.ArgumentParser(description="Style profile cache manager")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # check
    p_check = subparsers.add_parser("check", help="Verify cache validity")
    p_check.add_argument("--examples", required=True, help="Examples directory path")
    p_check.add_argument("--cache", required=True, help="Cache file path")

    # get
    p_get = subparsers.add_parser("get", help="Read cached style summary")
    p_get.add_argument("cache", help="Cache file path")

    # save
    p_save = subparsers.add_parser("save", help="Write/update style cache")
    p_save.add_argument("cache", help="Cache file path")
    p_save.add_argument("--summary", required=True, help="Style summary text")
    p_save.add_argument("--examples", required=True, help="Examples directory for hashing")

    # hash (debug)
    p_hash = subparsers.add_parser("hash", help="Print current example file hashes")
    p_hash.add_argument("examples", help="Examples directory path")

    args = parser.parse_args()

    if args.command == "check":
        result = cache_is_valid(args.examples, args.cache)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "get":
        result = read_cache(args.cache)
        if not result["exists"]:
            print(json.dumps({"exists": False, "error": "Cache file not found"}, indent=2, ensure_ascii=False))
            sys.exit(1)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "save":
        result = write_cache(args.cache, args.summary, args.examples)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "hash":
        result = compute_source_hash(args.examples)
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
