"""Typed domain models with one canonical objective ordering."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Mapping


class ObjectiveName(StrEnum):
    TIME = "TIME"
    CONGESTION = "CONGESTION"
    DISTANCE = "DISTANCE"
    FUEL = "FUEL"
    EMISSIONS = "EMISSIONS"
    SAFETY = "SAFETY"


OBJECTIVE_ORDER: tuple[ObjectiveName, ...] = (
    ObjectiveName.TIME,
    ObjectiveName.CONGESTION,
    ObjectiveName.DISTANCE,
    ObjectiveName.FUEL,
    ObjectiveName.EMISSIONS,
    ObjectiveName.SAFETY,
)


@dataclass(frozen=True, slots=True)
class ObjectiveVector:
    """Minimisation objectives in the canonical Q-ROUTE order.

    Named fields are the source of truth. ``as_tuple`` is solely for generic
    optimisation routines and always follows ``OBJECTIVE_ORDER``.
    """

    time: float
    congestion: float
    distance: float
    fuel: float
    emissions: float
    safety: float

    def __post_init__(self) -> None:
        if any(value < 0 for value in self.as_tuple()):
            raise ValueError("Objective values must be non-negative")

    def as_tuple(self) -> tuple[float, float, float, float, float, float]:
        return (
            self.time,
            self.congestion,
            self.distance,
            self.fuel,
            self.emissions,
            self.safety,
        )

    def as_dict(self) -> dict[str, float]:
        return dict(zip((item.value for item in OBJECTIVE_ORDER), self.as_tuple(), strict=True))


@dataclass(frozen=True, slots=True)
class RoadSegment:
    edge_id: str
    source: str
    target: str
    distance_km: float
    free_flow_speed_kph: float
    fuel_litres_per_km: float
    safety_risk: float

    def __post_init__(self) -> None:
        if self.source == self.target:
            raise ValueError("Road segments must connect distinct nodes")
        if self.distance_km <= 0 or self.free_flow_speed_kph <= 0:
            raise ValueError("Distance and free-flow speed must be positive")
        if self.fuel_litres_per_km < 0 or self.safety_risk < 0:
            raise ValueError("Fuel and safety values must be non-negative")


@dataclass(frozen=True, slots=True)
class TrafficState:
    """Mutable-by-replacement traffic state for a single road segment."""

    speed_factor: float = 1.0
    congestion: float = 0.0
    incident: bool = False
    closed: bool = False

    def __post_init__(self) -> None:
        if not 0 < self.speed_factor <= 1:
            raise ValueError("speed_factor must be in (0, 1]")
        if not 0 <= self.congestion <= 1:
            raise ValueError("congestion must be in [0, 1]")


@dataclass(frozen=True, slots=True)
class Route:
    nodes: tuple[str, ...]
    edge_ids: tuple[str, ...]
    objectives: ObjectiveVector
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if len(self.nodes) < 2 or len(self.edge_ids) != len(self.nodes) - 1:
            raise ValueError("A route needs connected nodes and one edge per hop")

    @property
    def signature(self) -> tuple[str, ...]:
        """Structural identity used for archive de-duplication."""
        return self.nodes
