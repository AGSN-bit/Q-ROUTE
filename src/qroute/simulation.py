"""Deterministic, explicitly synthetic traffic network and event simulator."""

from __future__ import annotations

from dataclasses import dataclass

from .graph import DynamicRoadGraph
from .models import RoadSegment, TrafficState


@dataclass(frozen=True, slots=True)
class TrafficEvent:
    tick: int
    description: str
    changes: dict[str, TrafficState]


class TrafficSimulator:
    def __init__(self, graph: DynamicRoadGraph, events: tuple[TrafficEvent, ...]) -> None:
        self.graph = graph
        self.events = tuple(sorted(events, key=lambda event: event.tick))
        self.tick = 0

    def advance_to(self, tick: int) -> list[TrafficEvent]:
        if tick < self.tick:
            raise ValueError("TrafficSimulator cannot rewind; create a new scenario for replay")
        applied: list[TrafficEvent] = []
        for event in self.events:
            if self.tick < event.tick <= tick:
                self.graph.update_traffic(event.changes)
                applied.append(event)
        self.tick = tick
        return applied


@dataclass(frozen=True, slots=True)
class SyntheticScenario:
    label: str
    seed: int
    source: str
    destination: str
    graph: DynamicRoadGraph
    simulator: TrafficSimulator


def create_synthetic_scenario(seed: int = 7) -> SyntheticScenario:
    """A fully local, deterministic scenario; it contains no external data."""
    segments = (
        RoadSegment("A_B", "A", "B", 4.0, 60.0, 0.075, 0.08),
        RoadSegment("B_D", "B", "D", 4.0, 60.0, 0.075, 0.08),
        RoadSegment("A_C", "A", "C", 5.0, 65.0, 0.070, 0.06),
        RoadSegment("C_D", "C", "D", 5.0, 65.0, 0.070, 0.06),
        RoadSegment("A_E", "A", "E", 6.0, 55.0, 0.068, 0.05),
        RoadSegment("E_D", "E", "D", 5.0, 55.0, 0.068, 0.05),
    )
    graph = DynamicRoadGraph(segments)
    graph.update_traffic(
        {
            "A_B": TrafficState(speed_factor=0.85, congestion=0.20),
            "B_D": TrafficState(speed_factor=0.80, congestion=0.25),
            "A_C": TrafficState(speed_factor=0.90, congestion=0.10),
            "C_D": TrafficState(speed_factor=0.95, congestion=0.08),
        }
    )
    events = (
        TrafficEvent(
            tick=1,
            description="SYNTHETIC: incident on B_D increases congestion and travel time",
            changes={"B_D": TrafficState(speed_factor=0.20, congestion=0.95, incident=True)},
        ),
        TrafficEvent(
            tick=2,
            description="SYNTHETIC: incident clearance restores B_D traffic flow",
            changes={"B_D": TrafficState(speed_factor=0.80, congestion=0.25)},
        ),
    )
    simulator = TrafficSimulator(graph, events)
    return SyntheticScenario("SYNTHETIC deterministic incident reroute", seed, "A", "D", graph, simulator)
