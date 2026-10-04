"""Small, local-only Phase 1 demonstration command."""

from __future__ import annotations

import argparse
import json

from .pareto import ParetoArchive
from .routing import fastest_route, generate_candidates, rank_routes, shortest_distance
from .simulation import create_synthetic_scenario


def _route_summary(route: object) -> dict[str, object]:
    from .models import Route

    assert isinstance(route, Route)
    return {"nodes": route.nodes, "algorithm": route.metadata["algorithm"], "objectives": route.objectives.as_dict()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the deterministic synthetic Q-ROUTE Phase 1 scenario.")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args(argv)
    scenario = create_synthetic_scenario(args.seed)
    before = [shortest_distance(scenario.graph, scenario.source, scenario.destination), fastest_route(scenario.graph, scenario.source, scenario.destination)]
    scenario.simulator.advance_to(1)
    after = [shortest_distance(scenario.graph, scenario.source, scenario.destination), fastest_route(scenario.graph, scenario.source, scenario.destination)]
    archive = ParetoArchive()
    archive.add_all(generate_candidates(scenario.graph, scenario.source, scenario.destination))
    payload = {
        "scenario": scenario.label,
        "seed": scenario.seed,
        "synthetic": True,
        "before_incident": [_route_summary(route) for route in before],
        "after_incident": [_route_summary(route) for route in after],
        "pareto_routes": [_route_summary(route) for route in rank_routes(archive.routes())],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0
