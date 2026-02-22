from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import random
import time
from typing import Any, Callable

from protocols.base import BaseProtocol, ProtocolResult


@dataclass
class IVSATrialRecord:
    trial_index: int
    lever_type: str
    press_detected: bool
    infusion_delivered: bool
    outcome: str
    timeout_s: float


class IVSAProtocol(BaseProtocol):
    """
    Experimental IVSA staging protocol.

    This intentionally models a simplified active/inactive lever process to keep
    the runtime interface alive while IVSA is inactive.
    """

    LEVER_ACTIVE = "active"
    LEVER_INACTIVE = "inactive"

    def __init__(self, session):
        super().__init__(session)
        self.trial_records: list[IVSATrialRecord] = []

    def run(self, emit_event: Callable[[str, dict[str, object]], None]) -> ProtocolResult:
        params = self.session.resolved_parameters

        trial_count = self._get_int(params, "trial_count", 120, minimum=1)
        active_lever_probability = self._get_probability(params, "active_lever_probability", 0.5)
        press_probability_active = self._get_probability(params, "press_probability_active", 0.4)
        press_probability_inactive = self._get_probability(params, "press_probability_inactive", 0.1)
        infusion_probability_given_active_press = self._get_probability(
            params,
            "infusion_probability_given_active_press",
            1.0,
        )
        timeout_s = self._get_float(params, "timeout_s", 20.0, minimum=0.0)

        enforce_timing = bool(params.get("enforce_timing", False))
        seed = params.get("seed", None)
        random_source = random.Random(seed)

        outcomes: list[str] = []

        for trial_index in range(1, trial_count + 1):
            lever_type = (
                self.LEVER_ACTIVE
                if random_source.random() < active_lever_probability
                else self.LEVER_INACTIVE
            )
            press_probability = (
                press_probability_active
                if lever_type == self.LEVER_ACTIVE
                else press_probability_inactive
            )
            press_detected = random_source.random() < press_probability

            infusion_delivered = False
            if lever_type == self.LEVER_ACTIVE and press_detected:
                infusion_delivered = random_source.random() < infusion_probability_given_active_press

            if lever_type == self.LEVER_ACTIVE:
                if press_detected and infusion_delivered:
                    outcome = "active_press_infused"
                elif press_detected:
                    outcome = "active_press_no_infusion"
                else:
                    outcome = "active_no_press"
            else:
                outcome = "inactive_press" if press_detected else "inactive_no_press"

            emit_event(
                "ivsa_trial_start",
                {
                    "trial_index": trial_index,
                    "lever_type": lever_type,
                    "timeout_s": timeout_s,
                },
            )
            emit_event(
                "ivsa_trial_end",
                {
                    "trial_index": trial_index,
                    "lever_type": lever_type,
                    "press_detected": press_detected,
                    "infusion_delivered": infusion_delivered,
                    "outcome": outcome,
                },
            )

            outcomes.append(outcome)
            self.trial_records.append(
                IVSATrialRecord(
                    trial_index=trial_index,
                    lever_type=lever_type,
                    press_detected=press_detected,
                    infusion_delivered=infusion_delivered,
                    outcome=outcome,
                    timeout_s=timeout_s,
                )
            )

            if enforce_timing and timeout_s > 0:
                time.sleep(timeout_s)

        outcome_counts = dict(Counter(outcomes))
        emit_event(
            "session_complete",
            {
                "total_trials": trial_count,
                "outcome_counts": outcome_counts,
            },
        )

        return ProtocolResult(
            protocol=self.session.protocol,
            preset=self.session.preset,
            total_trials=trial_count,
            outcome_counts=outcome_counts,
            outcomes=outcomes,
        )

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


def trial_record_to_dict(record: IVSATrialRecord) -> dict[str, Any]:
    return asdict(record)
