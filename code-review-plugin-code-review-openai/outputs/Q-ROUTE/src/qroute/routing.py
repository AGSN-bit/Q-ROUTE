"""Feasible route construction, evaluation, baselines, and decision ranking."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
import heapq

from .graph import DynamicRoadGraph
from .models import OBJECTIVE_ORDER, ObjectiveVector, Route


def is_feasible(graph: DynamicRoadGraph, nodes: tuple[str, ...], source: str, destination: str) -> bool:
    if len(nodes) < 2 or nodes[0] != source or nodes[-1] != destination:
        return False
    if len(set(nodes)) != len(nodes):
        return False
    return all(
        graph.network.has_edge(start, end) and not bool(graph.network.edge(start, end)["closed"])
        for start, end in zip(nodes, nodes[1:])
    )


def evaluate_route(graph: DynamicRoadGraph, nodes: Iterable[str], *, algorithm: str) -> Route:
    path = tuple(nodes)
    if len(path) < 2:
        raise ValueError("A route needs at least a source and destination")
    edge_ids: list[str] = []
    totals = {name: 0.0 for name in OBJECTIVE_ORDER}
    for start, end in zip(path, path[1:]):
        if not graph.network.has_edge(start, end):
            raise ValueError(f"No road segment from {start} to {end}")
        edge = graph.network.edge(start, end)
        if edge["closed"]:
            raise ValueError(f"Road segment {edge['edge_id']} is closed")
        edge_ids.append(str(edge["edge_id"]))
        totals[OBJECTIVE_ORDER[0]] += float(edge["travel_time_hours"])
        totals[OBJECTIVE_ORDER[1]] += float(edge["congestion"])
        totals[OBJECTIVE_ORDER[2]] += float(edge["distance_km"])
        totals[OBJECTIVE_ORDER[3]] += float(edge["fuel_litres"])
        totals[OBJECTIVE_ORDER[4]] += float(edge["emissions_kg"])
        totals[OBJECTIVE_ORDER[5]] += float(edge["safety_risk"])
    return Route(
        nodes=path,
        edge_ids=tuple(edge_ids),
        objectives=ObjectiveVector(*tuple(totals[name] for name in OBJECTIVE_ORDER)),
        metadata={"algorithm": algorithm, "objective_order": tuple(item.value for item in OBJECTIVE_ORDER)},
    )


def _shortest_path(graph: DynamicRoadGraph, source: str, destination: str, weight: str) -> tuple[str, ...]:
    queue: list[tuple[float, tuple[str, ...]]] = [(0.0, (source,))]
    best: dict[str, float] = {source: 0.0}
    while queue:
        cost, path = heapq.heappop(queue)
        node = path[-1]
        if node == destination:
            return path
        if cost > best.get(node, float("inf")):
            continue
        for target, edge in graph.network.neighbors(node).items():
            if bool(edge["closed"]) or target in path:
                continue
            candidate_cost = cost + float(edge[weight])
            if candidate_cost < best.get(target, float("inf")):
                best[target] = candidate_cost
                heapq.heappush(queue, (candidate_cost, (*path, target)))
    raise ValueError(f"No open route from {source} to {destination}")


def shortest_distance(graph: DynamicRoadGraph, source: str, destination: str) -> Route:
    nodes = _shortest_path(graph, source, destination, "distance_km")
    return evaluate_route(graph, nodes, algorithm="shortest-distance")


def fastest_route(graph: DynamicRoadGraph, source: str, destination: str) -> Route:
    nodes = _shortest_path(graph, source, destination, "travel_time_hours")
    return evaluate_route(graph, nodes, algorithm="fastest-current-travel-time")


def generate_candidates(graph: DynamicRoadGraph, source: str, destination: str, limit: int = 5) -> list[Route]:
    """Deterministic simple-path candidate generation for Phase 1 experiments."""
    if limit <= 0:
        return []
    candidates: list[Route] = []
    def visit(path: tuple[str, ...]) -> None:
        node = path[-1]
        if node == destination:
            candidates.append(evaluate_route(graph, path, algorithm="deterministic-candidate-generator"))
            return
        for target, edge in graph.network.neighbors(node).items():
            if not bool(edge["closed"]) and target not in path:
                visit((*path, target))

    visit((source,))
    return sorted(candidates, key=lambda route: (route.objectives.time, route.nodes))[:limit]


def rank_routes(routes: Iterable[Route], preferences: Mapping[str, float] | None = None) -> list[Route]:
    """Rank a Pareto set by normalised, explicit decision preferences."""
    route_list = list(routes)
    if not route_list:
        return []
    weights = {name.value: 1.0 for name in OBJECTIVE_ORDER}
    if preferences:
        unknown = set(preferences).difference(weights)
        if unknown:
            raise KeyError(f"Unknown preferences: {sorted(unknown)}")
        weights.update(preferences)
    maxima = [max(route.objectives.as_tuple()[index] for route in route_list) for index in range(len(OBJECTIVE_ORDER))]

    def score(route: Route) -> float:
        return sum(
            weights[name.value] * value / maximum if maximum else 0.0
            for name, value, maximum in zip(OBJECTIVE_ORDER, route.objectives.as_tuple(), maxima, strict=True)
        )

    return sorted(route_list, key=lambda route: (score(route), route.nodes))
