from __future__ import annotations

from collections import Counter
import random
from typing import Callable

from protocols.base import BaseProtocol, ProtocolResult
from runtime.events import BehaviorEvent, make_behavior_event


class NoOpProtocol(BaseProtocol):
    OUTCOME_OPTIONS = ("noop_ok", "noop_retry", "noop_idle")

    def run(self, emit_event: Callable[[BehaviorEvent], None]) -> ProtocolResult:
        seed = int(self.session.resolved_parameters.get("seed", 0))
        trial_count = int(self.session.resolved_parameters.get("trial_count", 5))

        random_source = random.Random(seed)
        outcomes: list[str] = []

        for trial_index in range(1, trial_count + 1):
            outcome = random_source.choice(self.OUTCOME_OPTIONS)
            latency_ms = random_source.randint(25, 250)
            outcomes.append(outcome)
            emit_event(
                make_behavior_event(
                    "trial",
                    {
                        "trial_index": trial_index,
                        "outcome": outcome,
                        "latency_ms": latency_ms,
                    },
                )
            )

        counts = dict(Counter(outcomes))
        emit_event(
            make_behavior_event(
                "session_complete",
                {
                    "total_trials": trial_count,
                    "outcome_counts": counts,
                },
            )
        )

        return ProtocolResult(
            protocol=self.session.protocol,
            preset=self.session.preset,
            total_trials=trial_count,
            outcome_counts=counts,
            outcomes=outcomes,
        )
