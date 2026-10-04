"""Phase 1 configuration and reproducibility controls."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AcoConfig:
    seed: int = 7
    iterations: int = 30
    ants_per_iteration: int = 12
    alpha: float = 1.0
    beta: float = 2.0
    evaporation_rate: float = 0.2
    initial_pheromone: float = 1.0

    def __post_init__(self) -> None:
        if self.iterations <= 0 or self.ants_per_iteration <= 0:
            raise ValueError("ACO iterations and ants_per_iteration must be positive")
        if self.alpha < 0 or self.beta < 0 or self.initial_pheromone <= 0:
            raise ValueError("ACO influences must be non-negative and pheromone positive")
        if not 0 < self.evaporation_rate < 1:
            raise ValueError("evaporation_rate must be in (0, 1)")


@dataclass(frozen=True, slots=True)
class ParetoConfig:
    archive_size: int = 20

    def __post_init__(self) -> None:
        if self.archive_size <= 0:
            raise ValueError("archive_size must be positive")


@dataclass(frozen=True, slots=True)
class RunConfig:
    """One seed governs all stochastic implementations added after Phase 1."""

    seed: int = 7
    aco: AcoConfig = AcoConfig()
    pareto: ParetoConfig = ParetoConfig()
