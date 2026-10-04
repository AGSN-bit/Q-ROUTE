import unittest

from qroute.models import TrafficState
from qroute.routing import fastest_route
from qroute.simulation import create_synthetic_scenario


class GraphTests(unittest.TestCase):
    def test_graph_construction_and_in_place_dynamic_update(self) -> None:
        scenario = create_synthetic_scenario()
        graph_identity = id(scenario.graph.network)
        before = fastest_route(scenario.graph, "A", "D")
        scenario.graph.update_traffic({"B_D": TrafficState(speed_factor=0.20, congestion=0.95, incident=True)})
        after = fastest_route(scenario.graph, "A", "D")
        self.assertEqual(id(scenario.graph.network), graph_identity)
        self.assertEqual(scenario.graph.network.number_of_edges(), 6)
        self.assertEqual(before.nodes, ("A", "B", "D"))
        self.assertEqual(after.nodes, ("A", "C", "D"))
