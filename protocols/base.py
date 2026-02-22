from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable

from runtime.session_config import SessionConfig


@dataclass
class ProtocolResult:
    protocol: str
    preset: str
    total_trials: int
    outcome_counts: dict[str, int]
    outcomes: list[str]


class BaseProtocol(ABC):
    def __init__(self, session: SessionConfig):
        self.session = session

    @abstractmethod
    def run(self, emit_event: Callable[[str, dict[str, object]], None]) -> ProtocolResult:
        """Execute one session of the protocol and return aggregate outcomes."""
