# Anti-pattern catalog (Phase 2)

22 anti-patterns, grouped by severity. Each entry gives: what it is, **detection signals** (what to
search for, then confirm by reading), why it matters, and the playbook transformation that fixes it.

A signal is a lead, not a verdict: open the code and confirm before reporting. Signals are written
for several stacks; for a stack not listed, look for the equivalent construct.

## Severity scale

| Severity | Meaning |
|---|---|
| **CRITICAL** | Serious architecture or security failures: exposed secrets or data, injection, unauthenticated destructive access, or a complete collapse of separation of responsibilities (God class). |
| **HIGH** | Strong MVC / SOLID violations that make maintenance and testing very hard: business logic trapped in controllers, tight coupling without dependency injection, global mutable state, data-integrity risks. |
| **MEDIUM** | Standardization problems, duplication, moderate performance bottlenecks (N+1), missing validation, deprecated APIs. |
| **LOW** | Readability: poor names, magic numbers, print-style logging, dead code. |

When a case sits between two levels, choose the higher one if it is exploitable or can lose data,
otherwise the lower one, and say why in the finding.

---

## CRITICAL

### AP-01 Hardcoded credentials and secrets
- **What**: passwords, API keys, tokens, signing keys, SMTP/DB credentials written in source.
- **Signals**: assignments to names containing `secret`, `password`, `passwd`, `pwd`, `key`, `token`,
  `api_key`, `smtp`, `dbUser`, `dbPass` with a string literal; prefixes such as `pk_live_`, `sk_`,
  `AKIA`; `app.config['SECRET_KEY'] = '...'`; connection strings with embedded credentials; config
  objects exported from a utils file.
- **Why**: anyone with repo access gets production access; rotation requires a code change.
- **Fix**: T-01.

### AP-02 SQL injection through dynamic query construction
- **What**: SQL assembled from request or variable data by concatenation or interpolation.
- **Signals**: `execute("..." + x)`, `execute(f"... {x}")`, `"%s" % x` inside SQL, template literals
  `` `SELECT ... ${x}` ``, `.run("..." + x)`, `LIKE '%" + term + "%'`, `str(id)` glued into SQL,
  `.format(` on SQL strings, ORM `text(f"...")`/`raw()` with interpolation.
- **Why**: data theft, authentication bypass (`' OR '1'='1`), destructive statements.
- **Fix**: T-02.

### AP-03 Insecure credential storage and exposure
- **What**: passwords stored or compared in plaintext, hashed with a broken or home-made scheme, or
  secrets and personal data returned by the API or written to logs.
- **Signals**: `password == body.password`; `hashlib.md5/sha1(...)` on passwords; custom hash loops
  (`base64`, truncation, fixed salt); a password/hash field inside a serializer (`to_dict`, response
  dict); seed data with plaintext passwords; secrets echoed by a health/debug endpoint; card numbers,
  tokens or passwords in `print`/`console.log`; "tokens" built by concatenation
  (`'fake-jwt-token-' + id`); default password fallbacks (`pwd || "123456"`).
- **Why**: one leak exposes every account; PCI/LGPD/GDPR violations; forgeable sessions.
- **Fix**: T-03.

### AP-04 Unprotected privileged or destructive endpoints
- **What**: routes that execute raw SQL, reset or delete data, change roles, or expose reports with
  no authentication or authorization check.
- **Signals**: paths containing `admin`, `reset`, `query`, `debug`, `drop`; handlers that call
  `execute(request...)` with client-supplied SQL; `DELETE`/`PUT` handlers with no guard decorator or
  middleware; a client-controlled `role` field accepted on update; no auth middleware anywhere in the
  project; a login endpoint that issues a token or a `role` column that no route ever verifies.
- **Why**: any anonymous caller can wipe or read the whole database or escalate privileges.
- **Fix**: T-04. In the recommendation, name the guard that fits: validate the login token and the
  user's role when the project already has a login, the admin-token header when it has none.

### AP-05 God class / God module
- **What**: one class or file that owns several unrelated responsibilities (routing, validation,
  business rules, data access, schema creation, formatting, side effects).
- **Signals**: a file or class above ~200 lines that contains both route registration and SQL; a
  class whose methods span schema init, seeding, route handlers and reporting; a `models` file that
  also computes business rules and builds HTTP-shaped dicts; entry file containing handlers and DB
  calls; names such as `Manager`, `Handler`, `Utils`, `Helper` holding everything.
- **Why**: untestable in isolation; every change touches everything; merge conflicts.
- **Fix**: T-05 (plus T-06, T-07).

---

## HIGH

### AP-06 Business logic in the controller / route layer
- **What**: pricing, discounts, workflows, state transitions, aggregations or side effects
  implemented inside request handlers.
- **Signals**: handlers longer than ~30 lines; arithmetic on domain values; loops over domain
  collections; payment/notification/email calls inside a handler; status transitions decided in the
  handler; overdue/discount/total calculations in routes.
- **Why**: logic cannot be reused or unit-tested without an HTTP request.
- **Fix**: T-06.

### AP-07 Data access outside the model layer
- **What**: SQL or ORM queries in routes, controllers, the entry file or helpers.
- **Signals**: `cursor.execute`, `db.run/get/all`, `Model.query`, `session.query`, `db.session.add`
  in a file that also defines routes or handlers; `get_db()` called from a controller; queries in
  `app.py`/`app.js`.
- **Why**: persistence concerns leak everywhere; schema changes ripple through the whole code base.
- **Fix**: T-05, T-06.

### AP-08 Global mutable state
- **What**: module-level variables mutated at runtime and shared by all requests.
- **Signals**: `global x` statements; module-level `connection = None` lazily set; module-level
  dict/list used as cache or counter (`sharedCache = {}`, `counter = 0`); exported mutable
  singletons; counters incremented in handlers.
- **Why**: hidden coupling, race conditions between requests/threads, order-dependent tests.
- **Fix**: T-07.

### AP-09 Tight coupling and no dependency injection
- **What**: components create or import their concrete collaborators directly.
- **Signals**: `new Database(...)` or `sqlite3.connect(...)` inside constructors/handlers; classes
  that import configuration and clients directly instead of receiving them; handlers that `require`
  a concrete module and call it statically; impossible to swap the database or gateway in a test.
- **Why**: cannot test with fakes; changing a dependency means editing business code.
- **Fix**: T-07.

### AP-10 Non-atomic multi-step writes and missing referential integrity
- **What**: several dependent writes without a transaction, check-then-act races, deletes that leave
  orphans.
- **Signals**: sequence of `INSERT`/`UPDATE` across tables with a single (or no) commit and no
  rollback path; stock read then decremented in separate statements; success/error responses sent
  from inside nested write callbacks; `DELETE` of a parent row with no cascade or child cleanup;
  foreign keys declared but not enforced (`PRAGMA foreign_keys` off); error branches that return
  after partial writes; shared connection with pending uncommitted work.
- **Why**: partial data after failures, oversold stock, orphan records, silent corruption.
- **Fix**: T-08.

### AP-11 Callback hell / deeply nested asynchronous flow
- **What**: nested callbacks (4+ levels) driving a flow, manual counters to detect completion.
- **Signals**: callbacks inside callbacks of `db.get/run/all`; variables such as `pending--` /
  `if (pending === 0)`; error handling repeated at each level; ignored `err` arguments.
- **Why**: unreadable, error-prone, impossible to extend; easy to send two responses or none.
- **Fix**: T-09.

### AP-12 Insecure runtime configuration
- **What**: development settings enabled for a deployable app.
- **Signals**: `debug=True` / `app.config['DEBUG'] = True` / `NODE_ENV` ignored; `host='0.0.0.0'`
  by default; `CORS(app)` or `cors()` with no origin restriction; stack traces or `str(e)` returned
  to clients; secrets or `debug: true` echoed in responses; interactive debugger reachable.
- **Why**: Werkzeug debugger allows remote code execution; information disclosure; unwanted exposure.
- **Fix**: T-01, T-12.

---

## MEDIUM

### AP-13 N+1 queries
- **What**: one query for a list plus one or more extra queries for each element.
- **Signals**: query execution inside a `for` / `forEach` / comprehension; lazy relationship access in
  a loop (`len(user.orders)`, `order.user.name`); `Model.query.get(x.fk_id)` per row; several
  `COUNT(*)` statements that could be one aggregate; nested loops each running a lookup.
- **Why**: latency grows with data size; database load multiplies.
- **Fix**: T-10.

### AP-14 Duplicated code
- **What**: the same logic copied in several places.
- **Signals**: identical blocks of 5+ lines; row-to-dict mapping repeated per query; the same
  validation chain in create and update; the same calculation (for example overdue) in many
  handlers; helper or model method exists but handlers reimplement it; same regex/list/constant in
  multiple files.
- **Why**: fixes must be applied N times; copies drift apart and diverge in behavior.
- **Fix**: T-11.

### AP-15 Missing or weak input validation
- **What**: external input used without checking type, range, format or existence.
- **Signals**: `request.get_json()` result used without a `None` check; comparison of unvalidated
  values (`price < 0` on a string); `int(x)`/`float(x)` on query params without handling errors; no
  email/format check; no length limits; ids not checked for existence before update; required body
  fields only checked for presence; client-controlled fields persisted as is.
- **Why**: 500 errors on bad input, corrupted data, injection surface.
- **Fix**: T-12.

### AP-16 Fragmented or unsafe error handling
- **What**: error handling repeated per handler, too broad, or swallowing errors.
- **Signals**: `try/except Exception` or `except:` in every handler; `catch (e) {}` empty; returning
  `str(e)` / `err.message` to clients; callback `err` argument ignored; no global error handler
  (`errorhandler`, error middleware); inconsistent status codes for the same failure.
- **Why**: leaks internals, hides bugs, inconsistent API behavior.
- **Fix**: T-12.

### AP-17 Deprecated or obsolete API usage
- **What**: calls the framework/runtime has deprecated or removed.
- **Signals / equivalents**: compare the versions from Phase 1 with this table; report every use.

| Stack | Obsolete usage | Modern equivalent |
|---|---|---|
| Python 3.12+ | `datetime.utcnow()`, `datetime.utcfromtimestamp()`, `default=datetime.utcnow` | `datetime.now(timezone.utc)` (keep naive-UTC storage with a helper, see T-13) |
| SQLAlchemy 2.x / Flask-SQLAlchemy 3.x | `Model.query.get(id)`, `session.query(M).get(id)` | `db.session.get(Model, id)` |
| SQLAlchemy 2.x | `db.engine.execute(...)`, `ext.declarative.declarative_base` | `with engine.connect()` + `text()`, `orm.declarative_base` |
| Flask >= 2.3 | `@app.before_first_request`, `app.json_encoder`, `flask.escape`, `flask.Markup` | initialize in the app factory, `app.json` provider, `markupsafe` |
| Pydantic v2 | `.dict()`, `.parse_obj()`, `@validator` | `.model_dump()`, `.model_validate()`, `@field_validator` |
| Python stdlib | `distutils`, `imp`, `pkg_resources`, `asyncio.get_event_loop()` outside a loop | `setuptools`/`importlib`, `asyncio.run` / `get_running_loop` |
| Node.js | `new Buffer(x)` | `Buffer.from(x)` / `Buffer.alloc(n)` |
| Node.js | `fs.exists`, `url.parse`, `crypto.createCipher`, `querystring` | `fs.existsSync`/`access`, `new URL()`, `createCipheriv`, `URLSearchParams` |
| Node.js | npm `request`, standalone `body-parser` (Express >= 4.16) | built-in `fetch`/`undici`/`axios`, `express.json()` / `express.urlencoded()` |
| Express 4/5 | `app.del()`, `req.param()`, `res.send(statusNumber)`, `res.json(obj, status)` | `app.delete()`, `req.params/query/body`, `res.sendStatus()`, `res.status(n).json(obj)` |
| JavaScript | `var`, `==` | `const`/`let`, `===` |
| Java | `new Date()`/`SimpleDateFormat`, `WebSecurityConfigurerAdapter`, `finalize()` | `java.time`, `SecurityFilterChain` bean, `Cleaner`/try-with-resources |
| PHP | `mysql_*`, `each()`, `create_function` | PDO / mysqli, `foreach`, closures |

  For a stack not in the table, compare each framework call against the framework's migration or
  deprecation notes for the detected version, and report only what you can name precisely.
- **Why**: breaks on upgrade, emits warnings, may carry known flaws.
- **Fix**: T-13.

### AP-18 Inconsistent response contract
- **What**: the same API answers with different shapes or content types.
- **Signals**: `res.send("text")` next to `res.json({...})`; error bodies that are sometimes plain
  text, sometimes `{error}`, sometimes `{erro}`; success flags present in some routes only; wrong
  status codes (200 on failure).
- **Why**: clients need per-route parsing; hard to evolve or document.
- **Fix**: T-12.

---

## LOW

### AP-19 Magic numbers and magic strings
- **Signals**: numeric literals with business meaning (`> 10000`, `* 0.1`, `< 4`, `substring(0, 10)`,
  `10000` loop count); repeated string literals for statuses, roles, categories
  (`'pending'`, `'PAID'`); the same literal in several files.
- **Why**: meaning is invisible; changes must be made in many places.
- **Fix**: T-14.

### AP-20 Poor naming
- **Signals**: single-letter or cryptic variables outside tiny scopes (`u`, `e`, `p`, `cc`, `pid`,
  `p1..p5`, `cursor2`); shadowing built-ins (`id`, `type`, `list`); vague module/class names
  (`utils`, `Manager`, `helpers`); inconsistent language/convention mix (`get_all_items` vs
  `list_products`); abbreviated request field names leaked into code.
- **Why**: slows every reader; hides intent.
- **Fix**: T-14.

### AP-21 Print-style logging
- **Signals**: `print(`, `console.log(` for operational messages; no logger; log lines containing
  data that should not be logged; simulated side effects implemented as `print("SENDING EMAIL")`.
- **Why**: no levels, no structure, noise in output, risk of leaking data.
- **Fix**: T-14.

### AP-22 Dead code and unused imports
- **Signals**: imports never referenced (`os`, `sys`, `json`, `hashlib`, `time`); functions, classes
  or constants never called (search the whole project before concluding); variables assigned and
  unused; exported-but-never-imported symbols; a service class that no module imports; unused
  dependencies in the manifest.
- **Why**: noise, false sense of reuse, slower builds, larger attack surface.
- **Fix**: T-14.

---

## Detection procedure

1. For each entry, run the listed signals over the whole project (search tool, then read the lines).
2. Confirm in context; discard matches inside tests, comments or documentation strings.
3. For AP-22, prove "unused" by searching all source files for the symbol name.
4. For AP-17, read the dependency manifest first to know which versions apply.
5. Merge repeated occurrences of the same root cause into one finding.
6. A well-organized project still gets audited: partial layering does not exempt AP-06, AP-07,
   AP-13, AP-14, AP-17, AP-22, which are typical for projects that already have folders.
