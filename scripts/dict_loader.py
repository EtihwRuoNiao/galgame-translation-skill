#!/usr/bin/env python3
"""
dict_loader.py - Dictionary loader and query tool for galgame-translation-skill

Usage:
    python dict_loader.py <dictionary_dir> [--lookup <term>] [--stats]

Output (JSON):
    For full load: dictionary structure with all_terms for quick lookup
    For lookup: term lookup result
"""

import os
import sys
import json
import argparse
import glob
from pathlib import Path


def parse_dictionary_file(file_path: str) -> dict:
    """Parse a single dictionary CSV file with ==== TYPE ==== sections."""
    result = {
        "file": os.path.basename(file_path),
        "sections": {},
        "total_entries": 0
    }

    current_section = None

    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            for line in f:
                line = line.strip()

                if not line:
                    continue

                if line.startswith('===') and line.endswith('==='):
                    section_name = line.strip('=').strip()
                    if section_name:
                        current_section = section_name
                        if current_section not in result["sections"]:
                            result["sections"][current_section] = []
                    continue

                if current_section and ',' in line:
                    parts = line.split(',', 2)
                    japanese = parts[0].strip() if len(parts) > 0 else ""
                    chinese = parts[1].strip() if len(parts) > 1 else ""
                    note = parts[2].strip() if len(parts) > 2 else ""

                    if japanese:
                        entry = {
                            "japanese": japanese,
                            "chinese": chinese,
                            "note": note
                        }
                        result["sections"][current_section].append(entry)
                        result["total_entries"] += 1

    except Exception as e:
        result["errors"] = result.get("errors", []) + [f"Error parsing {file_path}: {e}"]

    return result


def load_all_dictionaries(dict_dir: str) -> dict:
    """Load all dictionary files from a directory."""
    dict_path = Path(dict_dir)
    if not dict_path.is_dir():
        return {
            "dictionaries": [],
            "all_terms": {},
            "stats": {"total_files": 0, "total_entries": 0, "by_type": {}},
            "error": f"Dictionary directory not found: {dict_dir}"
        }

    csv_files = glob.glob(str(dict_path / "*.csv"))
    csv_files.sort()

    result = {
        "dictionaries": [],
        "all_terms": {},
        "stats": {
            "total_files": len(csv_files),
            "total_entries": 0,
            "by_type": {}
        }
    }

    for csv_file in csv_files:
        dict_data = parse_dictionary_file(csv_file)
        result["dictionaries"].append(dict_data)

        result["stats"]["total_entries"] += dict_data["total_entries"]

        for section_name, entries in dict_data["sections"].items():
            if section_name not in result["stats"]["by_type"]:
                result["stats"]["by_type"][section_name] = 0
            result["stats"]["by_type"][section_name] += len(entries)

            for entry in entries:
                japanese = entry["japanese"]
                if japanese and japanese not in result["all_terms"]:
                    result["all_terms"][japanese] = {
                        "chinese": entry["chinese"],
                        "type": section_name,
                        "note": entry["note"]
                    }

    return result


def main() -> None:
    """CLI entry point: load, query, or convert dictionary."""
    parser = argparse.ArgumentParser(description="Dictionary loader for galgame-translation-skill")
    parser.add_argument("dict_dir", help="Dictionary directory path")
    parser.add_argument("--lookup", "-l", help="Lookup a specific term")
    parser.add_argument("--stats", "-s", action="store_true", help="Show statistics only")

    args = parser.parse_args()

    data = load_all_dictionaries(args.dict_dir)

    if args.lookup:
        if "all_terms" in data:
            term = args.lookup
            if term in data["all_terms"]:
                result = {"term": term, "found": True, "result": data["all_terms"][term]}
            else:
                result = {"term": term, "found": False, "result": None}
            result["all_terms"] = data["all_terms"]
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(json.dumps({
                "term": args.lookup,
                "found": False,
                "result": None,
                "error": "Failed to load dictionaries"
            }, indent=2, ensure_ascii=False))
        return

    if args.stats:
        print(json.dumps({"stats": data.get("stats", {})}, indent=2, ensure_ascii=False))
        return

    print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
