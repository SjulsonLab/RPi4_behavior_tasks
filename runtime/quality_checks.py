from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ProtocolQualityRule:
    trial_event_type: str
    completion_event_types: tuple[str, ...]
    allowed_outcomes: tuple[str, ...]
    require_session_summary: bool = True


ALIAS_TO_CANONICAL_PROTOCOL = {
    "go_nogo": "gonogo",
    "matt_context": "context",
    "cue_ivsa": "ivsa",
    "soyoun_treadmill_experimental": "soyoun_treadmill",
}


PROTOCOL_QUALITY_RULES: dict[str, ProtocolQualityRule] = {
    "noop": ProtocolQualityRule(
        trial_event_type="trial",
        completion_event_types=("session_complete",),
        allowed_outcomes=("noop_ok", "noop_retry", "noop_idle"),
        require_session_summary=False,
    ),
    "gonogo": ProtocolQualityRule(
        trial_event_type="trial_end",
        completion_event_types=("session_complete",),
        allowed_outcomes=("hit", "miss", "fa", "cr"),
    ),
    "context": ProtocolQualityRule(
        trial_event_type="context_trial",
        completion_event_types=("context_complete",),
        allowed_outcomes=(
            "omission",
            "correct_rewarded",
            "correct_unrewarded",
            "incorrect_rewarded",
            "incorrect_unrewarded",
        ),
    ),
    "soyoun_treadmill": ProtocolQualityRule(
        trial_event_type="treadmill_trial_end",
        completion_event_types=("session_complete",),
        allowed_outcomes=("reward_hit", "reward_miss", "neutral_lick", "neutral_pass"),
    ),
    "ivsa": ProtocolQualityRule(
        trial_event_type="ivsa_trial_end",
        completion_event_types=("session_complete",),
        allowed_outcomes=(
            "active_press_infused",
            "active_press_no_infusion",
            "active_no_press",
            "inactive_press",
            "inactive_no_press",
        ),
    ),
}


def _canonical_protocol(protocol: str | None) -> str | None:
    if protocol is None:
        return None
    return ALIAS_TO_CANONICAL_PROTOCOL.get(protocol, protocol)


def _finding(level: str, check: str, message: str) -> dict[str, str]:
    return {"level": level, "check": check, "message": message}


def _load_json_object(path: Path, label: str, findings: list[dict[str, str]]) -> dict[str, Any] | None:
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except FileNotFoundError:
        findings.append(_finding("error", f"{label}_missing", f"Missing file: {path}"))
        return None
    except json.JSONDecodeError as exc:
        findings.append(_finding("error", f"{label}_invalid_json", f"{label} JSON parse error: {exc}"))
        return None

    if not isinstance(payload, dict):
        findings.append(_finding("error", f"{label}_shape", f"{label} must be a JSON object."))
        return None
    return payload


def _load_events(path: Path, findings: list[dict[str, str]]) -> list[dict[str, Any]]:
    if not path.exists():
        findings.append(_finding("error", "events_missing", f"Missing file: {path}"))
        return []

    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                findings.append(
                    _finding("error", "events_invalid_json", f"events.jsonl line {line_number}: invalid JSON ({exc}).")
                )
                continue
            if not isinstance(record, dict):
                findings.append(
                    _finding("error", "events_shape", f"events.jsonl line {line_number}: event record must be JSON object.")
                )
                continue
            records.append(record)

    if not records:
        findings.append(_finding("error", "events_empty", "events.jsonl has no parseable event records."))

    return records


def _count_events(events: list[dict[str, Any]], event_type: str) -> int:
    return sum(1 for event in events if event.get("event_type") == event_type)


def _first_event_type(events: list[dict[str, Any]]) -> str | None:
    if not events:
        return None
    value = events[0].get("event_type")
    return value if isinstance(value, str) else None


def _validate_trial_indices(
    events: list[dict[str, Any]],
    event_type: str,
    expected_count: int,
    findings: list[dict[str, str]],
) -> None:
    indices: list[int] = []
    for event in events:
        if event.get("event_type") != event_type:
            continue
        payload = event.get("payload")
        if not isinstance(payload, dict):
            findings.append(
                _finding("error", "trial_index_payload_shape", f"{event_type} payload must be a JSON object.")
            )
            continue
        value = payload.get("trial_index")
        if not isinstance(value, int):
            findings.append(
                _finding("error", "trial_index_type", f"{event_type} payload trial_index must be an integer.")
            )
            continue
        indices.append(value)

    if len(indices) != expected_count:
        return

    expected = list(range(1, expected_count + 1))
    if sorted(indices) != expected:
        findings.append(
            _finding(
                "error",
                "trial_index_sequence",
                f"{event_type} trial_index values must cover exactly 1..{expected_count}.",
            )
        )


def evaluate_run_quality(run_dir: Path) -> dict[str, Any]:
    findings: list[dict[str, str]] = []

    metadata = _load_json_object(run_dir / "run_metadata.json", "run_metadata", findings)
    result = _load_json_object(run_dir / "result.json", "result", findings)
    events = _load_events(run_dir / "events.jsonl", findings)

    protocol_from_result = result.get("protocol") if isinstance(result, dict) else None
    protocol_from_metadata = metadata.get("protocol") if isinstance(metadata, dict) else None
    protocol_raw = protocol_from_result if isinstance(protocol_from_result, str) else (
        protocol_from_metadata if isinstance(protocol_from_metadata, str) else None
    )
    canonical_protocol = _canonical_protocol(protocol_raw)

    if metadata is not None and result is not None:
        if metadata.get("protocol") != result.get("protocol"):
            findings.append(_finding("error", "protocol_match", "run_metadata.protocol must match result.protocol."))
        if metadata.get("preset") != result.get("preset"):
            findings.append(_finding("error", "preset_match", "run_metadata.preset must match result.preset."))

    if events:
        if _count_events(events, "session_start") == 0:
            findings.append(_finding("error", "session_start_present", "events.jsonl must contain session_start."))
        if _first_event_type(events) != "session_start":
            findings.append(_finding("error", "session_start_first", "First event must be session_start."))

        if _count_events(events, "session_start") > 1:
            findings.append(
                _finding("warning", "session_start_duplicates", "Multiple session_start events were recorded.")
            )

    if canonical_protocol is None:
        findings.append(_finding("warning", "protocol_unknown", "Could not determine protocol for quality checks."))
    else:
        rule = PROTOCOL_QUALITY_RULES.get(canonical_protocol)
        if rule is None:
            findings.append(
                _finding(
                    "warning",
                    "protocol_rule_missing",
                    f"No protocol quality rule is configured for '{canonical_protocol}'.",
                )
            )
        else:
            completion_count = sum(_count_events(events, event_type) for event_type in rule.completion_event_types)
            if completion_count == 0:
                completion_list = ", ".join(rule.completion_event_types)
                findings.append(
                    _finding("error", "completion_event", f"Missing completion event. Expected one of: {completion_list}.")
                )

            if rule.require_session_summary and _count_events(events, "session_summary") == 0:
                findings.append(_finding("error", "session_summary", "Missing session_summary event."))

            if isinstance(result, dict):
                total_trials = result.get("total_trials")
                if isinstance(total_trials, int) and total_trials >= 0:
                    trial_event_count = _count_events(events, rule.trial_event_type)
                    if trial_event_count != total_trials:
                        findings.append(
                            _finding(
                                "error",
                                "trial_event_count",
                                f"Event count for '{rule.trial_event_type}' ({trial_event_count}) "
                                f"must equal total_trials ({total_trials}).",
                            )
                        )
                    _validate_trial_indices(events, rule.trial_event_type, total_trials, findings)

                outcomes = result.get("outcomes")
                if isinstance(outcomes, list):
                    unknown_outcomes = sorted(
                        {item for item in outcomes if isinstance(item, str) and item not in rule.allowed_outcomes}
                    )
                    if unknown_outcomes:
                        findings.append(
                            _finding(
                                "error",
                                "outcome_values",
                                f"Unexpected outcomes for protocol '{canonical_protocol}': {unknown_outcomes}.",
                            )
                        )

                    non_string_outcomes = [item for item in outcomes if not isinstance(item, str)]
                    if non_string_outcomes:
                        findings.append(
                            _finding(
                                "error",
                                "outcome_types",
                                "All result.outcomes entries must be strings.",
                            )
                        )

    error_count = sum(1 for finding in findings if finding["level"] == "error")
    warning_count = sum(1 for finding in findings if finding["level"] == "warning")
    status = "FAIL" if error_count else ("WARN" if warning_count else "PASS")

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "run_dir": str(run_dir),
        "protocol": canonical_protocol if canonical_protocol is not None else "unknown",
        "status": status,
        "error_count": error_count,
        "warning_count": warning_count,
        "findings": findings,
    }
