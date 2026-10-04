"""A dynamic road graph whose traffic state can change in place."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from .models import RoadSegment, TrafficState


class DirectedRoadNetwork:
    """Small directed graph abstraction for deterministic local simulations."""

    def __init__(self) -> None:
        self._adjacency: dict[str, dict[str, dict[str, object]]] = {}

    def add_edge(self, source: str, target: str, **data: object) -> None:
        self._adjacency.setdefault(source, {})[target] = data
        self._adjacency.setdefault(target, {})

    def has_edge(self, source: str, target: str) -> bool:
        return target in self._adjacency.get(source, {})

    def edge(self, source: str, target: str) -> dict[str, object]:
        return self._adjacency[source][target]

    def neighbors(self, node: str) -> Mapping[str, dict[str, object]]:
        return self._adjacency.get(node, {})

    def edges(self) -> Iterable[tuple[str, str, dict[str, object]]]:
        for source, targets in self._adjacency.items():
            for target, data in targets.items():
                yield source, target, data

    def number_of_edges(self) -> int:
        return sum(len(targets) for targets in self._adjacency.values())


class DynamicRoadGraph:
    def __init__(self, segments: Iterable[RoadSegment]) -> None:
        self.network = DirectedRoadNetwork()
        self._segments: dict[str, RoadSegment] = {}
        self._state: dict[str, TrafficState] = {}
        for segment in segments:
            if segment.edge_id in self._segments:
                raise ValueError(f"Duplicate edge id: {segment.edge_id}")
            if self.network.has_edge(segment.source, segment.target):
                raise ValueError("Phase 1 graph supports one directed segment per node pair")
            self._segments[segment.edge_id] = segment
            self._state[segment.edge_id] = TrafficState()
            self.network.add_edge(segment.source, segment.target, edge_id=segment.edge_id)
            self._refresh_edge(segment.edge_id)

    @property
    def segments(self) -> Mapping[str, RoadSegment]:
        return self._segments

    def state_for(self, edge_id: str) -> TrafficState:
        return self._state[edge_id]

    def update_traffic(self, changes: Mapping[str, TrafficState]) -> None:
        """Update only affected edge attributes; the graph instance is retained."""
        unknown = set(changes).difference(self._segments)
        if unknown:
            raise KeyError(f"Unknown edge ids: {sorted(unknown)}")
        for edge_id, state in changes.items():
            self._state[edge_id] = state
            self._refresh_edge(edge_id)

    def edge_id_between(self, source: str, target: str) -> str:
        return str(self.network.edge(source, target)["edge_id"])

    def is_open(self, edge_id: str) -> bool:
        return not self._state[edge_id].closed

    def _refresh_edge(self, edge_id: str) -> None:
        segment = self._segments[edge_id]
        state = self._state[edge_id]
        data = self.network.edge(segment.source, segment.target)
        speed_kph = segment.free_flow_speed_kph * state.speed_factor
        data.update(
            distance_km=segment.distance_km,
            travel_time_hours=segment.distance_km / speed_kph,
            congestion=state.congestion,
            fuel_litres=segment.distance_km * segment.fuel_litres_per_km * (1 + 0.2 * state.congestion),
            emissions_kg=segment.distance_km
            * segment.fuel_litres_per_km
            * (1 + 0.2 * state.congestion)
            * 2.31,
            safety_risk=segment.safety_risk + (0.25 if state.incident else 0.0),
            closed=state.closed,
        )
