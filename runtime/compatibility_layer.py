from __future__ import annotations

import json
from typing import Any

from runtime.session_config import SessionTemplate



def _coerce_value(value: str) -> Any:
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"

    try:
        return int(value)
    except ValueError:
        pass

    try:
        return float(value)
    except ValueError:
        pass

    if value.startswith("{") or value.startswith("["):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass

    return value



def parse_cli_overrides(items: list[str]) -> dict[str, Any]:
    overrides: dict[str, Any] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"Override must be in KEY=VALUE format: {item}")
        key, value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"Override key cannot be empty: {item}")
        overrides[key] = _coerce_value(value.strip())
    return overrides



def _prompt_for_value(parameter_name: str) -> Any:
    raw = input(f"Enter value for required parameter '{parameter_name}': ").strip()
    return _coerce_value(raw)



def resolve_runtime_parameters(
    template: SessionTemplate,
    cli_overrides: dict[str, Any],
    interactive: bool,
) -> dict[str, Any]:
    resolved = dict(template.parameters)
    resolved.update(cli_overrides)

    for parameter in template.required_parameters:
        value = resolved.get(parameter)
        missing = parameter not in resolved or value is None or (isinstance(value, str) and value == "")
        if not missing:
            continue

        if interactive:
            resolved[parameter] = _prompt_for_value(parameter)
        else:
            raise ValueError(
                f"Required parameter '{parameter}' was not provided. "
                "Use --set KEY=VALUE or enable interactive mode."
            )

    return resolved
