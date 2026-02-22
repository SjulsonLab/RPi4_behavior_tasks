from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import random
import time
from typing import Any, Callable

from protocols.base import BaseProtocol, ProtocolResult


@dataclass
class SoyounTreadmillTrialRecord:
    trial_index: int
    zone: str
    speed_cm_s: float
    trial_duration_s: float
    distance_cm: float
    lick_detected: bool
    outcome: str
    reward_delivered: bool


class SoyounTreadmillProtocol(BaseProtocol):
    """
    Experimental Soyoun treadmill staging protocol.

    This is a simulation-first baseline so the runtime path can be exercised
    while behavior targets are finalized with protocol owners.
    """

    ZONE_REWARD = "reward_zone"
    ZONE_NEUTRAL = "neutral_zone"

    def __init__(self, session):
        super().__init__(session)
        self.trial_records: list[SoyounTreadmillTrialRecord] = []

    def run(self, emit_event: Callable[[str, dict[str, object]], None]) -> ProtocolResult:
        params = self.session.resolved_parameters

        trial_count = self._get_int(params, "trial_count", 80, minimum=1)
        reward_zone_probability = self._get_probability(params, "reward_zone_probability", 0.35)
        lick_probability_reward_zone = self._get_probability(params, "lick_probability_reward_zone", 0.8)
        lick_probability_neutral_zone = self._get_probability(params, "lick_probability_neutral_zone", 0.2)
        speed_mean_cm_s = self._get_float(params, "speed_mean_cm_s", 18.0, minimum=0.0)
        speed_std_cm_s = self._get_float(params, "speed_std_cm_s", 3.0, minimum=0.0)
        trial_duration_s = self._get_float(params, "trial_duration_s", 2.0, minimum=0.0)
        intertrial_interval_s = self._get_float(params, "intertrial_interval_s", 1.0, minimum=0.0)

        enforce_timing = bool(params.get("enforce_timing", False))
        seed = params.get("seed", None)
        random_source = random.Random(seed)

        outcomes: list[str] = []

        for trial_index in range(1, trial_count + 1):
            zone = self.ZONE_REWARD if random_source.random() < reward_zone_probability else self.ZONE_NEUTRAL
            lick_probability = (
                lick_probability_reward_zone
                if zone == self.ZONE_REWARD
                else lick_probability_neutral_zone
            )

            lick_detected = random_source.random() < lick_probability
            speed_cm_s = max(0.0, round(random_source.gauss(speed_mean_cm_s, speed_std_cm_s), 4))
            distance_cm = round(speed_cm_s * trial_duration_s, 4)

            if zone == self.ZONE_REWARD:
                reward_delivered = lick_detected
                outcome = "reward_hit" if reward_delivered else "reward_miss"
            else:
                reward_delivered = False
                outcome = "neutral_lick" if lick_detected else "neutral_pass"

            emit_event(
                "treadmill_trial_start",
                {
                    "trial_index": trial_index,
                    "zone": zone,
                    "trial_duration_s": trial_duration_s,
                    "intertrial_interval_s": intertrial_interval_s,
                },
            )
            emit_event(
                "treadmill_trial_end",
                {
                    "trial_index": trial_index,
                    "zone": zone,
                    "lick_detected": lick_detected,
                    "speed_cm_s": speed_cm_s,
                    "distance_cm": distance_cm,
                    "reward_delivered": reward_delivered,
                    "outcome": outcome,
                },
            )

            outcomes.append(outcome)
            self.trial_records.append(
                SoyounTreadmillTrialRecord(
                    trial_index=trial_index,
                    zone=zone,
                    speed_cm_s=speed_cm_s,
                    trial_duration_s=trial_duration_s,
                    distance_cm=distance_cm,
                    lick_detected=lick_detected,
                    outcome=outcome,
                    reward_delivered=reward_delivered,
                )
            )

            if enforce_timing and intertrial_interval_s > 0:
                time.sleep(intertrial_interval_s)

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


def trial_record_to_dict(record: SoyounTreadmillTrialRecord) -> dict[str, Any]:
    return asdict(record)
