#!/usr/bin/env python3
"""Release notebook의 compile 및 미정의 이름을 깨끗한 소스로 검사한다."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path


# Jupyter가 실행 시 제공하는 이름만 제한적으로 허용한다.
ALLOWED_UNDEFINED_NAMES = {"display", "get_ipython"}


def load_code_cells(notebook_path: Path) -> list[str]:
    with notebook_path.open("r", encoding="utf-8") as stream:
        notebook = json.load(stream)
    return [
        "".join(cell.get("source", []))
        for cell in notebook.get("cells", [])
        if cell.get("cell_type") == "code"
    ]


def compile_cells(notebook_path: Path, cells: list[str]) -> list[str]:
    failures = []
    for index, source in enumerate(cells, 1):
        try:
            compile(source, f"{notebook_path}#cell-{index}", "exec")
        except SyntaxError as exc:
            failures.append(f"cell {index}: {exc}")
    return failures


def find_undefined_names(cells: list[str]) -> list[str]:
    source = "\n\n".join(cells)
    with tempfile.NamedTemporaryFile("w", suffix=".py", encoding="utf-8") as stream:
        stream.write(source)
        stream.flush()
        result = subprocess.run(
            [sys.executable, "-m", "pyflakes", stream.name],
            check=False,
            capture_output=True,
            text=True,
        )

    if result.returncode not in {0, 1} or "No module named pyflakes" in result.stderr:
        raise RuntimeError(
            "pyflakes 실행 실패: " + (result.stderr.strip() or f"exit={result.returncode}")
        )

    failures = []
    for line in result.stdout.splitlines():
        if "undefined name" not in line:
            continue
        if any(f"'{name}'" in line for name in ALLOWED_UNDEFINED_NAMES):
            continue
        failures.append(line.replace(stream.name, "<release>"))
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("notebook", type=Path)
    args = parser.parse_args()

    cells = load_code_cells(args.notebook)
    failures = compile_cells(args.notebook, cells)
    try:
        failures.extend(find_undefined_names(cells))
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if failures:
        print(f"FAIL: {args.notebook}")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"PASS: {args.notebook} / code_cells={len(cells)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
