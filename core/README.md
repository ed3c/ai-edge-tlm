# Host-owned deterministic DAG core

Production planning authority stays in the host. Model-suggested plans are candidate data and must pass `PlanValidator` before execution.

The first slice provides bounded acyclic compilation, deterministic order, retries, explicit fallback, cancellation/deadline propagation, stable external-effect operation IDs, stale-subject rejection, ToolBroker admission, compensation, and terminal evidence receipts.

Fake-provider tests prove deterministic core behavior only; they do not prove provider/device availability, performance, privacy, power, or thermal behavior.
