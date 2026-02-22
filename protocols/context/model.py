from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import random
import time
from typing import Any, Callable

from protocols.base import BaseProtocol, ProtocolResult
from runtime.events import BehaviorEvent, make_behavior_event


@dataclass
class ContextTrialRecord:
    trial_index: int
    active_patch_before: str
    active_patch_after: str
    choice_side: str | None
    outcome: str
    response_detected: bool
    correct_choice: bool | None
    reward_delivered: bool
    switched_patch: bool
    intertrial_interval_s: float


class ContextProtocol(BaseProtocol):
    """
    Consolidated context (latent-inference-style) protocol.

    Phase 2 baseline uses a simulation-first engine with explicit patch state,
    choice sampling, probabilistic rewards, and patch switching.
    """

    PATCH_LEFT = "left"
    PATCH_RIGHT = "right"

    def __init__(self, session):
        super().__init__(session)
        self.trial_records: list[ContextTrialRecord] = []

    def run(self, emit_event: Callable[[BehaviorEvent], None]) -> ProtocolResult:
        params = self.session.resolved_parameters

        trial_count = self._get_int(params, "trial_count", 180, minimum=1)
        switch_probability = self._get_probability(params, "switch_probability", 0.2)
        correct_reward_probability = self._get_probability(params, "correct_reward_probability", 0.9)
        incorrect_reward_probability = self._get_probability(params, "incorrect_reward_probability", 0.0)
        response_probability = self._get_probability(params, "response_probability", 0.95)
        patch_choice_accuracy = self._get_probability(params, "patch_choice_accuracy", 0.75)

        intertrial_interval_s = self._get_float(params, "intertrial_interval_s", 2.0, minimum=0.0)
        enforce_timing = bool(params.get("enforce_timing", False))

        max_correct_trials_in_patch = self._get_int(
            params,
            "max_correct_trials_in_patch",
            999999,
            minimum=1,
        )

        seed = params.get("seed", None)
        random_source = random.Random(seed)

        start_patch = self._normalize_start_patch(params.get("start_patch", "random"), random_source)
        active_patch = start_patch

        response_script = self._parse_response_script(params.get("response_script"))

        outcomes: list[str] = []
        correct_trials_in_patch = 0

        emit_event(make_behavior_event("context_start", {"start_patch": active_patch}))

        for trial_index in range(1, trial_count + 1):
            active_patch_before = active_patch
            response_detected, scripted_choice = self._sample_response(
                random_source=random_source,
                response_probability=response_probability,
                response_script=response_script,
                trial_index=trial_index,
            )

            choice_side: str | None = None
            correct_choice: bool | None = None
            reward_delivered = False
            switched_patch = False

            if not response_detected:
                outcome = "omission"
                correct_trials_in_patch = 0
            else:
                if scripted_choice is not None:
                    choice_side = scripted_choice
                else:
                    choose_correct = random_source.random() < patch_choice_accuracy
                    if choose_correct:
                        choice_side = active_patch_before
                    else:
                        choice_side = self._opposite_patch(active_patch_before)

                correct_choice = choice_side == active_patch_before

                if correct_choice:
                    reward_delivered = random_source.random() < correct_reward_probability
                    outcome = "correct_rewarded" if reward_delivered else "correct_unrewarded"
                    correct_trials_in_patch += 1
                else:
                    reward_delivered = random_source.random() < incorrect_reward_probability
                    outcome = "incorrect_rewarded" if reward_delivered else "incorrect_unrewarded"
                    correct_trials_in_patch = 0

                should_switch = False
                if reward_delivered and correct_choice and random_source.random() < switch_probability:
                    should_switch = True
                if correct_trials_in_patch >= max_correct_trials_in_patch:
                    should_switch = True

                if should_switch:
                    active_patch = self._opposite_patch(active_patch_before)
                    switched_patch = True
                    correct_trials_in_patch = 0

            outcomes.append(outcome)
            active_patch_after = active_patch

            emit_event(
                make_behavior_event(
                    "context_trial",
                    {
                        "trial_index": trial_index,
                        "active_patch_before": active_patch_before,
                        "active_patch_after": active_patch_after,
                        "choice_side": choice_side,
                        "response_detected": response_detected,
                        "correct_choice": correct_choice,
                        "reward_delivered": reward_delivered,
                        "outcome": outcome,
                        "switched_patch": switched_patch,
                    },
                )
            )

            self.trial_records.append(
                ContextTrialRecord(
                    trial_index=trial_index,
                    active_patch_before=active_patch_before,
                    active_patch_after=active_patch_after,
                    choice_side=choice_side,
                    outcome=outcome,
                    response_detected=response_detected,
                    correct_choice=correct_choice,
                    reward_delivered=reward_delivered,
                    switched_patch=switched_patch,
                    intertrial_interval_s=intertrial_interval_s,
                )
            )

            if enforce_timing and intertrial_interval_s > 0:
                time.sleep(intertrial_interval_s)

        outcome_counts = dict(Counter(outcomes))
        emit_event(
            make_behavior_event(
                "context_complete",
                {"total_trials": trial_count, "outcome_counts": outcome_counts},
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
    def _normalize_start_patch(raw: Any, random_source: random.Random) -> str:
        if raw is None:
            return random_source.choice([ContextProtocol.PATCH_LEFT, ContextProtocol.PATCH_RIGHT])
        value = str(raw).strip().lower()
        if value == "random":
            return random_source.choice([ContextProtocol.PATCH_LEFT, ContextProtocol.PATCH_RIGHT])
        if value not in {ContextProtocol.PATCH_LEFT, ContextProtocol.PATCH_RIGHT}:
            raise ValueError("Parameter 'start_patch' must be one of: left, right, random.")
        return value

    @staticmethod
    def _opposite_patch(patch: str) -> str:
        return ContextProtocol.PATCH_RIGHT if patch == ContextProtocol.PATCH_LEFT else ContextProtocol.PATCH_LEFT

    @staticmethod
    def _parse_response_script(raw_script: Any) -> list[tuple[bool, str | None]] | None:
        """
        Parse optional scripted responses.

        Supported entry examples:
        - true / false
        - 1 / 0
        - "left" / "right" / "none"
        - {"respond": true, "choice": "left"}
        """
        if raw_script is None:
            return None
        if not isinstance(raw_script, list):
            raise ValueError("Parameter 'response_script' must be a JSON list when provided.")

        parsed: list[tuple[bool, str | None]] = []
        for entry in raw_script:
            if isinstance(entry, bool):
                parsed.append((entry, None))
                continue
            if isinstance(entry, int):
                if entry in {0, 1}:
                    parsed.append((bool(entry), None))
                    continue
                raise ValueError("Integer response_script entries must be 0 or 1.")
            if isinstance(entry, str):
                lowered = entry.strip().lower()
                if lowered in {"none", "no", "omit", "omission", "0", "false"}:
                    parsed.append((False, None))
                    continue
                if lowered in {"left", "right"}:
                    parsed.append((True, lowered))
                    continue
                if lowered in {"response", "yes", "1", "true"}:
                    parsed.append((True, None))
                    continue
                raise ValueError(
                    "String response_script entries must be left/right/none or boolean-like values."
                )
            if isinstance(entry, dict):
                respond = bool(entry.get("respond", True))
                choice_raw = entry.get("choice", None)
                choice: str | None
                if choice_raw is None:
                    choice = None
                else:
                    choice = str(choice_raw).strip().lower()
                    if choice not in {"left", "right"}:
                        raise ValueError("Dict response_script choice must be 'left' or 'right'.")
                parsed.append((respond, choice))
                continue
            raise ValueError("Unsupported response_script entry type for context protocol.")

        return parsed

    @staticmethod
    def _sample_response(
        random_source: random.Random,
        response_probability: float,
        response_script: list[tuple[bool, str | None]] | None,
        trial_index: int,
    ) -> tuple[bool, str | None]:
        if response_script is not None and trial_index <= len(response_script):
            return response_script[trial_index - 1]

        response_detected = random_source.random() < response_probability
        return response_detected, None

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



def trial_record_to_dict(record: ContextTrialRecord) -> dict[str, Any]:
    return asdict(record)
