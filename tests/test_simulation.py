import unittest

from qroute.routing import fastest_route
from qroute.simulation import create_synthetic_scenario


class SimulationTests(unittest.TestCase):
    def test_incident_changes_route_cost_and_triggers_alternative_fastest_route(self) -> None:
        scenario = create_synthetic_scenario(seed=11)
        before = fastest_route(scenario.graph, scenario.source, scenario.destination)
        events = scenario.simulator.advance_to(1)
        after = fastest_route(scenario.graph, scenario.source, scenario.destination)
        self.assertIn("SYNTHETIC", events[0].description)
        self.assertEqual(before.nodes, ("A", "B", "D"))
        self.assertEqual(after.nodes, ("A", "C", "D"))
        self.assertGreater(scenario.graph.network.edge("B", "D")["travel_time_hours"], before.objectives.time)

    def test_synthetic_scenario_is_deterministic_for_a_seed(self) -> None:
        first = create_synthetic_scenario(seed=19)
        second = create_synthetic_scenario(seed=19)
        self.assertEqual(fastest_route(first.graph, "A", "D").objectives, fastest_route(second.graph, "A", "D").objectives)
