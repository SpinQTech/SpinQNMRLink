"""Build language documentation and an English redirect entry point."""

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENTRY_POINT = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="0; url=en/index.html">
  <title>SpinQNMRLink Documentation</title>
</head>
<body>
  <p><a href="en/index.html">Open the English documentation</a></p>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--language", choices=("all", "zh_CN", "en"), default="all")
    parser.add_argument("--output", type=Path, default=ROOT / "docs/_build/html")
    args = parser.parse_args()
    output = args.output.resolve()
    languages = ("zh_CN", "en") if args.language == "all" else (args.language,)
    for language in languages:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "sphinx",
                "-E",
                "-a",
                "-W",
                "--keep-going",
                "-b",
                "html",
                "-c",
                str(ROOT / "docs"),
                "-D",
                "language=" + language,
                str(ROOT / "docs" / language),
                str(output / language),
            ],
            cwd=ROOT,
            check=True,
        )
    (output / "index.html").write_text(ENTRY_POINT, encoding="utf-8")


if __name__ == "__main__":
    main()
