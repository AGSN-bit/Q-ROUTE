"""Interfaces that keep Q-ROUTE's quantum and ACO roles independently replaceable."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from random import Random
from typing import Protocol

from ..config import AcoConfig
from ..models import ObjectiveVector, Route


class CandidateGenerator(Protocol):
    def generate(self, source: str, destination: str, count: int, rng: Random) -> list[tuple[str, ...]]: ...


class MultiObjectiveEvaluator(Protocol):
    def evaluate(self, candidate: tuple[str, ...]) -> ObjectiveVector: ...


@dataclass(frozen=True, slots=True)
class QuantumCandidate:
    representation: tuple[str, ...]
    amplitudes: tuple[float, ...]
    objectives: ObjectiveVector | None = None


@dataclass(frozen=True, slots=True)
class QuantumSearchState:
    population: tuple[QuantumCandidate, ...]
    iteration: int
    diversity: float
    convergence: float


class QuantumInspiredSearch(ABC):
    """Contract for a genuine probabilistic/diversity search stage.

    Implementations must expose candidate representation, probabilistic
    generation/update, exploration/exploitation control, convergence, and a
    termination decision. They are evaluated independently before hybrid use.
    """

    @abstractmethod
    def initialize(self, candidates: Iterable[tuple[str, ...]], rng: Random) -> QuantumSearchState: ...

    @abstractmethod
    def generate_candidates(self, state: QuantumSearchState, count: int, rng: Random) -> list[tuple[str, ...]]: ...

    @abstractmethod
    def evaluate_candidates(
        self, candidates: Iterable[tuple[str, ...]], evaluator: MultiObjectiveEvaluator
    ) -> list[QuantumCandidate]: ...

    @abstractmethod
    def update(self, state: QuantumSearchState, evaluated: Iterable[QuantumCandidate], rng: Random) -> QuantumSearchState: ...

    @abstractmethod
    def exploration_ratio(self, state: QuantumSearchState) -> float: ...

    @abstractmethod
    def convergence(self, state: QuantumSearchState) -> float: ...

    @abstractmethod
    def should_terminate(self, state: QuantumSearchState) -> bool: ...


class AcoRefiner(ABC):
    """Modular ACO route-refinement contract; no quantum dependency is implied."""

    @abstractmethod
    def initialize_pheromones(self, edge_ids: Iterable[str], config: AcoConfig) -> Mapping[str, float]: ...

    @abstractmethod
    def heuristic(self, edge_id: str) -> float: ...

    @abstractmethod
    def construct_feasible_path(
        self, source: str, destination: str, visited_nodes: frozenset[str], rng: Random
    ) -> tuple[str, ...] | None: ...

    @abstractmethod
    def evaporate(self, pheromones: Mapping[str, float], config: AcoConfig) -> Mapping[str, float]: ...

    @abstractmethod
    def deposit(self, pheromones: Mapping[str, float], routes: Iterable[Route]) -> Mapping[str, float]: ...

    @abstractmethod
    def refine(self, candidates: Iterable[Route], source: str, destination: str, config: AcoConfig) -> list[Route]: ...


class ParetoArchivist(Protocol):
    def add_all(self, candidates: Iterable[Route]) -> None: ...

    def routes(self) -> list[Route]: ...


class DecisionRanker(Protocol):
    def rank(self, routes: Iterable[Route]) -> list[Route]: ...
