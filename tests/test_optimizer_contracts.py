import unittest
from inspect import isabstract

from qroute.optimization.contracts import AcoRefiner, QuantumInspiredSearch


class OptimizerContractTests(unittest.TestCase):
    def test_quantum_contract_exposes_search_lifecycle(self) -> None:
        required = {"initialize", "generate_candidates", "evaluate_candidates", "update", "exploration_ratio", "convergence", "should_terminate"}
        self.assertTrue(required.issubset(QuantumInspiredSearch.__abstractmethods__))
        self.assertTrue(isabstract(QuantumInspiredSearch))

    def test_aco_contract_exposes_modular_refinement_lifecycle(self) -> None:
        required = {"initialize_pheromones", "heuristic", "construct_feasible_path", "evaporate", "deposit", "refine"}
        self.assertTrue(required.issubset(AcoRefiner.__abstractmethods__))
        self.assertTrue(isabstract(AcoRefiner))
