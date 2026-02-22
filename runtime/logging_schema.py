from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

from runtime.events import BehaviorEvent, make_behavior_event


@dataclass
class RunMetadata:
    run_id: str
    protocol: str
    preset: str
    mouse_id: str
    project: str
    started_at: str
    git_branch: str
    git_tag: str | None
    git_commit: str
    git_dirty: bool
    run_mode: str = "debug"
    seed: Any = None
    template_path: str | None = None
    schema_version: int = 1


@dataclass
class RunPaths:
    run_dir: Path
    metadata_path: Path
    events_path: Path
    result_path: Path
    quality_report_path: Path



def create_run_paths(output_root: Path, run_id: str) -> RunPaths:
    run_dir = output_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    return RunPaths(
        run_dir=run_dir,
        metadata_path=run_dir / "run_metadata.json",
        events_path=run_dir / "events.jsonl",
        result_path=run_dir / "result.json",
        quality_report_path=run_dir / "quality_report.json",
    )



def write_run_metadata(path: Path, metadata: RunMetadata) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(asdict(metadata), handle, indent=2, sort_keys=True)



def append_event(
    path: Path,
    event: BehaviorEvent | str,
    payload: dict[str, object] | None = None,
    timestamp: str | None = None,
) -> None:
    if isinstance(event, BehaviorEvent):
        event_obj = event
    else:
        if payload is None:
            raise ValueError("payload is required when append_event is called with an event_type string.")
        event_obj = make_behavior_event(event_type=event, payload=payload, timestamp=timestamp)

    event_record = {
        "timestamp": event_obj.timestamp,
        "event_type": event_obj.event_type,
        "payload": event_obj.payload,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event_record, sort_keys=True) + "\n")



def write_result(path: Path, result: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)



def write_quality_report(path: Path, report: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
