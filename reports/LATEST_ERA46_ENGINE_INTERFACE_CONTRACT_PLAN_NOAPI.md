# ERA46 ENGINE INTERFACE CONTRACT PLAN NOAPI

- Created UTC: 2026-07-08T08:35:33.670683+00:00
- Status: `PLANNED_NEXT`
- Purpose: define Runtime → Discipline Layer read-only interface before implementation.

## Core Rule

`Runtime never imports Lab.`

Lab may inspect Runtime outputs. Runtime must never depend on Lab.

## Engines

- Performance Metrics Engine
- Reliability Engine
- Security Boundary Engine
- Scalability Engine
- Opportunity Cost Engine
- Statistical Decision Engine
- Governance Delta Engine
- Immutable Audit Log

## Statistical Requirements

- Single measurement forbidden.
- Initial minimum sample size: 30.
- Required: mean, median, min, max, variance, standard deviation, standard error, p95, p99, confidence interval.
- Backlog: bootstrap, Bayesian update, Monte Carlo, control charts, change-point detection.
- Pareto frontier is not initial scope.

## Opportunity Cost

Every component must satisfy:

`Net Benefit = Benefit - Opportunity Cost`

If Net Benefit is negative, non-critical feature is rejected.
