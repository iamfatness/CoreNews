# CoreNews review deployment

This stack runs the integrated app and PostgreSQL using the checked-out
revision. It initializes the research schema before the web app starts. The app
binds to the review host's loopback interface, and PostgreSQL stays on the
Compose network. This is intended for controlled reviews with workspace keys.

## Start a review build

1. Copy `.env.review.example` to `.env.review`. Set
   `CORENEWS_DB_PASSWORD` to a random hexadecimal value, set
   `RESEARCH_SIGNING_KEY` to an independent random secret of at least 32
   bytes, and add SHA-256 key digests to `RESEARCH_WORKSPACE_TOKEN_HASHES`
   as described in the [workspace setup](../README.md#research-cases-and-company-filings).
2. Run `docker compose --env-file .env.review -f compose.review.yml up -d --build`.
3. Check `http://127.0.0.1:8080/ready` before opening
   [the Research workspace](http://127.0.0.1:8080/research/). The ready
   endpoint checks the required database tables and columns.
4. For remote controlled review, front the loopback port with a managed HTTPS
   endpoint and access controls. Share each workspace's raw review key only with
   its designated testers.

The Compose stack keeps data in a named volume between restarts. Stop the
stack with `docker compose --env-file .env.review -f compose.review.yml down`.
Record the checkout SHA and back up the database before changing revisions.
Before rollback, verify the restored database and the previous app image
together in a disposable environment.

## Verify on the intended host

CI builds the review stack, imports synthetic OFAC snapshots, and exercises
workspace access, case evidence, saved investigation comparisons, a cited
report, and case activity. For a hosted review, run the following checks
against that deployment too.

| Area | Verification |
| --- | --- |
| Data sources | Query each enabled upstream from the intended host. Sample originals and check collected time, source time and attribution. Set SEC request identity and enable GDELT only after live verification. |
| Monitoring | Set `RESEARCH_WATCHES_ENABLED=true` after source verification and start the Compose stack with `--profile monitoring`. Observe a baseline, a new result, duplicate suppression and restart recovery. |
| Saved investigations | Enable run history for approved sources, save a workbench query to a case, compare another run after a source change, and add a cited finding. Check that an unavailable source preserves its baseline. |
| Screening | Import the original SDN XML, keep its SHA-256, and reproduce a source citation against the selected version. In a POSIX shell, run `docker compose --env-file .env.review -f compose.review.yml exec -T backend python -m app.ofac_catalog /dev/stdin < SDN.XML`. |
| Research workflow | Save original records to a case, verify a metadata hash for an approved source, cite evidence in a report, and inspect case activity. Open another workspace and verify its cases and activity are isolated. |
| Recovery | Restore a PostgreSQL backup in a disposable stack, check `/ready`, and reopen a saved case with its findings and evidence. |

Release approval also requires the canonical host, individual sign-in,
role and case access checks, and the design-partner beta. A healthy review
stack and fixture test establish that the packaged build runs.
