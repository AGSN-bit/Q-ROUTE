import unittest

from qroute.models import ObjectiveVector, Route
from qroute.pareto import ParetoArchive, dominates, pareto_ranks


def route(nodes: tuple[str, ...], values: tuple[float, ...]) -> Route:
    return Route(nodes=nodes, edge_ids=tuple(f"e{index}" for index in range(len(nodes) - 1)), objectives=ObjectiveVector(*values))


class ParetoTests(unittest.TestCase):
    def test_dominance_and_non_dominated_ranks(self) -> None:
        best = route(("A", "B"), (1, 1, 1, 1, 1, 1))
        worse = route(("A", "C"), (2, 2, 2, 2, 2, 2))
        tradeoff = route(("A", "D"), (0.5, 3, 3, 3, 3, 3))
        self.assertTrue(dominates(best, worse))
        self.assertFalse(dominates(best, tradeoff))
        self.assertEqual(pareto_ranks([best, worse, tradeoff])[worse.signature], 1)

    def test_archive_removes_duplicates_and_preserves_non_dominated_routes(self) -> None:
        archive = ParetoArchive()
        duplicate_a = route(("A", "B"), (1, 1, 1, 1, 1, 1))
        duplicate_b = route(("A", "B"), (2, 2, 2, 2, 2, 2))
        tradeoff = route(("A", "C"), (0.5, 3, 3, 3, 3, 3))
        archive.add_all([duplicate_a, duplicate_b, tradeoff])
        entries = archive.entries()
        self.assertEqual(len(entries), 2)
        self.assertEqual({entry.route.nodes for entry in entries}, {("A", "B"), ("A", "C")})
        self.assertTrue(all(entry.rank == 0 for entry in entries))
