# Gate-bundle fixtures

Six synthetic feature bundles in the shape the lifecycle checks read (`spec.md`, `plan.md`,
`tasks.md`, `gates/verify.md`, `gates/closeout.md`). The tests copy a bundle into a scratch git
repository, so nothing here depends on a live service. All content is synthetic; tracker-style
identifiers are invented.

| Bundle | Scenario |
| --- | --- |
| `deferred-post-deploy-captured` | A post-deployment proof is deferred with a durable record |
| `deferred-missing-captured-as` | A post-deployment proof is deferred without a durable record |
| `mandatory-failure-deferral-attempt` | A mandatory proof failed and deferral is attempted |
| `pre-merge-needs-deployment` | A pre-merge proof mode depends on a deployed environment |
| `high-risk-missing-accepted-by` | A high-risk deferral has no named acceptor |
| `legacy-no-stage` | Bundle written before stage and evidence class existed |

The current scripts read only the verify mode status and the closeout decision; the expected result
for each bundle is recorded in `tests/test_stage_evidence_fixtures_contract.py`.
