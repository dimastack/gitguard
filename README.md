# GitGuard — Automated tests for Git client/server interactions

[![CI](https://github.com/dimastack/gitguard/actions/workflows/ci.yml/badge.svg)](https://github.com/dimastack/gitguard/actions/workflows/ci.yml)
[![Allure Report](https://img.shields.io/badge/Allure-Report-blue)](https://dimastack.github.io/gitguard/)

## Goal
GitGuard is an end-to-end testing framework for Git client ↔ Git server interactions.
It focuses on verifying the basic Git workflows (clone, commit, push, pull, branch, fetch, status) and the server API (Gitea) behavior for user/repo/org administration.

## Task
The task is to write a test or set of tests that test the Git software. You are free to use available
frameworks; how you test it is up to you. Use your best judgment!
If you don’t have any experience with Git, feel free to choose another client/server protocol (for
example, HTTP or FTP) and test this instead.
You can assume that the software has no existing tests. Your task is to select the areas that
must be tested first and implement these. One important part that needs to be tested is
communication between a Git client and a Git server (we can assume that two hosts will be
used for this, one acting as a client and one as a server).
We are not looking for complete coverage but tests that implement the basics. You can take
shortcuts where a certain implementation would take a long time. In this case, describe how the
solution would be implemented instead.
After the basic set of tests has been implemented, describe what the second phase of the test
implementation would be, and also describe the requirements of the system that would run
these tests in a continuous integration manner.

## Preparation and thoughts
Home solution:
Initially, I had another plan: I wished to run Git client on local VM (CI runner) and run Git server (Gitea) inside the Docker. This way on CI I planned to use different runner OS's to run
the tests via matrix 'OSs/git client versions/protocols'. But in such case I was made to work via
localhost which technically break task requirements.
So in the result I decided to orginize infrastructure as 2 Docker containers connected via network in bridge mode - means 2 different hosts with 2 different IPs.
I tried to complete the task as complex solution with unit tests, e2e, clients, infrastructure.
Real life solution:
In case I need to test Git clients and server in reality, I'd preffered next way:
1) Separate dev teams works on each version of Git client (per OS) and one works with server code.
2) All the teams write unit tests (I added them here just to show they should be stage 0)
3) We deploy server code on test environment somewhere in eg AWS.
4) I use let's say Github Actions or Gitlab CI to run tests from Runner VM with different OS's with installed python and git client in matrix against Git server running on AWS.

## Why two-container architecture
We must test communication between **two separate hosts** — a Git client and a Git server — to match the assignment requirements. Running both roles in different Docker containers (`tester` and `gitea`) gives:
- deterministic networking (services communicate by DNS in the compose network),
- reproducible test environments (same image used locally and in CI),
- ability to vary client git versions by building different tester images,
- isolation: tester contains git + python + tests, gitea contains server only.

## Architecture

```
+----------------------+        docker network         +----------------------+
|   tester (container) | <---------------------------> |  gitea (container)   |
|  - python, pytest    |                               |  - Gitea server      |
|  - git               |                               |  - API (http/ssh/git)|
|  - tests (pytest)    |                               |                      |
+----------------------+                               +----------------------+
            |                                                   |
            |   Allure results (volume)                         |
            |-- ./allure-results <------------------------------|
```

## Project structure (important)
```
gitguard/
├─ clients/
│  ├─ git_client.py
│  ├─ http_client.py
│  ├─ http_gitea_client.py
│  └─ ssh_client.py
├─ docker/
│  └─ tester/Dockerfile
├─ scripts/
│  ├─ wait_for_gitea.sh
│  └─ init_gitea.sh
├─ tests/
│  ├─ conftest.py
│  └─ e2e/
│     └─ api/
│        ├─ cli/
│        └─ server/
├─ docker-compose.yml
├─ pytest.ini
├─ requirements.txt
└─ .github/workflows/ci.yml
```

## How tests are organized
- `tests/unit` — unit tests
- `tests/e2e/api/cli` — e2e scenarios using `GitClient` (clone/commit/push/pull/branch/status/fetch)
- `tests/e2e/api/server` — e2e scenarios using `GiteaHttpClient` (users, repos, orgs, admin)
- `tests/e2e/ui` — (future) UI tests (Playwright/Selenium)

## Quickstart (local)
1. Install Docker & docker-compose.
2. Ensure `configs/local.env` contains any needed envs (or set env vars).
3. Build tester image:
   ```bash
   docker build -t gitguard/tester -f docker/tester/Dockerfile .
   ```
4. Start stack:
   ```bash
   docker-compose up -d --build
   ./scripts/wait_for_gitea.sh
   docker exec tester bash -lc "/app/scripts/init_gitea.sh"
   ```
5. Run tests inside tester:
   ```bash
   docker exec tester pytest -v --alluredir=/app/allure-results tests/unit
   docker exec tester pytest -v --alluredir=/app/allure-results tests/e2e/api
   ```
6. Generate Allure report:
   ```bash
   allure generate allure-results -o allure-report --clean
   allure open allure-report
   ```

## CI (GitHub Actions)
- The workflow builds `tester`, starts services (docker-compose), waits for Gitea, runs `init_gitea.sh` inside `tester`, runs unit → e2e/api → (optional) e2e/ui, and uploads Allure results as artifacts.
- Add `GITEA_ADMIN_TOKEN` to repository secrets for API initialization.

## What was tested first (MVP)
- Core Git operations (clone, init, add, commit, push, pull, fetch, branch, checkout, status).
- Gitea API: create/delete users, create/delete repos, list orgs, admin endpoints.
- Communication between client and server over supported protocols (http, ssh, git).
- Basic negative scenarios (invalid repo, non-existent user, invalid payload).

## Shortcuts / assumptions
- We use Gitea for server; initialization is best-effort by `init_gitea.sh`. On CI pass `GITEA_ADMIN_TOKEN` to allow API-based setup.
- SSH keys are generated at start and shared between tester and gitea (via scripts/compose). This is implemented as a best-effort in `init_gitea.sh` and docker-compose mounts.

## Second phase (roadmap)
1. **Expand test coverage**: add edge cases, large-file pushes, submodules.
2. **Performance & stress**: scripted parallel pushes/fetches, large repos, measure latencies.
3. **UI tests**: Playwright tests for login / repo creation / web UI flows.
4. **Security tests**: RBAC, token expiry, CSRF, input validation fuzzing.
5. **Chaos testing**: network partition, disk I/O throttle, restart gitea during push.
6. **Matrix builds**: add multiple tester images (different Git versions) and runner targets (Linux/macOS/Windows).

## CI runner / infra requirements
- Docker & docker-compose available (for running services).
- Secrets access for `GITEA_ADMIN_TOKEN`.
- Optionally Allure CLI installed to publish HTML report.
- Runners for UI tests require browser support (Playwright).

## Notes & troubleshooting
- If tests fail due to Gitea initial setup, check `allure-results` and `artifacts/git-client-*.log`.
- If SSH fails — verify keys present and that `GIT_SSH_COMMAND` is configured to bypass host checking.
