"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: JSON Schema validation with artifact-oriented error messages.

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from ..exceptions import SpecificationValidationError
from .schema_loader import SchemaLoader

DOCUMENT_SCHEMAS = {
    "institutional-capability": "capability",
    "institutional-capability-registry-snapshot": "capability-registry",
    "capability-knowledge-contract": "ckc",
    "operational-intent": "intent",
    "capability-resolution": "resolution",
    "contextual-assembly": "assembly",
    "execution-evidence-bundle": "evidence-bundle",
    "governance-decision": "governance-decision",
}


class ArtifactValidator:
    def __init__(self, loader: SchemaLoader | None = None) -> None:
        self.loader = loader or SchemaLoader()

    def schema_for(self, data: dict[str, Any]) -> str:
        document_type = data.get("document_type")
        try:
            return DOCUMENT_SCHEMAS[str(document_type)]
        except KeyError as error:
            raise SpecificationValidationError(
                f"Unknown document_type {document_type!r}; cannot select a schema"
            ) from error

    def validate_artifact(self, data: dict[str, Any], schema_name: str | None = None) -> None:
        name = schema_name or self.schema_for(data)
        schema = self.loader.load(name)
        validator = Draft202012Validator(schema, registry=self.loader.registry)
        errors = sorted(validator.iter_errors(data), key=lambda item: list(item.absolute_path))
        if errors:
            details = []
            for error in errors:
                location = ".".join(str(part) for part in error.absolute_path) or "<root>"
                details.append(f"{location}: {error.message}")
            raise SpecificationValidationError(f"{name}.yaml:\n  " + "\n  ".join(details))

    def validate_file(self, path: str | Path, schema_name: str | None = None) -> dict[str, Any]:
        artifact_path = Path(path)
        try:
            with artifact_path.open(encoding="utf-8") as stream:
                data = yaml.safe_load(stream)
        except yaml.YAMLError as error:
            raise SpecificationValidationError(f"{artifact_path}: invalid YAML: {error}") from error
        if not isinstance(data, dict):
            raise SpecificationValidationError(f"{artifact_path}: artifact must be a mapping")
        self.validate_artifact(data, schema_name)
        return data

    def validate_directory(self, path: str | Path) -> list[Path]:
        root = Path(path)
        validated: list[Path] = []
        failures: list[str] = []
        for artifact_path in sorted((*root.rglob("*.yaml"), *root.rglob("*.yml"))):
            if artifact_path.name.endswith((".schema.yaml", ".schema.yml")):
                continue
            try:
                self.validate_file(artifact_path)
                validated.append(artifact_path)
            except SpecificationValidationError as error:
                failures.append(f"{artifact_path}: {error}")
        if failures:
            raise SpecificationValidationError("\n".join(failures))
        return validated
