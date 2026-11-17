"""Run project checks without installing tools or changing source files."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--test", action="store_true", help="also run tests and compilation"
    )
    args = parser.parse_args()
    checks = [
        ("Python lint (Ruff)", [sys.executable, "-m", "ruff", "check", "."]),
        ("Python format (Black)", [sys.executable, "-m", "black", "--check", "."]),
    ]
    node = shutil.which("node")
    eslint = ROOT / "node_modules" / "eslint" / "bin" / "eslint.js"
    if node and eslint.is_file():
        checks.append(
            (
                "JavaScript/TypeScript lint (ESLint)",
                [node, str(eslint), ".", "--max-warnings", "0"],
            )
        )
    if args.test:
        checks.extend(
            [
                (
                    "Application tests",
                    [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
                ),
                (
                    "Python compilation",
                    [
                        sys.executable,
                        "-m",
                        "compileall",
                        "-q",
                        "backend",
                        "migrations",
                        "tests",
                        "scripts",
                    ],
                ),
            ]
        )

    results = []
    for name, command in checks:
        print(f"\n=== {name} ===", flush=True)
        try:
            result = subprocess.run(command, cwd=ROOT, check=False)
            code = result.returncode
        except OSError as exc:
            print(f"Could not run check: {exc}", file=sys.stderr)
            code = 2
        results.append((name, code))

    if not node or not eslint.is_file():
        print(
            "\nESLint unavailable. Install Node.js and run npm ci in the repository root.",
            file=sys.stderr,
        )
        results.append(("JavaScript/TypeScript lint (ESLint)", 2))

    print("\n=== Summary ===", flush=True)
    for name, code in results:
        print(f"{'PASS' if code == 0 else 'FAIL'} | {name} | exit={code}")
    print("Lint success does not establish functional correctness.")
    return 1 if any(code for _, code in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
