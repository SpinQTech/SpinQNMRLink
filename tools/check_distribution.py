"""Check portable artifacts and the installed wheel outside the source checkout."""

import argparse
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_EXAMPLE_JSON = {
    "examples/manifest.json",
    "examples/connection_config.example.json",
}


def check_configuration_paths(names, *, source_archive=False):
    """Reject local profiles, including files ignored by Git but bundled by setuptools."""
    for name in names:
        path = PurePosixPath(name)
        if source_archive:
            path = PurePosixPath(*path.parts[1:])
        if (
            path.name == "connection_config.json"
            or path.name.endswith(".local.json")
            or (
                path.parts[:1] == ("examples",)
                and path.suffix == ".json"
                and path.as_posix() not in PUBLIC_EXAMPLE_JSON
            )
        ):
            raise SystemExit("Local or unapproved configuration in distribution: " + name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist-dir", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    wheels = list(args.dist_dir.resolve().glob("*.whl"))
    archives = list(args.dist_dir.resolve().glob("*.tar.gz"))
    if len(wheels) != 1 or len(archives) != 1:
        raise SystemExit("Build exactly one current wheel and source archive in dist/")
    with zipfile.ZipFile(wheels[0]) as wheel:
        names = wheel.namelist()
        metadata = wheel.read(next(n for n in names if n.endswith(".dist-info/WHEEL")))
        assert b"Root-Is-Purelib: true" in metadata and b"Tag: py3-none-any" in metadata
        assert not any(n.endswith(".dist-info/entry_points.txt") for n in names)
    with tarfile.open(archives[0]) as archive:
        source_names = archive.getnames()
    check_configuration_paths(names)
    check_configuration_paths(source_names, source_archive=True)
    for name in names + source_names:
        assert not name.lower().endswith((".dll", ".so", ".dylib", ".pyd", ".cmd", ".bat"))
        assert not name.endswith(("/native.py", "/cli.py", "/launcher.py"))
    for required in (
        "tests/test_triangulum_protocol.py",
        "docs/en/installation.rst",
        "docs/zh_CN/installation.rst",
        "examples/manifest.json",
        "examples/connection_config.example.json",
    ):
        assert any(n.endswith("/" + required) for n in source_names), required
    code = """
import ctypes, importlib.util, os, pathlib, sys, threading
package_root = sys.argv[1]
sys.path.insert(0, package_root)
before = {t.ident for t in threading.enumerate()}
ctypes.CDLL = lambda *a, **k: (_ for _ in ()).throw(AssertionError('native loading'))
import spinqnmrlink
assert os.path.commonpath([str(pathlib.Path(spinqnmrlink.__file__).resolve()), package_root]) == package_root
assert importlib.util.find_spec('spinqnmrlink.cli') is None
assert importlib.util.find_spec('spinqnmrlink.native') is None
entries = spinqnmrlink.list_experiments()
assert len(entries) == 35
for entry in entries:
    assert spinqnmrlink.parameters_for(entry.key).to_wire()
assert {t.ident for t in threading.enumerate()} == before
print('Installed wheel: 35 offline parameter definitions passed without network workers or native loading.')
"""
    with tempfile.TemporaryDirectory(prefix="spinq-wheel-") as directory:
        package_root = str((Path(directory) / "installed").resolve())
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--no-index",
                "--no-deps",
                "--target",
                package_root,
                str(wheels[0]),
            ],
            check=True,
        )
        subprocess.run([sys.executable, "-I", "-c", code, package_root], cwd=directory, check=True)
    print("Universal wheel and source archive contents passed.")


if __name__ == "__main__":
    main()
