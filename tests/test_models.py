import unittest

from qroute.models import OBJECTIVE_ORDER, ObjectiveVector, RoadSegment


class ModelTests(unittest.TestCase):
    def test_objective_vector_has_one_canonical_named_order(self) -> None:
        objectives = ObjectiveVector(1, 2, 3, 4, 5, 6)
        self.assertEqual(tuple(item.value for item in OBJECTIVE_ORDER), ("TIME", "CONGESTION", "DISTANCE", "FUEL", "EMISSIONS", "SAFETY"))
        self.assertEqual(objectives.as_tuple(), (1, 2, 3, 4, 5, 6))
        self.assertEqual(objectives.as_dict()["EMISSIONS"], 5)

    def test_models_reject_invalid_values(self) -> None:
        with self.assertRaises(ValueError):
            ObjectiveVector(-1, 0, 0, 0, 0, 0)
        with self.assertRaises(ValueError):
            RoadSegment("bad", "A", "A", 1, 30, 0.1, 0.1)
