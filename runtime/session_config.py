from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


@dataclass
class MouseInfo:
    mouse_id: str
    project: str
    species: str = "mouse"
    sex: str = "unknown"
    genotype: str = "unknown"
    notes: str = ""
    extras: dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionTemplate:
    protocol: str
    preset: str
    max_minutes: int
    parameters: dict[str, Any] = field(default_factory=dict)
    required_parameters: list[str] = field(default_factory=list)


@dataclass
class SessionConfig:
    run_id: str
    started_at: str
    protocol: str
    preset: str
    max_minutes: int
    mouse_info: MouseInfo
    resolved_parameters: dict[str, Any]
    source_template: str | None = None



def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected an object in JSON file: {path}")
    return data



def load_mouse_info(path: Path) -> MouseInfo:
    data = _load_json(path)
    extras = {
        key: value
        for key, value in data.items()
        if key not in {"mouse_id", "project", "species", "sex", "genotype", "notes"}
    }
    try:
        return MouseInfo(
            mouse_id=str(data["mouse_id"]),
            project=str(data["project"]),
            species=str(data.get("species", "mouse")),
            sex=str(data.get("sex", "unknown")),
            genotype=str(data.get("genotype", "unknown")),
            notes=str(data.get("notes", "")),
            extras=extras,
        )
    except KeyError as exc:
        raise ValueError(f"Mouse info is missing required key: {exc}") from exc



def load_session_template(path: Path) -> SessionTemplate:
    data = _load_json(path)
    try:
        protocol = str(data["protocol"])
        preset = str(data["preset"])
        max_minutes = int(data.get("max_minutes", 60))
    except KeyError as exc:
        raise ValueError(f"Session template is missing required key: {exc}") from exc

    parameters = data.get("parameters", {})
    if not isinstance(parameters, dict):
        raise ValueError("Template field 'parameters' must be a JSON object.")

    required_parameters = data.get("required_parameters", [])
    if not isinstance(required_parameters, list):
        raise ValueError("Template field 'required_parameters' must be a JSON array.")

    return SessionTemplate(
        protocol=protocol,
        preset=preset,
        max_minutes=max_minutes,
        parameters=parameters,
        required_parameters=[str(item) for item in required_parameters],
    )



def build_session_config(
    template: SessionTemplate,
    mouse_info: MouseInfo,
    resolved_parameters: dict[str, Any],
    protocol_override: str | None = None,
    source_template: str | None = None,
) -> SessionConfig:
    now = datetime.now(timezone.utc)
    started_at = now.isoformat()
    timestamp = now.strftime("%Y%m%d_%H%M%S")

    protocol = protocol_override if protocol_override else template.protocol
    run_id = f"{mouse_info.mouse_id}_{protocol}_{timestamp}"

    return SessionConfig(
        run_id=run_id,
        started_at=started_at,
        protocol=protocol,
        preset=template.preset,
        max_minutes=template.max_minutes,
        mouse_info=mouse_info,
        resolved_parameters=resolved_parameters,
        source_template=source_template,
    )
