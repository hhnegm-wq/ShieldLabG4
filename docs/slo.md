# SLOs

| Indicator                           | Target (per 30 d) | Notes                                  |
|-------------------------------------|-------------------|----------------------------------------|
| API availability (`GET /`)          | 99.9 %            | Excluding announced maintenance        |
| API p95 latency, lightweight calls  | < 250 ms          | `/api/v1/version`, `/api/v1/shielding` |
| API p95 latency, compute calls      | < 5 s             | `/api/v1/compare` (≤ 8 materials)      |
| Worker job p95 turnaround           | < 10 min          | Default 100 k-history slab study       |
| Job success rate                    | ≥ 99 %            | Excludes user input errors             |
| Data durability                     | 11 nines          | Inherited from Azure GZRS              |
| Mean Time To Recovery (MTTR)        | < 1 h             | For Sev-1 incidents                    |
| Recovery Point Objective (RPO)      | ≤ 15 min          |                                        |
| Recovery Time Objective (RTO)       | ≤ 4 h             |                                        |

Error budget = 1 - SLO. Burn-rate alerts fire at 2× and 10× the budget.

Status page: `https://status.shieldlab-g4.invalid` (Phase 4 deliverable).
