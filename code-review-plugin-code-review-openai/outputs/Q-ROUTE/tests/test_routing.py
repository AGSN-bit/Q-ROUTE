import unittest

from qroute.routing import evaluate_route, fastest_route, is_feasible, shortest_distance
from qroute.simulation import create_synthetic_scenario


class RoutingTests(unittest.TestCase):
    def test_baselines_and_route_feasibility(self) -> None:
        scenario = create_synthetic_scenario()
        distance_route = shortest_distance(scenario.graph, scenario.source, scenario.destination)
        fastest = fastest_route(scenario.graph, scenario.source, scenario.destination)
        self.assertEqual(distance_route.nodes, ("A", "B", "D"))
        self.assertEqual(fastest.nodes, ("A", "B", "D"))
        self.assertTrue(is_feasible(scenario.graph, fastest.nodes, "A", "D"))
        self.assertFalse(is_feasible(scenario.graph, ("A", "B", "A", "D"), "A", "D"))

    def test_objective_calculation_uses_named_canonical_fields(self) -> None:
        scenario = create_synthetic_scenario()
        route = evaluate_route(scenario.graph, ("A", "B", "D"), algorithm="test")
        self.assertEqual(route.objectives.distance, 8.0)
        self.assertGreater(route.objectives.time, 0)
        self.assertGreater(route.objectives.fuel, 0)
        self.assertGreater(route.objectives.emissions, route.objectives.fuel)
        self.assertEqual(route.metadata["objective_order"][-1], "SAFETY")
