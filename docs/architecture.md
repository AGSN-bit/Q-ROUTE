# Q-ROUTE Phase 1 Architecture

## Canonical objective contract

Every route is evaluated as a named `ObjectiveVector`. Any array or tuple
representation uses this fixed minimisation order:

`[TIME, CONGESTION, DISTANCE, FUEL, EMISSIONS, SAFETY]`

This order is exported as `OBJECTIVE_ORDER`; modules must not define a local
alternative. Time is measured in hours, distance in kilometres, fuel in
litres, emissions in kilograms of CO2-equivalent, and safety is an additive
risk score. Congestion is an additive segment-cost score in Phase 1.

## Pipeline contract

```text
Candidate Generation
        -> Multi-Objective Evaluation
        -> Quantum-Inspired Search
        -> ACO Route Search / Refinement
        -> Pareto Archive
        -> Decision / Ranking
```

`optimization.contracts` makes every stage explicit. `QuantumInspiredSearch`
owns probabilistic candidate representation, initialisation, candidate
generation, state update, diversity/exploration, convergence, and termination.
`AcoRefiner` owns pheromone initialisation, heuristic access, feasible
source-to-destination path construction with an explicit visited-node set for
loop prevention, evaporation, deposition, and route refinement. Neither
interface imports or assumes the other, so the following
ablations remain possible without architectural changes:

- classical baselines;
- ACO only;
- quantum-inspired search only where meaningful;
- the Q-ROUTE hybrid, wired through the two interfaces.

Phase 1 defines and tests the contracts but does not claim an ACO or quantum
performance result. Those implementations belong to the next research phase.

## Dynamic graph and rerouting

`DynamicRoadGraph` keeps one lightweight directed-graph instance. Traffic updates
replace state for affected edge IDs and refresh only their derived attributes;
the surrounding application and graph do not need rebuilding. Closed links are
excluded from route construction. A later optimisation orchestrator can reuse
this instance when re-optimising after an update.

## Pareto and decisions

`ParetoArchive` removes structural duplicates, retains only non-dominated
routes, calculates crowding distance for diversity, and applies a configurable
archive bound. Routes carry their algorithm and objective-order metadata.
Decision ranking is separate, normalises objectives across the current archive,
and accepts explicit preferences rather than silently collapsing objectives.

## Data boundary

Phase 1 uses only the labelled `SYNTHETIC deterministic incident reroute`
scenario. `TrafficSimulator` applies deterministic traffic events locally.
There are no external traffic providers, messaging systems, cameras, weather
feeds, machine-learning predictors, web APIs, or frontend components.

To make this first foundation runnable without package installation, the graph
and test runner use only the Python standard library. The documented NetworkX
technology remains compatible with the `DynamicRoadGraph` boundary and can be
introduced in a later phase without altering the objective or optimizer
contracts.
