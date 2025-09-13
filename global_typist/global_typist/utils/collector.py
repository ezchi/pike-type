import json
import argparse
from global_typist.typist import typist
import site
import importlib.util
import sys
from pathlib import Path

def import_typist_lib(path: Path):
    module_name = str(path).replace(".py", "").replace("/", ".")
    importlib.import_module(module_name)

def main():
    parser = argparse.ArgumentParser(description="Collect all types from provided files and produce the intermediate representation.")

    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("outfile", type=argparse.FileType("w"))
    parser.add_argument("typist_files", type=str, nargs="+")

    args = parser.parse_args()
    root = args.project_root.absolute()
    for path in args.typist_files:
        import_typist_lib(Path(path).resolve().relative_to(root))

    json.dump(typist.allNameSpacesToIRDict(), args.outfile, indent=2)

if __name__ == "__main__":
    main()
