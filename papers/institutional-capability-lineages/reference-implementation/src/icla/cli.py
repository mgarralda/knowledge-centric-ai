"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: Dependency-light command line interface for specification verification.

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

from .config import Settings
from .exceptions import ICLAError
from .specification import (
    ArtifactValidator,
    ConformanceChecker,
    ConformanceProfile,
    SchemaLoader,
)


def _validator(specification_dir: str | None) -> ArtifactValidator:
    settings = (
        Settings(specification_dir=Path(specification_dir).resolve())
        if specification_dir
        else Settings()
    )
    return ArtifactValidator(SchemaLoader(settings.schema_dir))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="icla", description="ICLA reference implementation")
    parser.add_argument("--specification-dir", help="Directory containing schemas/")
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="validate an artifact or directory")
    validate.add_argument("path")
    trace = commands.add_parser("run-trace", help="validate every artifact in a reference trace")
    trace.add_argument("name")
    trace.add_argument("--trace-dir")
    commands.add_parser("schemas", help="list available specification schemas")
    commands.add_parser("validate-schemas", help="validate all published Draft 2020-12 schemas")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    validator = _validator(arguments.specification_dir)
    try:
        if arguments.command == "schemas":
            for name in validator.loader.available():
                print(name)
            return 0
        if arguments.command == "validate-schemas":
            names = validator.loader.available()
            if not names:
                raise ICLAError(f"No schemas found in {validator.loader.schema_dir}")
            for name in names:
                Draft202012Validator.check_schema(validator.loader.load(name))
                print(f"valid: {name}")
            print(f"Validated {len(names)} schema(s)")
            return 0
        path = (
            Path(arguments.path)
            if arguments.command == "validate"
            else Path(
                arguments.trace_dir
                or validator.loader.schema_dir.parent / "reference-traces" / arguments.name
            )
        )
        if not path.exists():
            raise ICLAError(f"Path does not exist: {path}")
        validated = (
            validator.validate_directory(path)
            if path.is_dir()
            else [path]
            if validator.validate_file(path)
            else []
        )
        if arguments.command == "run-trace":
            artifacts = [validator.validate_file(artifact_path) for artifact_path in validated]
            ConformanceChecker().require_trace(artifacts, ConformanceProfile.EVOLVING)
            print(
                f"Validated {len(validated)} artifact(s); "
                f"{ConformanceProfile.EVOLVING} conformance passed"
            )
        else:
            print(f"Validated {len(validated)} artifact(s)")
        return 0
    except (ICLAError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
    # print("Hello world")
