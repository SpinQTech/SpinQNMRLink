"""Regenerate Protobuf with pinned tools; run in a dedicated tool environment."""

from importlib.metadata import version
from pathlib import Path


def main():
    required = {"grpcio-tools": "1.70.0", "protobuf": "5.29.3"}
    for package, expected in required.items():
        if version(package) != expected:
            raise SystemExit("Use {}=={} in a dedicated environment".format(package, expected))
    from grpc_tools import protoc

    root = Path(__file__).resolve().parents[1]
    source = root / "src"
    proto = source / "spinqnmrlink/_backends/lab/connection/message.proto"
    result = protoc.main(
        ["grpc_tools.protoc", "-I" + str(source), "--python_out=" + str(source), str(proto)]
    )
    if result:
        raise SystemExit(result)


if __name__ == "__main__":
    main()
