import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from .core import ConversionError, convert


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="patentar-convert",
        description="Convert a supported CAD or mesh file into a validated GLB.",
    )
    parser.add_argument("input", type=Path, help="Source model path")
    parser.add_argument("--output", required=True, type=Path, help="Destination .glb path")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.output.suffix.lower() != ".glb":
        print("Conversion failed: --output must end with .glb", file=sys.stderr)
        return 2

    try:
        result = convert(args.input, args.output)
    except ConversionError as exc:
        print(f"Conversion failed: {exc}", file=sys.stderr)
        return 1

    print(result)
    return 0
