"""Pareto dominance, ranking, archive management, and diversity preservation."""

from __future__ import annotations

from dataclasses import dataclass
from math import inf
from typing import Iterable

from .config import ParetoConfig
from .models import OBJECTIVE_ORDER, Route


def dominates(left: Route, right: Route) -> bool:
    left_values = left.objectives.as_tuple()
    right_values = right.objectives.as_tuple()
    return all(a <= b for a, b in zip(left_values, right_values, strict=True)) and any(
        a < b for a, b in zip(left_values, right_values, strict=True)
    )


def pareto_ranks(routes: Iterable[Route]) -> dict[tuple[str, ...], int]:
    """Return non-dominated-front rank for each route signature (zero is best)."""
    remaining = list(routes)
    ranks: dict[tuple[str, ...], int] = {}
    rank = 0
    while remaining:
        front = [route for route in remaining if not any(dominates(other, route) for other in remaining if other is not route)]
        for route in front:
            ranks[route.signature] = rank
        remaining = [route for route in remaining if route not in front]
        rank += 1
    return ranks


def crowding_distances(routes: Iterable[Route]) -> dict[tuple[str, ...], float]:
    route_list = list(routes)
    distances = {route.signature: 0.0 for route in route_list}
    if len(route_list) <= 2:
        return {route.signature: inf for route in route_list}
    for index in range(len(OBJECTIVE_ORDER)):
        ordered = sorted(route_list, key=lambda route: route.objectives.as_tuple()[index])
        distances[ordered[0].signature] = inf
        distances[ordered[-1].signature] = inf
        low = ordered[0].objectives.as_tuple()[index]
        high = ordered[-1].objectives.as_tuple()[index]
        if high == low:
            continue
        for position in range(1, len(ordered) - 1):
            signature = ordered[position].signature
            if distances[signature] != inf:
                before = ordered[position - 1].objectives.as_tuple()[index]
                after = ordered[position + 1].objectives.as_tuple()[index]
                distances[signature] += (after - before) / (high - low)
    return distances


@dataclass(frozen=True, slots=True)
class ArchiveEntry:
    route: Route
    rank: int
    crowding_distance: float


class ParetoArchive:
    """Bounded archive that removes structural duplicates before selection."""

    def __init__(self, config: ParetoConfig = ParetoConfig()) -> None:
        self.config = config
        self._routes: dict[tuple[str, ...], Route] = {}

    def add_all(self, candidates: Iterable[Route]) -> None:
        combined = dict(self._routes)
        for candidate in candidates:
            incumbent = combined.get(candidate.signature)
            if incumbent is None or dominates(candidate, incumbent):
                combined[candidate.signature] = candidate
        non_dominated = {
            signature: route
            for signature, route in combined.items()
            if not any(dominates(other, route) for other in combined.values() if other is not route)
        }
        if len(non_dominated) > self.config.archive_size:
            diversity = crowding_distances(non_dominated.values())
            keep = sorted(
                non_dominated.values(),
                key=lambda route: (-diversity[route.signature], route.nodes),
            )[: self.config.archive_size]
            non_dominated = {route.signature: route for route in keep}
        self._routes = non_dominated

    def entries(self) -> list[ArchiveEntry]:
        routes = list(self._routes.values())
        ranks = pareto_ranks(routes)
        diversity = crowding_distances(routes)
        return sorted(
            (ArchiveEntry(route, ranks[route.signature], diversity[route.signature]) for route in routes),
            key=lambda entry: (entry.rank, -entry.crowding_distance, entry.route.nodes),
        )

    def routes(self) -> list[Route]:
        return [entry.route for entry in self.entries()]
