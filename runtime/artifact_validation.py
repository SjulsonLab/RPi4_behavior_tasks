from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Any


def _is_iso_timestamp(value: str) -> bool:
    try:
        datetime.fromisoformat(value)
    except ValueError:
        return False
    return True


def _ensure_dict(value: Any, context: str) -> tuple[dict[str, Any] | None, list[str]]:
    if isinstance(value, dict):
        return value, []
    return None, [f"{context} must be a JSON object."]


def _load_json_file(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        return None, [f"Missing file: {path}"]
    except json.JSONDecodeError as exc:
        return None, [f"Invalid JSON in {path}: {exc}"]
    return _ensure_dict(data, str(path))


def validate_run_metadata(metadata: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    required_string_fields = (
        "run_id",
        "protocol",
        "preset",
        "mouse_id",
        "project",
        "started_at",
        "git_branch",
        "git_commit",
        "run_mode",
    )
    for field in required_string_fields:
        value = metadata.get(field)
        if not isinstance(value, str) or not value:
            errors.append(f"run_metadata.{field} must be a non-empty string.")

    if "git_tag" not in metadata:
        errors.append("run_metadata.git_tag is required (string or null).")
    else:
        git_tag = metadata.get("git_tag")
        if git_tag is not None and not isinstance(git_tag, str):
            errors.append("run_metadata.git_tag must be a string or null.")

    git_dirty = metadata.get("git_dirty")
    if not isinstance(git_dirty, bool):
        errors.append("run_metadata.git_dirty must be boolean.")

    run_mode = metadata.get("run_mode")
    if run_mode not in {"debug", "production"}:
        errors.append("run_metadata.run_mode must be one of: debug, production.")

    schema_version = metadata.get("schema_version")
    if not isinstance(schema_version, int) or schema_version < 1:
        errors.append("run_metadata.schema_version must be an integer >= 1.")

    started_at = metadata.get("started_at")
    if isinstance(started_at, str) and not _is_iso_timestamp(started_at):
        errors.append("run_metadata.started_at must be an ISO-8601 timestamp.")

    return errors


def validate_event_record(record: dict[str, Any], line_number: int) -> list[str]:
    errors: list[str] = []

    timestamp = record.get("timestamp")
    if not isinstance(timestamp, str) or not timestamp:
        errors.append(f"events.jsonl line {line_number}: timestamp must be a non-empty string.")
    elif not _is_iso_timestamp(timestamp):
        errors.append(f"events.jsonl line {line_number}: timestamp must be ISO-8601.")

    event_type = record.get("event_type")
    if not isinstance(event_type, str) or not event_type:
        errors.append(f"events.jsonl line {line_number}: event_type must be a non-empty string.")

    payload = record.get("payload")
    if not isinstance(payload, dict):
        errors.append(f"events.jsonl line {line_number}: payload must be a JSON object.")

    return errors


def validate_result_payload(result: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    protocol = result.get("protocol")
    if not isinstance(protocol, str) or not protocol:
        errors.append("result.protocol must be a non-empty string.")

    preset = result.get("preset")
    if not isinstance(preset, str) or not preset:
        errors.append("result.preset must be a non-empty string.")

    total_trials = result.get("total_trials")
    if not isinstance(total_trials, int) or total_trials < 0:
        errors.append("result.total_trials must be an integer >= 0.")

    outcomes = result.get("outcomes")
    if not isinstance(outcomes, list) or any(not isinstance(item, str) for item in outcomes):
        errors.append("result.outcomes must be a list of strings.")

    outcome_counts = result.get("outcome_counts")
    if not isinstance(outcome_counts, dict):
        errors.append("result.outcome_counts must be a JSON object.")
    else:
        for key, value in outcome_counts.items():
            if not isinstance(key, str):
                errors.append("result.outcome_counts keys must be strings.")
            if not isinstance(value, int) or value < 0:
                errors.append("result.outcome_counts values must be integers >= 0.")

    if isinstance(total_trials, int) and isinstance(outcomes, list):
        if len(outcomes) != total_trials:
            errors.append(
                f"result.total_trials ({total_trials}) must equal len(result.outcomes) ({len(outcomes)})."
            )

    if isinstance(total_trials, int) and isinstance(outcome_counts, dict):
        count_sum = sum(value for value in outcome_counts.values() if isinstance(value, int))
        if count_sum != total_trials:
            errors.append(
                f"result.total_trials ({total_trials}) must equal sum(result.outcome_counts.values()) "
                f"({count_sum})."
            )

    return errors


def validate_run_directory(run_dir: Path) -> list[str]:
    errors: list[str] = []
    if not run_dir.exists():
        return [f"Run directory does not exist: {run_dir}"]
    if not run_dir.is_dir():
        return [f"Run path is not a directory: {run_dir}"]

    metadata_path = run_dir / "run_metadata.json"
    events_path = run_dir / "events.jsonl"
    result_path = run_dir / "result.json"

    metadata, metadata_errors = _load_json_file(metadata_path)
    errors.extend(metadata_errors)
    result, result_errors = _load_json_file(result_path)
    errors.extend(result_errors)

    if metadata is not None:
        errors.extend(validate_run_metadata(metadata))
        run_id = metadata.get("run_id")
        if isinstance(run_id, str) and run_id and run_id != run_dir.name:
            errors.append(f"run_metadata.run_id ({run_id}) must match run directory name ({run_dir.name}).")

    if result is not None:
        errors.extend(validate_result_payload(result))

    if metadata is not None and result is not None:
        metadata_protocol = metadata.get("protocol")
        result_protocol = result.get("protocol")
        if metadata_protocol != result_protocol:
            errors.append("run_metadata.protocol must match result.protocol.")

        metadata_preset = metadata.get("preset")
        result_preset = result.get("preset")
        if metadata_preset != result_preset:
            errors.append("run_metadata.preset must match result.preset.")

    if not events_path.exists():
        errors.append(f"Missing file: {events_path}")
    else:
        line_count = 0
        parsed_event_count = 0
        with events_path.open("r", encoding="utf-8") as handle:
            for line_count, raw_line in enumerate(handle, start=1):
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    errors.append(f"events.jsonl line {line_count}: invalid JSON ({exc}).")
                    continue
                record_dict, record_errors = _ensure_dict(record, f"events.jsonl line {line_count}")
                if record_dict is None:
                    errors.extend(record_errors)
                    continue
                errors.extend(validate_event_record(record_dict, line_count))
                parsed_event_count += 1
        if line_count == 0:
            errors.append("events.jsonl must contain at least one event record.")
        elif parsed_event_count == 0:
            errors.append("events.jsonl must contain at least one non-empty event record.")

    return errors
