# refactor-arch — Automated Architectural Refactoring Skill

A Claude Code **Skill** (`refactor-arch`) that analyzes a backend codebase, audits it against an
anti-pattern catalog, asks for confirmation, refactors it to the **MVC** pattern and validates that
the application still boots and answers its endpoints. It is technology-agnostic and was exercised on
three legacy projects:

| # | Project | Stack | Domain |
|---|---|---|---|
| 1 | [`code-smells-project/`](code-smells-project) | Python / Flask | E-commerce API |
| 2 | [`ecommerce-api-legacy/`](ecommerce-api-legacy) | Node.js / Express | LMS API with checkout flow |
| 3 | [`task-manager-api/`](task-manager-api) | Python / Flask + SQLAlchemy | Task manager API |

The skill lives in `.claude/skills/refactor-arch/` inside each project (one source, three identical
copies). The audit reports produced by Phase 2 are in [`reports/`](reports). The raw evidence of the
runs (transcripts, original-code baselines, smoke-test specs and results) is in [`tmp/`](tmp).

> [`README.md`](README.md) keeps the challenge statement untouched. This file documents the solution.

Contents: [Análise Manual](#análise-manual) · [Construção da Skill](#construção-da-skill) ·
[Resultados](#resultados) · [Como Executar](#como-executar)

---

## Análise Manual

Done by reading every source file **before** writing the skill, to learn which patterns the skill
has to detect. Severity scale: CRITICAL (security or total collapse of separation), HIGH (strong
MVC/SOLID violation or data-integrity risk), MEDIUM (duplication, N+1, missing validation,
deprecated APIs), LOW (readability). Line numbers are exact.

### Project 1 — `code-smells-project` (Python/Flask)

| # | Severity | Location | Problem | Why it matters |
|---|---|---|---|---|
| 1 | CRITICAL | `app.py:7`, `controllers.py:289` | Hardcoded `SECRET_KEY`, and `/health` echoes it in its JSON. | Anyone with the repo, or anyone who calls `/health`, holds the signing key; rotating it needs a code change. |
| 2 | CRITICAL | `models.py:28, 47-50, 57-61, 109-111, 291-297` (and every other query in the file) | SQL built by string concatenation, including the login query. | `' OR '1'='1` logs in without a password; search and CRUD routes allow reading or destroying any table. |
| 3 | CRITICAL | `app.py:47-78` | `/admin/reset-db` and `/admin/query` have no authentication; the second executes SQL sent by the client. | Any anonymous caller can dump or wipe the database. |
| 4 | CRITICAL | `database.py:75-79`, `models.py:83, 99, 110`, `controllers.py:130-132` | Passwords stored and compared in plaintext, and returned by `GET /usuarios`. | One request leaks every credential. |
| 5 | CRITICAL | `models.py:1-314`, `app.py:47-78`, `controllers.py:264-292` | God module: `models.py` mixes queries, business rules and serialization for four domains; the entry file and a controller also run SQL. | Nothing can be tested in isolation; every change touches everything. |
| 6 | HIGH | `models.py:256-262, 133-169`, `controllers.py:208-210, 247-250` | Business rules (volume discount, order flow, notifications) sit in the data layer and in controllers. | Rules cannot be reused or unit-tested without HTTP or a database. |
| 7 | HIGH | `models.py:133-169` | Order creation is not atomic: stock is checked, then decremented in other statements, with no rollback. | On the shared connection a failure leaves pending writes that the next request commits; concurrent orders can oversell. |
| 8 | HIGH | `database.py:4-10` | Global mutable connection shared across threads (`check_same_thread=False`) with a hardcoded path. | Hidden coupling and race conditions between requests. |
| 9 | HIGH | `app.py:8, 9, 88` | `debug=True`, bound to `0.0.0.0`, CORS open to all. | The Werkzeug debugger is reachable from the network (remote code execution). |
| 10 | MEDIUM | `models.py:171-233` | N+1: one query for items per order and one for the product name per item. | Latency grows linearly with orders and items. |
| 11 | MEDIUM | `models.py:12-21, 31-40, 304-313, 178-199, 211-231`, `controllers.py:24-62` vs `64-96` | Row-to-dict mapping and the validation chain are copy-pasted. | Fixes must be applied several times and copies drift apart. |
| 12 | MEDIUM | `controllers.py:43-46, 118-121, 169-171, 239-243` | Weak validation: `preco < 0` on a string raises, `float()` errors surface as 500, `login` crashes on a non-JSON body, unknown order ids are "updated". | Bad input produces 500s or silent no-ops. |
| 13 | MEDIUM | `controllers.py:10-12` (repeated in every handler) | Per-handler `try/except Exception` returning `str(e)`; no central error handler. | Leaks internals and gives inconsistent failure handling. |
| 14 | LOW | `models.py:257-262`, `controllers.py:47-52, 242` | Magic numbers and strings (thresholds 10000/5000/1000, rates 0.1/0.05/0.02, category and status lists). | The meaning is invisible and changes touch several places. |
| 15 | LOW | `controllers.py:8, 57, 106, 208-210, 248`, `app.py:56, 83-86` | `print()` used as logging, including simulated e-mail/SMS/push. | No levels, noisy output, no real notification boundary. |
| 16 | LOW | `controllers.py:14, 56, 64`, `models.py:187-191`, `models.py:2`, `database.py:2` | `id` shadows a built-in, `cursor2/cursor3`, unused imports (`sqlite3`, `os`). | Readability and dead code. |

### Project 2 — `ecommerce-api-legacy` (Node.js/Express)

| # | Severity | Location | Problem | Why it matters |
|---|---|---|---|---|
| 1 | CRITICAL | `utils.js:2-5` | DB user and password, a live payment-gateway key (`pk_live_...`) and SMTP user are hardcoded in a utils file. | Production credentials in version control. |
| 2 | CRITICAL | `AppManager.js:45` | Every checkout logs the full card number and the gateway key. | Card data in logs is a PCI violation and a leak by design. |
| 3 | CRITICAL | `utils.js:17-23`, `AppManager.js:18, 68` | `badCrypto` is not a hash (base64 repeated and cut to 10 characters); default password `"123456"`; seed password in plaintext. | Passwords are trivially recoverable or guessable. |
| 4 | CRITICAL | `AppManager.js:4-139` | God class: schema, seed, routing, checkout, payment, reporting and deletion in one class. | Untestable, no separation of responsibilities. |
| 5 | CRITICAL | `AppManager.js:80-137` | `/api/admin/financial-report` and `DELETE /api/users/:id` are open to anyone. | Financial data disclosure and unauthenticated deletion. |
| 6 | HIGH | `AppManager.js:28-78` | Checkout business logic (payment decision `cc.startsWith("4")`, user creation, enrollment) inside the route handler. | Cannot be reused or tested without HTTP. |
| 7 | HIGH | `AppManager.js:37-77, 83-128` | Callback hell, up to six levels, with manual completion counters. | Easy to answer twice or never; hard to extend. |
| 8 | HIGH | `AppManager.js:50-63, 131-137` | Checkout is not transactional; deleting a user leaves orphan enrollments and payments (the response text admits it). | Inconsistent data after any failure. |
| 9 | HIGH | `utils.js:9-15, 25`, `AppManager.js:7, 59` | Global mutable cache and counter; the database is created inside the constructor. | Hidden state, no dependency injection. |
| 10 | MEDIUM | `AppManager.js:83-128` | N+1 in the financial report (per course, per enrollment: user and payment queries); `err` ignored at 92/104/106. | Slow report that crashes on a database error. |
| 11 | MEDIUM | `AppManager.js:35` (plain-text errors at 38, 41, 48, 51, 55, 70, 84, 135 vs JSON at 60) | Presence-only validation and mixed plain-text/JSON responses. | Clients need per-route parsing; bad data gets in. |
| 12 | MEDIUM | `AppManager.js:57-60, 133-136` | Callback errors ignored (audit log insert, delete). | Failures are silent. |
| 13 | LOW | `AppManager.js:29-33`, `utils.js:12-23` | Cryptic names (`u, e, p, cid, cc`, `badCrypto`). | Slows every reader. |
| 14 | LOW | `utils.js:19, 22`, `AppManager.js:46, 108` | Magic numbers and strings (`10000`, `substring(0, 10)`, `"4"`, `"PAID"`). | Meaning hidden in literals. |
| 15 | LOW | `utils.js:10`, `AppManager.js:2`, `utils.js:3-5` | Dead code: `totalRevenue`, unused imports and config fields. | Noise and false reuse. |

No deprecated APIs were found in this project (it already uses `express.json()` and `Buffer.from`).

### Project 3 — `task-manager-api` (Python/Flask + SQLAlchemy, partially layered)

| # | Severity | Location | Problem | Why it matters |
|---|---|---|---|---|
| 1 | CRITICAL | `app.py:13`, `services/notification_service.py:9-10` | Hardcoded secret key and SMTP credentials. | Secrets in version control. |
| 2 | CRITICAL | `models/user.py:29, 32, 21` | Passwords hashed with unsalted MD5, and the hash is returned in every user response. | Hashes are cracked in seconds and leak through the API. |
| 3 | CRITICAL | `routes/user_routes.py:119-122, 134-151, 210` | No authentication or authorization anywhere: anyone can set `role` to `admin` or delete users; `/login` returns the forgeable token `fake-jwt-token-<id>`. | Complete privilege escalation. |
| 4 | HIGH | `routes/task_routes.py:11-63`, `routes/report_routes.py:12-101`, `routes/user_routes.py:134-151` | Fat routes: serialization, overdue rules, report math and cascade deletes live in the route layer; there is no controller layer and `NotificationService` is never used. | Layers exist as folders but not as responsibilities. |
| 5 | HIGH | `app.py:15, 34` | `debug=True`, bound to `0.0.0.0`, CORS open to all. | Debugger reachable from the network. |
| 6 | MEDIUM | `routes/task_routes.py:41-57`, `routes/user_routes.py:22`, `routes/report_routes.py:55-68, 163` | N+1: user and category fetched per task, `len(u.tasks)` per user, per-user and per-category queries. | Query count grows with data. |
| 7 | MEDIUM | `routes/task_routes.py:30-39, 71-80, 283-287`, `routes/user_routes.py:171-180`, `routes/report_routes.py:34-43, 132-135` | The overdue rule is copied six times although `Task.is_overdue` exists (`models/task.py:50-60`); task serialization and the e-mail regex are duplicated too. | Rules drift apart; helpers exist but are ignored. |
| 8 | MEDIUM | `Query.get` at `task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227` (and in the other routes); `datetime.utcnow()` at `models/task.py:15-16, 52`, `task_routes.py:31`, `notification_service.py:35` | Deprecated APIs: legacy `Query.get` (SQLAlchemy 2.x) and `datetime.utcnow()` (deprecated since Python 3.12). | Warnings today, breakage on upgrade. |
| 9 | MEDIUM | `task_routes.py:62, 137, 204, 236`, `user_routes.py:130, 149`, `report_routes.py:186, 207, 221`; validation at `task_routes.py:113, 182, 261, 264`, `report_routes.py:196-197` | Bare `except:` clauses and unchecked types (`priority < 1` on a string, `int()` on query params, `data` possibly `None`). | Errors are swallowed and bad input becomes a 500. |
| 10 | LOW | `app.py:7`, `task_routes.py:7`, `user_routes.py:6`, `report_routes.py:7-8`, `utils/helpers.py:2-7, 19-116` | Unused imports and dead helpers (`process_task_data`, `generate_id`, constants that nothing imports). | Noise and a false sense of reuse. |
| 11 | LOW | `task_routes.py:149, 153, 219, 234`, `user_routes.py:83, 89, 147` | `print()` as logging. | No levels or structure. |
| 12 | LOW | `task_routes.py:110, 177`, `user_routes.py:64, 71, 115, 120` | Magic numbers and strings (status and role lists, minimum password length 4, priority range 1-5). | Same literal in several places. |

---

## Construção da Skill

### Structure

```
.claude/skills/refactor-arch/
├── SKILL.md                      # the 3 phases, ground rules, the confirmation gate
└── references/
    ├── project-analysis.md       # language / framework / database / architecture heuristics
    ├── anti-patterns-catalog.md  # 22 anti-patterns, signals, severities, deprecated-API table
    ├── report-template.md        # exact output of phases 1, 2 and 3
    ├── mvc-guidelines.md         # target layers, dependency rule, behavior-preservation contract
    └── refactoring-playbook.md   # 14 transformations with before/after code
```

### Design decisions

- **`SKILL.md` is the procedure, `references/` is the knowledge.** `SKILL.md` says what to do and in
  which order; each reference is read in full at the start of the phase that needs it. Phase 1 reads
  the analysis heuristics, Phase 2 the catalog and the template, Phase 3 the guidelines and the
  playbook. The context stays small and each phase can be audited on its own.
- **Evidence rule.** A finding needs a file and line numbers verified by reading those lines.
  Repeated occurrences of one root cause are merged into one finding that lists every location.
- **Phases 1 and 2 are read-only, and the gate is enforced twice.** `SKILL.md` forbids edits before
  the answer, and in my runs the headless session only had read tools. The Phase 2 output ends with
  `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]` and the turn stops there.
- **Phase 3 has a safety net.** Before touching code the skill records a baseline of the original
  app (status code and top-level JSON keys per route), then refactors, boots the result, replays the
  same requests and diffs. Every difference is either fixed or listed under "Behavior changes". Check
  marks are printed only for checks that really ran, and "zero anti-patterns" only if a re-scan finds
  none.
- **Behavior-preservation contract** (`mvc-guidelines.md`, section 5). Routes, methods, status codes,
  success payloads and the run command stay identical. A short allow-list covers the changes that fix
  an audited defect (secrets out of responses, admin guard, hashed passwords, signed tokens, one JSON
  error envelope, safer defaults, rejecting input that crashed or corrupted data). Anything else that
  differs is a regression to fix.
- **Execution order** (`refactoring-playbook.md`): config, mechanical modernization, data layer
  (queries, credentials, transactions, N+1), layer split and injection, logic out of controllers,
  validation and error handling, admin guard, entry-point wiring, cleanup. Each step leaves the app
  runnable.

### Anti-patterns in the catalog and why

22 entries, each with detection signals, why it matters and the playbook transformation that fixes it.
I started from the manual analysis (the patterns that recurred in the three projects) and completed
the list with the usual suspects of each severity.

| Severity | Entries | Why they sit there |
|---|---|---|
| CRITICAL (5) | AP-01 hardcoded secrets, AP-02 SQL injection, AP-03 insecure credential storage/exposure, AP-04 unprotected privileged endpoints, AP-05 God class/module | The scale's definition: exposed data, injection, and total collapse of separation of responsibilities. |
| HIGH (7) | AP-06 logic in controllers, AP-07 data access outside models, AP-08 global mutable state, AP-09 tight coupling/no DI, AP-10 non-atomic writes and missing integrity, AP-11 callback hell, AP-12 insecure runtime config | Strong MVC/SOLID violations and data-integrity risks that make maintenance and tests very hard. |
| MEDIUM (6) | AP-13 N+1, AP-14 duplication, AP-15 weak validation, AP-16 fragmented error handling, AP-17 deprecated APIs, AP-18 inconsistent response contract | Standardization, duplication, moderate performance and upgrade risk. |
| LOW (4) | AP-19 magic numbers/strings, AP-20 poor naming, AP-21 print-style logging, AP-22 dead code and unused imports | Readability. |

**Deprecated APIs (AP-17)** has its own table: obsolete usage and modern equivalent for Python 3.12+,
SQLAlchemy 2.x / Flask-SQLAlchemy 3.x, Flask >= 2.3, Pydantic v2, Python stdlib, Node.js, Express,
JavaScript, Java and PHP. The skill reads the dependency manifest first, so it only reports what
applies to the detected versions. Result: none in projects 1 and 2, two findings in project 3
(`datetime.utcnow()` and `Model.query.get()`).

### How the skill stays technology-agnostic

- The catalog and the guidelines speak in **roles** (config, models, views/routes, controllers,
  services, middleware, entry point), never in file names. Section 3 of `mvc-guidelines.md` maps the
  roles to Flask, Express, Spring Boot, Django, Laravel, Rails and ASP.NET idioms.
- Detection uses **signals** written for several stacks (for example `execute("..." + x)`,
  `` `...${x}` ``, `.run("..." + x)` for SQL injection), always confirmed by reading the code.
- Phase 1 derives the stack, the route inventory, the entry point and the run command from the code,
  and Phase 3 builds its baseline from that inventory. No route, table or domain is hardcoded.
- The target layout adapts to what exists: a monolith gets all layers, a God class is split by
  responsibility, and a partially layered project keeps its correct folders and only gets what is
  missing.
- The playbook shows every transformation in Python and in JavaScript and tells the agent to apply
  the same idea idiomatically in other stacks.

**Limits of this claim.** The skill was exercised on Flask and Express only. The examples in the
catalog and the playbook were first modeled on patterns seen in the three projects (class names,
domain words, Portuguese messages). Before the final runs I rewrote them in a neutral domain
(`tmp/neutralize-examples.py`), so the final results do not come from examples that mirror the
targets.

### Challenges and how they were solved

- **The model over-reached in Phase 3, twice, and the skill was tightened each time.** In the first
  run of project 1 it also rejected input that silently corrupted data (negative quantities, orders
  for missing users); the contract did not name that class of change, so I clarified items 6 and 7
  of the allow-list. In a later run of project 3 it built a Bearer-token authentication system and
  required login on `GET /reports/summary` and `PUT /users/<id>`, which were open routes. The
  playbook already said not to invent an auth system, so I made the rule explicit in
  `mvc-guidelines.md` (section 5, item 2) and `T-04`: guard only the routes the audit lists under
  AP-04, with the admin-token header, and report the rest as residual risk. After each change I
  re-ran from the original code. Earlier attempts are kept: `tmp/p1-run1/` and `tmp/p1-phase*.jsonl`
  (first), `tmp/p1b-*`, `tmp/p2-*`, `tmp/p3-*` (second generation) and `tmp/attempt-2/` with
  `tmp/p?f-*` (the run with the Bearer authentication).
- **Examples that mirrored the targets.** The playbook examples reused names and domains of the
  three projects. I neutralized them and re-ran all three projects so that one frozen skill produced
  every final result.
- **Validation could have been a false positive.** Port 3000 (project 2's port) was held by an
  unrelated container, which would have answered the readiness check and the baseline requests.
  `SKILL.md` now says: check the port first, never send requests to a port you did not start a
  process on, and confirm the responder is your own process.
- **Security fixes versus "endpoints keep responding".** Privileged endpoints are guarded instead of
  deleted: with no token configured they answer 403, with a wrong one 401. The raw-SQL endpoint also
  needs an explicit opt-in flag and accepts a single read-only `SELECT`. Seed users keep working
  because seed passwords are hashed on insert, and old plaintext or MD5 rows are verified once and
  re-hashed on login.
- **The Phase 2 gate in a non-interactive run.** `claude -p` ends the turn at the `[y/n]` question;
  I resumed the session with `--continue` and the answer `y`. This is exactly how the gate works
  interactively.
- **Keeping my own instructions out of the skill runs.** The runs set
  `CLAUDE_CODE_DISABLE_CLAUDE_MDS=1` and `--setting-sources project,local`, so only the skill
  governed the behavior (`tmp/run-skill.sh`).
- **Agent sandbox.** The sessions could write only inside the project directory plus their own
  scratch space, so the baseline copy ended up in different places (see the observations below).

---

## Resultados

All three projects were run through the real CLI (`claude -p "/refactor-arch"`, then
`claude -p --continue "y"`) with Claude Code 2.1.319 and model `claude-opus-5-5`. Transcripts are in
`tmp/*.jsonl`; the files named `p1g-*`, `p2g-*` and `p3g-*` are the final runs, the ones whose
results are reported here.

### Audit summary

| Project | CRITICAL | HIGH | MEDIUM | LOW | Total | Resolved by Phase 3 |
|---|---|---|---|---|---|---|
| 1 — code-smells-project | 5 | 6 | 5 | 4 | 20 | 19 of 20 (AP-04 partial) |
| 2 — ecommerce-api-legacy | 4 | 6 | 4 | 4 | 18 | 18 of 18 (residual: no auth system, simulated gateway) |
| 3 — task-manager-api | 3 | 5 | 6 | 4 | 18 | 16 of 18 (AP-03, AP-04 partial) |

Full reports: [`reports/audit-project-1.md`](reports/audit-project-1.md),
[`reports/audit-project-2.md`](reports/audit-project-2.md),
[`reports/audit-project-3.md`](reports/audit-project-3.md). Every finding of the manual analysis has
a counterpart in the skill's report, and the skill found more. Examples: the numeric `card` that
crashes the whole Node process (project 2), a negative `quantidade` that increases stock (project 1),
the unused `marshmallow` and `requests` dependencies (project 3).

### Before and after

**Project 1 — code-smells-project** (~780 lines in 4 files)

```
before                         after
├── app.py (config+routes+SQL) ├── app.py                  # create_app() composition root
├── controllers.py             ├── config/ {settings,constants}.py
├── models.py                  ├── database/connection.py
├── database.py                ├── models/ {produto,usuario,pedido,sistema}.py
└── requirements.txt           ├── services/ {pedido,relatorio,notification}_service.py
                               ├── controllers/ {produto,usuario,pedido,relatorio,sistema}_controller.py + validators.py
                               ├── views/routes.py         # Blueprint, same 19 routes
                               ├── middlewares/ {error_handler,auth}.py
                               ├── utils/errors.py
                               └── .env.example, README.md, requirements.txt
```

**Project 2 — ecommerce-api-legacy** (~180 lines in 3 files)

```
before                         after
src/                           src/
├── app.js                     ├── app.js                  # composition root
├── AppManager.js (God class)  ├── config/ {index,constants}.js
└── utils.js (config+cache)    ├── database/connection.js  # schema, seed, promise helpers, transactions
                               ├── models/ {user,course,enrollment,payment,auditLog}Model.js
                               ├── services/ {checkout,financialReport,user}Service.js, paymentGateway.js
                               ├── controllers/ {checkout,admin,user}Controller.js
                               ├── routes/ {checkout,admin,user}Routes.js
                               ├── middlewares/ {asyncHandler,requireAdmin,errorHandler}.js
                               └── utils/ {logger,password,httpError}.js
                               + .env.example, api.http (sends X-Admin-Token)
```

**Project 3 — task-manager-api** (~1160 lines in 15 files, already partially layered)

```
before                          after
├── app.py                      ├── app.py                   # create_app()
├── database.py                 ├── database.py              # kept: db instance, FK enforcement
├── seed.py                     ├── seed.py                  # kept, hashed passwords
├── models/ {task,user,category}├── models/                  # kept, now own queries and rules
├── routes/ (fat routes)        ├── routes/ {task,user,category,report}_routes.py + serializers.py  # thin: URL -> controller
├── services/notification (dead)├── services/report_service.py
├── utils/helpers.py (dead)     ├── config/ {settings,constants}.py   # new
                                ├── controllers/ {task,user,category,report}_controller.py + validators.py  # new
                                ├── middlewares/ {error_handler,auth}.py   # new
                                ├── utils/ {errors,time}.py
                                └── .env.example, requirements.txt (2 unused deps dropped)
```

### Validation checklist

Marks are mine, after checking the evidence below each table. "Replay" means the independent
before/after smoke test described in the next subsection.

| Check | Project 1 | Project 2 | Project 3 |
|---|---|---|---|
| **Phase 1** language detected | [x] Python 3.14 | [x] JavaScript (Node 24) | [x] Python 3.14 |
| framework detected | [x] Flask 3.1.1 | [x] Express ^4.18.2 | [x] Flask 3.0.0 |
| domain described | [x] E-commerce API | [x] LMS with checkout | [x] Task Manager API |
| files analyzed match reality | [x] 4 | [x] 3 | [x] 12 (3 one-line `__init__.py` not counted, 15 files in total) |
| **Phase 2** follows the template | [x] | [x] | [x] |
| findings have file and exact lines | [x] spot-checked against the code | [x] spot-checked | [x] spot-checked |
| ordered CRITICAL to LOW | [x] | [x] | [x] |
| at least 5 findings | [x] 20 | [x] 18 | [x] 18 |
| at least 1 CRITICAL or HIGH | [x] 11 | [x] 10 | [x] 8 |
| deprecated-API detection included | [x] none applicable | [x] none applicable | [x] 2 findings |
| pauses and asks before Phase 3 | [x] | [x] | [x] |
| **Phase 3** MVC directory structure | [x] | [x] | [x] |
| configuration in a config module | [x] | [x] | [x] |
| models abstract the data | [x] | [x] | [x] |
| views/routes separated | [x] | [x] | [x] |
| controllers hold the flow | [x] | [x] | [x] |
| centralized error handling | [x] | [x] | [x] |
| clear entry point | [x] `app.py` | [x] `src/app.js` | [x] `app.py` |
| application boots without errors | [x] | [x] | [x] |
| original endpoints respond | [x] 19/19 | [x] 3/3 | [x] 22/22 |

Evidence for the Phase 2 gate: the Phase 1-2 runs used read-only tools, ended on the `[y/n]` line,
and `git status` showed no change in the project afterwards. Remaining literals after Phase 3: the
sample seed credentials of project 1, which are hashed on insert and needed to try the app, and one
`DELETE FROM` built from a fixed table whitelist (`models/sistema.py`).

Evidence for "boots without errors": the skill's own runs booted the apps with `python app.py` and
`node src/app.js`. The project 2 agent could not run `npm start` itself (port 3000 belongs to an
unrelated container) and said so in its summary; I ran `PORT=3100 npm start` myself in the replay
below, and `package.json` was not changed.

### Replay: original code versus refactored code

I replayed the same request list against the original code (extracted from git into `tmp/baseline/`,
only the port changed in the scratch copy) and against the refactored project, and compared status
code and top-level JSON keys. The skill did the same on its own; these are my independent runs.

| Project | Requests | Identical | Differences | Unexplained |
|---|---|---|---|---|
| 1 | 28 | 21 | 7 | 0 |
| 2 | 10 | 5 | 5 | 0 |
| 3 | 30 | 24 | 6 | 0 |

Every difference is an intended change from the allow-list:

- project 1: `/health` no longer returns `secret_key`, `debug`, `db_path`; five error bodies gain
  `"sucesso": false`; the anonymous `/admin/query` and `/admin/reset-db` now answer 403.
- project 2: error bodies are JSON `{"error": ...}` instead of plain text; the anonymous admin report
  and user delete answer 401 (403 if no token is configured).
- project 3: `password` is gone from user payloads; a non-numeric `priority` answers 400 instead of
  500; creating an `admin` user anonymously answers 401.

Success payloads are identical everywhere. Files: `tmp/spec-p*.json` (requests),
`tmp/p1-before.json`, `tmp/p2-before.json`, `tmp/p3-before.json` (original code) and
`tmp/p1g-after.json`, `tmp/p2g-after.json`, `tmp/p3g-after.json` (final refactors), plus the matching
`*.json.log` server logs.

### Applications running after the refactoring

Server logs of the replay (trimmed):

```
# project 1 (tmp/p1g-after.json.log)
INFO database.connection: Banco de dados inicializado com dados de exemplo
INFO __main__: Servidor iniciado em http://127.0.0.1:5000
 * Debug mode: off  * Running on http://127.0.0.1:5000

# project 2, started with npm start (tmp/p2g-after.json.log)
[INFO] Frankenstein LMS rodando na porta 3100...
[INFO] Processando pagamento { cardLast4: '4444', amount: 497, gatewayConfigured: false }
[INFO] Checkout concluído { courseId: 2, enrollmentId: 2 }

# project 3 (tmp/p3g-after.json.log)
 * Debug mode: off  * Running on http://127.0.0.1:5100
INFO controllers.task_controller: Task criada: 11
```

`GET /health` of project 1 after the refactoring:
`{"ambiente":"producao","counts":{"pedidos":0,"produtos":10,"usuarios":3},"database":"connected","status":"ok","versao":"1.0.0"}`.
The `senha` field no longer appears in `GET /usuarios`, and the full card number no longer appears in
the project 2 log (only the last four digits).

### Run statistics

Reported by the CLI for the final runs (`tmp/*.jsonl`).

| Project | Phases 1-2 | Phase 3 |
|---|---|---|
| 1 | 15 turns, 95 s, USD 0.59 | 85 turns, 503 s, USD 3.62 |
| 2 | 16 turns, 78 s, USD 0.50 | 78 turns, 292 s, USD 2.33 |
| 3 | 27 turns, 150 s, USD 0.88 | 93 turns, 500 s, USD 4.22 |

### Observations by stack

- **Python/Flask monolith (project 1).** The skill introduced an application factory, a per-request
  connection in `flask.g`, one Blueprint, domain exceptions with a single error handler, and a
  transaction with a conditional stock update. The request/response contract stayed the same.
- **Node.js/Express God class (project 2).** The class disappeared. The result is a composition
  root, promisified DB helpers with a serialized transaction helper, `async/await` services, an async
  handler wrapper feeding one error middleware, scrypt hashing and a timing-safe admin guard.
- **Partially layered Flask project (project 3).** The skill did not rename what was fine: `models/`,
  `routes/`, `database.py` and `seed.py` stayed. It added the missing layers (`controllers/`,
  `config/`, `middlewares/`), slimmed the routes to routing only, and removed the dead helpers, the
  unused `NotificationService` and two unused dependencies. It reported two findings as only
  partially resolved instead of claiming a clean result: project 3 still has no real authentication
  (only destructive routes and role changes require the admin token), and the 4-character minimum
  password and the seed passwords were kept by the behavior contract.
- **Both audits and refactors were consistent across stacks.** Same report format, same severity
  logic, same validation procedure. What changed was the detected idiom (callbacks versus ORM, plain
  SQL versus SQLAlchemy), not the procedure.

### Provenance and known limits

- **One frozen skill.** All final results (`p1g-*`, `p2g-*`, `p3g-*`) come from the skill in the first
  commit `feat: add refactor-arch skill`, run from the original code of each project. The three
  skill folders are byte-identical (`diff -r`). Earlier generations are kept as evidence in `tmp/`
  and are not used for the numbers above.
- **Baselines, taken before any edit.** The agents kept their scratch copies of the original in
  `tmp/p1-original/`, `tmp/p2-original/` and `tmp/cs-orig-p3/`. In the first generation, project 3
  removed its own scratch directories with a `cleanup.py` (visible in `tmp/p3-phase3.jsonl`). The
  original code of every project is also in the first commit of the repository, and my replays use a
  copy extracted from it (`tmp/baseline/`).
- Residual risks the skill reported and left open: none of the three projects has a real
  authentication system (only a minimal admin token was added), and the skill was not tested on
  stacks other than Flask and Express.

---

## Como Executar

### Prerequisites

- Claude Code installed and logged in (tested with 2.1.319). Gemini CLI or Codex would need the
  equivalent skill folder and invocation.
- Python 3.10+ with `venv` (tested with 3.14), Node.js 18+ with `npm` (tested with 24), `curl`.

Install the dependencies once:

```bash
cd code-smells-project && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && cd ..
cd task-manager-api && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && cd ..
cd ecommerce-api-legacy && npm install && cd ..
```

### Run the skill

The projects in this repository are already refactored. To run the skill on the original code, restore
a project from the first commit of the repository first:

```bash
git checkout "$(git rev-list --max-parents=0 HEAD)" -- code-smells-project
```

Then, for each project (the skill folder is already inside it):

```bash
cd code-smells-project      # then ecommerce-api-legacy, then task-manager-api
claude "/refactor-arch"
```

The skill prints the Phase 1 summary and the Phase 2 report, then asks
`Proceed with refactoring (Phase 3)? [y/n]`. Answer `y` to run Phase 3.

To run it headless the way I did (`tmp/run-skill.sh` holds the exact flags and permissions):

```bash
claude -p "/refactor-arch"        # phases 1-2, stops at the question
claude -p --continue "y"          # phase 3
```

### Validate that the refactoring worked

Boot each project with its original command and replay the request lists:

```bash
# project 1 (admin routes need ADMIN_TOKEN; raw query also needs ALLOW_ADMIN_QUERY=1)
cd code-smells-project && ADMIN_TOKEN=secret .venv/bin/python app.py          # http://127.0.0.1:5000

# project 2 (PORT and ADMIN_TOKEN are read from the environment)
cd ecommerce-api-legacy && ADMIN_TOKEN=secret npm start                       # http://127.0.0.1:3000

# project 3 (seed first)
cd task-manager-api && .venv/bin/python seed.py && ADMIN_TOKEN=secret .venv/bin/python app.py   # http://127.0.0.1:5000
```

Quick manual checks:

```bash
curl -s http://127.0.0.1:5000/health                                  # project 1: no secret_key in the body
curl -s -X POST http://127.0.0.1:5000/admin/reset-db                  # project 1: 403 without the token
curl -s -X POST http://127.0.0.1:3000/api/checkout -H 'Content-Type: application/json' \
  -d '{"usr":"Ana","eml":"ana@example.com","pwd":"x","c_id":2,"card":"4111222233334444"}'   # project 2
curl -s http://127.0.0.1:5000/tasks                                   # project 3
```

For the full before/after comparison, extract the original code and run the same spec on both:

```bash
mkdir -p tmp/baseline && git archive "$(git rev-list --max-parents=0 HEAD)" code-smells-project | tar -x -C tmp/baseline
python3 tmp/smoke.py run http://127.0.0.1:5000 tmp/spec-p1.json tmp/before.json   # server running the original
python3 tmp/smoke.py run http://127.0.0.1:5000 tmp/spec-p1.json tmp/after.json    # server running the refactored code
python3 tmp/smoke.py diff tmp/before.json tmp/after.json
```

`tmp/serve-and-smoke.sh` starts a server, replays a spec and stops it. Each project's own README lists
its environment variables (`.env.example`).
