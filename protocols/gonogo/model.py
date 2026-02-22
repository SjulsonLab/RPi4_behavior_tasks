from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import random
import time
from typing import Any, Callable

from protocols.base import BaseProtocol, ProtocolResult
from runtime.events import BehaviorEvent, make_behavior_event


@dataclass
class GoNoGoTrialRecord:
    trial_index: int
    trial_type: str
    outcome: str
    response_detected: bool
    response_time_s: float | None
    iti_s: float
    reward_delivered: bool
    punishment_delivered: bool


class GoNoGoProtocol(BaseProtocol):
    """
    Consolidated go/no-go task protocol.

    Phase 1 implementation uses a deterministic simulation path so parity and
    distribution checks can be validated immediately.
    """

    def __init__(self, session):
        super().__init__(session)
        self.trial_records: list[GoNoGoTrialRecord] = []

    def run(self, emit_event: Callable[[BehaviorEvent], None]) -> ProtocolResult:
        params = self.session.resolved_parameters

        trial_count = self._get_int(params, "trial_count", 100, minimum=1)
        go_probability = self._get_probability(params, "go_probability", 0.5)
        response_prob_go = self._get_probability(params, "response_prob_go", 0.8)
        response_prob_nogo = self._get_probability(params, "response_prob_nogo", 0.2)
        lockout_length_s = self._get_float(params, "lockout_length_s", 1.5, minimum=0.0)
        response_window_s = self._get_float(params, "response_window_s", 1.5, minimum=0.0)
        iti_min_s = self._get_float(params, "iti_min_s", 2.0, minimum=0.0)
        iti_max_s = self._get_float(params, "iti_max_s", 4.0, minimum=0.0)
        if iti_max_s < iti_min_s:
            raise ValueError("Parameter 'iti_max_s' must be >= 'iti_min_s'.")

        enforce_timing = bool(params.get("enforce_timing", False))
        seed = params.get("seed", None)
        random_source = random.Random(seed)

        response_script = self._parse_response_script(params.get("response_script"))

        outcomes: list[str] = []

        for trial_index in range(1, trial_count + 1):
            trial_type = "go" if random_source.random() < go_probability else "nogo"
            response_detected = self._sample_response(
                random_source=random_source,
                trial_type=trial_type,
                response_prob_go=response_prob_go,
                response_prob_nogo=response_prob_nogo,
                response_script=response_script,
                trial_index=trial_index,
            )

            response_time_s: float | None = None
            if response_detected:
                if response_window_s > 0:
                    response_time_s = round(lockout_length_s + random_source.uniform(0.0, response_window_s), 4)
                else:
                    response_time_s = round(lockout_length_s, 4)

            outcome = self._evaluate_outcome(trial_type=trial_type, response_detected=response_detected)
            reward_delivered = outcome == "hit"
            punishment_delivered = outcome == "fa"
            iti_s = round(random_source.uniform(iti_min_s, iti_max_s), 4)

            emit_event(
                make_behavior_event(
                    "trial_start",
                    {
                        "trial_index": trial_index,
                        "trial_type": trial_type,
                        "lockout_length_s": lockout_length_s,
                        "response_window_s": response_window_s,
                    },
                )
            )
            emit_event(
                make_behavior_event(
                    "trial_end",
                    {
                        "trial_index": trial_index,
                        "trial_type": trial_type,
                        "outcome": outcome,
                        "response_detected": response_detected,
                        "response_time_s": response_time_s,
                        "iti_s": iti_s,
                        "reward_delivered": reward_delivered,
                        "punishment_delivered": punishment_delivered,
                    },
                )
            )

            self.trial_records.append(
                GoNoGoTrialRecord(
                    trial_index=trial_index,
                    trial_type=trial_type,
                    outcome=outcome,
                    response_detected=response_detected,
                    response_time_s=response_time_s,
                    iti_s=iti_s,
                    reward_delivered=reward_delivered,
                    punishment_delivered=punishment_delivered,
                )
            )
            outcomes.append(outcome)

            if enforce_timing:
                total_trial_time_s = lockout_length_s + response_window_s + iti_s
                if total_trial_time_s > 0:
                    time.sleep(total_trial_time_s)

        outcome_counts = dict(Counter(outcomes))
        emit_event(
            make_behavior_event(
                "session_complete",
                {
                    "total_trials": trial_count,
                    "outcome_counts": outcome_counts,
                },
            )
        )

        return ProtocolResult(
            protocol=self.session.protocol,
            preset=self.session.preset,
            total_trials=trial_count,
            outcome_counts=outcome_counts,
            outcomes=outcomes,
        )

    @staticmethod
    def _evaluate_outcome(trial_type: str, response_detected: bool) -> str:
        if trial_type == "go":
            return "hit" if response_detected else "miss"
        return "fa" if response_detected else "cr"

    @staticmethod
    def _sample_response(
        random_source: random.Random,
        trial_type: str,
        response_prob_go: float,
        response_prob_nogo: float,
        response_script: list[bool] | None,
        trial_index: int,
    ) -> bool:
        if response_script is not None and trial_index <= len(response_script):
            return response_script[trial_index - 1]

        threshold = response_prob_go if trial_type == "go" else response_prob_nogo
        return random_source.random() < threshold

    @staticmethod
    def _parse_response_script(raw_script: Any) -> list[bool] | None:
        if raw_script is None:
            return None
        if not isinstance(raw_script, list):
            raise ValueError("Parameter 'response_script' must be a JSON list when provided.")

        parsed: list[bool] = []
        for item in raw_script:
            if isinstance(item, bool):
                parsed.append(item)
                continue
            if isinstance(item, int):
                if item in {0, 1}:
                    parsed.append(bool(item))
                    continue
                raise ValueError("Integer response_script entries must be 0 or 1.")
            if isinstance(item, str):
                lowered = item.strip().lower()
                if lowered in {"1", "true", "t", "yes", "y", "response", "r"}:
                    parsed.append(True)
                    continue
                if lowered in {"0", "false", "f", "no", "n", "none", "miss"}:
                    parsed.append(False)
                    continue
            raise ValueError(
                "Unsupported response_script entry. Allowed: bool, 0/1, or strings "
                "('response'/'none')."
            )

        return parsed

    @staticmethod
    def _get_probability(params: dict[str, Any], name: str, default: float) -> float:
        value = float(params.get(name, default))
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"Parameter '{name}' must be between 0.0 and 1.0.")
        return value

    @staticmethod
    def _get_float(params: dict[str, Any], name: str, default: float, minimum: float | None = None) -> float:
        value = float(params.get(name, default))
        if minimum is not None and value < minimum:
            raise ValueError(f"Parameter '{name}' must be >= {minimum}.")
        return value

    @staticmethod
    def _get_int(params: dict[str, Any], name: str, default: int, minimum: int | None = None) -> int:
        value = int(params.get(name, default))
        if minimum is not None and value < minimum:
            raise ValueError(f"Parameter '{name}' must be >= {minimum}.")
        return value



def trial_record_to_dict(record: GoNoGoTrialRecord) -> dict[str, Any]:
    return asdict(record)
