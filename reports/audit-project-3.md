================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0
Files:   12 analyzed | ~1155 lines of code

## Summary
CRITICAL: 4 | HIGH: 4 | MEDIUM: 7 | LOW: 4

## Findings

### [CRITICAL] Hardcoded credentials and secrets (AP-01)
File: app.py:11-13, services/notification_service.py:7-10
Description: The Flask signing key is a literal, `app.config['SECRET_KEY'] = 'super-secret-key-123'`. The database URI is hardcoded too. The SMTP account is written in source: `email_user = 'taskmanager@gmail.com'`, `email_password = 'senha123'`.
Impact: Anyone with repo access can forge Flask-signed data and log in to the mail account. Rotating either secret means changing code.
Recommendation: Move SECRET_KEY, DATABASE_URL and SMTP settings into a config module that reads environment variables (python-dotenv is already in the manifest). Add a `.env.example` with no real values (playbook T-01).

### [CRITICAL] Insecure credential storage and exposure (AP-03)
File: models/user.py:21, 29, 32, routes/user_routes.py:33, 64, 85, 115, 129, 209-210, seed.py:19, 26, 33
Description: Passwords are hashed with unsalted `hashlib.md5`. `User.to_dict()` includes `'password': self.password`, so GET /users/<id>, POST /users, PUT /users/<id> and POST /login all return the hash. Login returns a forgeable token, `'fake-jwt-token-' + str(user.id)`. The minimum password length is 4, and the seed uses passwords like '1234'.
Impact: MD5 hashes in API responses can be cracked offline almost instantly. Anyone can impersonate any user by guessing `fake-jwt-token-<id>`.
Recommendation: Hash with `werkzeug.security.generate_password_hash`/`check_password_hash` and accept legacy MD5 hashes on login so existing users can still sign in. Remove `password` from every serializer. Issue a signed, expiring token (itsdangerous, which ships with Flask) (playbook T-03).

### [CRITICAL] Unprotected privileged or destructive endpoints (AP-04)
File: routes/user_routes.py:52, 71, 119-122, 134-151, 185-211, routes/task_routes.py:225-238, routes/report_routes.py:12-155, 211-223, models/user.py:34-38
Description: No route checks authentication or authorization. Any anonymous caller can DELETE users, tasks and categories, read reports of every user, and set `role: 'admin'` on POST /users or PUT /users/<id>. /login issues a token that no route verifies, and `User.is_admin()` is never called.
Impact: Anonymous users can wipe data, read every user's data and escalate themselves to admin.
Recommendation: The project already has a login. Add a guard that validates the signed login token and the user's active status and role. Require it on destructive routes and role changes, and require the admin role for user deletion and role assignment (playbook T-04).

### [CRITICAL] God class / God module (AP-05)
File: routes/task_routes.py:1-299, routes/report_routes.py:1-223
Description: `task_routes.py` (299 lines) registers routes and also runs ORM queries, validation, overdue rules, statistics and manual dict serialization. `report_routes.py` combines two unrelated resources: the reporting aggregations and the full CRUD of `/categories`, all with inline queries.
Impact: None of this can be tested without HTTP. Every change to a task rule, query or response shape touches the same file, and categories are hard to find under "reports".
Recommendation: Split into thin route blueprints, controllers, model/query methods and a report service. Give categories their own route and controller modules (playbook T-05, plus T-06 and T-07).

### [HIGH] Business logic in the controller / route layer (AP-06)
File: routes/task_routes.py:11-63, 85-154, 156-223, 273-299, routes/user_routes.py:42-90, 140-142, 153-183, routes/report_routes.py:12-101, 103-155
Description: Handlers are 40-90 lines long. They compute the overdue state, completion rates, per-priority and per-status counts and days overdue, decide the cascade deletion of a user's tasks, and run the full validation chains inline.
Impact: The rules can't be reused or unit-tested without a request context, and they already differ between handlers (see AP-14).
Recommendation: Move validation to controllers/validators, domain rules to model methods, and aggregations to a report service (playbook T-06).

### [HIGH] Data access outside the model layer (AP-07)
File: routes/task_routes.py:14, 42, 51, 67, 117, 122, 147-148, 158, 188, 195, 218, 227, 232-233, 247-266, 275-281, routes/user_routes.py:12, 29, 35, 67, 81-82, 94, 109, 128, 136, 140-146, 155, 159, 197, routes/report_routes.py:15-30, 46-51, 53, 56, 105, 109, 159, 163, 183-184, 192, 205, 213, 218-219
Description: Every handler calls `Model.query...` and `db.session.add/commit/delete/rollback` directly.
Impact: Persistence details leak into the HTTP layer, so a schema or query change ripples through all three route files.
Recommendation: Put queries in model class methods (e.g. `Task.search(...)`, `Task.count_by_status()`) and let controllers call them (playbook T-05, T-06).

### [HIGH] Non-atomic multi-step writes and missing referential integrity (AP-10)
File: routes/report_routes.py:217-220, models/task.py:13-14, 20-21
Description: DELETE /categories/<id> deletes the category while tasks still reference its `category_id`. The foreign keys have no `ondelete` or cascade, and SQLite does not enforce foreign keys by default (no `PRAGMA foreign_keys=ON`), so the tasks keep a dangling id.
Impact: Orphan tasks point to categories that no longer exist, so reports and `category_name` resolution silently lose data.
Recommendation: In one transaction, set `category_id = NULL` on the affected tasks before deleting the category, and keep the user-delete cleanup inside the same transaction (playbook T-08).

### [HIGH] Insecure runtime configuration (AP-12)
File: app.py:15, 34
Description: `app.run(debug=True, host='0.0.0.0', port=5000)` turns on the Werkzeug interactive debugger and listens on all interfaces. `CORS(app)` allows every origin.
Impact: A reachable debugger means remote code execution, and any website can call the API from a browser.
Recommendation: Read DEBUG, HOST, PORT and CORS_ORIGINS from the environment with safe defaults (debug off) (playbook T-01, T-12).

### [MEDIUM] N+1 queries (AP-13)
File: routes/task_routes.py:41-57, 275-281, routes/user_routes.py:22, routes/report_routes.py:15-30, 53-57, 162-163
Description: GET /tasks runs `User.query.get` and `Category.query.get` for each task. GET /users reads the lazy `len(u.tasks)` for each user. The summary report runs 12 separate `COUNT` queries plus one query per user, and GET /categories runs one count per category.
Impact: The number of queries grows linearly with data, which adds latency and database load.
Recommendation: Use eager loading (`joinedload`) and grouped aggregates (`GROUP BY status/priority/user_id/category_id`) (playbook T-10).

### [MEDIUM] Duplicated code (AP-14)
File: routes/task_routes.py:17-28, 30-39, 71-80, 92-124, 166-198, 284-287, 296, routes/user_routes.py:61, 106, 171-180, routes/report_routes.py:34-36, 67, 132-135, 151, models/task.py:39, 50-60, utils/helpers.py:21, 75, 110
Description: The overdue rule is reimplemented in 6 places even though `Task.is_overdue()` exists. Task serialization at task_routes:17-28 copies `Task.to_dict()`. The create and update validation chains are duplicated. The email regex appears 3 times, the status list 4 times, and the completion-rate formula 3 times even though `calculate_percentage` exists.
Impact: Fixes have to be applied N times, and the copies drift apart.
Recommendation: Keep one source per rule (model methods, a validators module, a constants module) and call it everywhere (playbook T-11).

### [MEDIUM] Missing or weak input validation (AP-15)
File: routes/task_routes.py:96, 113, 167, 182, 261, 264, routes/report_routes.py:196-197, 180, 202, routes/user_routes.py:102-103, 124-125
Description: Values are compared without a type check: `priority < 1` with a string priority raises TypeError, and so does `len(title)` with a non-string title. `int(priority)`/`int(user_id)` on query params raise ValueError for non-numeric input. PUT /categories/<id> never checks for a `None` body. The color is never validated (`is_valid_color` exists but is unused), and user `name`/`active` are stored without checks.
Impact: Malformed input produces HTML 500 errors and can store corrupted data.
Recommendation: Add type-aware validators in the controllers that return 400 with `{'error': ...}` (playbook T-12).

### [MEDIUM] Fragmented or unsafe error handling (AP-16)
File: routes/task_routes.py:62-63, 137, 151-154, 204, 221-223, 236, routes/user_routes.py:87-90, 130, 149, routes/report_routes.py:186, 207, 221, app.py:9-34
Description: Bare `except:` appears in 9 handlers, and GET /tasks swallows every error into a generic 500. Two handlers print `str(e)`. There is no `@app.errorhandler`, so unexpected exceptions return Flask's default HTML pages.
Impact: Real bugs stay hidden, API behavior is inconsistent, and debugging is hard.
Recommendation: Register central JSON error handlers (400/404/405/500 plus a domain error class), log exceptions, and remove the per-handler bare excepts (playbook T-12).

### [MEDIUM] Deprecated or obsolete API usage (AP-17)
File: models/category.py:11, models/task.py:15-16, 52, models/user.py:14, routes/task_routes.py:31, 72, 215, 285, routes/user_routes.py:172, routes/report_routes.py:35, 42, 45, 71, 133, services/notification_service.py:35, utils/helpers.py:38, seed.py:66-67, 69-70, 74
Description: `datetime.utcnow()` and `default=datetime.utcnow` are used, which is deprecated since Python 3.12 (runtime here is 3.14).
Impact: Emits DeprecationWarning and will break when it is removed.
Recommendation: Replace with a `utc_now()` helper that returns `datetime.now(timezone.utc).replace(tzinfo=None)`, which keeps the stored values naive UTC (playbook T-13).

### [MEDIUM] Deprecated or obsolete API usage (AP-17)
File: routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227, routes/user_routes.py:29, 94, 136, 155, routes/report_routes.py:105, 192, 213
Description: These lines use `Model.query.get(id)`, a legacy Query API under SQLAlchemy 2.x / Flask-SQLAlchemy 3.1.
Impact: It emits LegacyAPIWarning and is slated for removal.
Recommendation: Replace with `db.session.get(Model, id)` (playbook T-13).

### [MEDIUM] Inconsistent response contract (AP-18)
File: routes/task_routes.py:17-39, 268-269, routes/user_routes.py:162-180, app.py:9-34
Description: The same task resource is returned in three shapes. GET /tasks adds `overdue`, `user_name` and `category_name`. GET /tasks/search returns `to_dict()` without `overdue`. GET /users/<id>/tasks returns a reduced dict without `tags`, `user_id` or `updated_at`. Unhandled errors return HTML while handled ones return `{'error'}` JSON.
Impact: Clients need per-route parsing for the same entity.
Recommendation: Use one serializer per entity (with explicit, documented variants) and JSON-only error responses. Keep the current payloads to preserve behavior (playbook T-12).

### [LOW] Magic numbers and magic strings (AP-19)
File: routes/task_routes.py:96, 99, 110, 113, 177, 182, routes/user_routes.py:64, 71, 115, 120, routes/report_routes.py:24-28, 45, 129, utils/helpers.py:110-116
Description: These lines use literal status lists, roles, priority bounds `1`/`5`, title limits `3`/`200`, password minimum `4`, `timedelta(days=7)` and `priority <= 2`. Constants for them exist in `utils/helpers.py:110-116` but are never used.
Impact: The meaning is hidden, and changing a rule means editing several files.
Recommendation: Use a single constants module and reference it everywhere (playbook T-14).

### [LOW] Poor naming (AP-20)
File: routes/report_routes.py:10, 24-28, 157-223, routes/task_routes.py:141, 210, utils/helpers.py:1-116
Description: The variables `p1..p5` are cryptic. The blueprint `report_bp` serves `/categories`. `type(tags) == list` is used instead of `isinstance`. The vague module name `helpers` holds unrelated functions.
Impact: It slows readers and hides intent.
Recommendation: Use descriptive names, one module per concern, and `isinstance` (playbook T-14).

### [LOW] Print-style logging (AP-21)
File: routes/task_routes.py:149, 153, 219, 234, routes/user_routes.py:83, 89, 147, services/notification_service.py:21, 24, utils/helpers.py:39, 41
Description: Operational messages and exception text go to `print(...)`.
Impact: There are no log levels or structure, and messages are lost in production.
Recommendation: Use the `logging` module with a module-level logger (playbook T-14).

### [LOW] Dead code and unused imports (AP-22)
File: app.py:7, routes/task_routes.py:7, routes/user_routes.py:6, routes/report_routes.py:7-8, models/task.py:3, 38-60, models/user.py:34-38, utils/helpers.py:2-7, 19-116, services/notification_service.py:1-48, requirements.txt:4-5
Description: These imports are unused: `os, sys, json, time, hashlib`, plus `format_date` and `calculate_percentage` in report_routes. `NotificationService` is never imported. Most helpers (`validate_email`, `sanitize_string`, `generate_id`, `log_action`, `parse_date`, `is_valid_color`, `process_task_data`) and the constants are never called. `Task.validate_status`, `validate_priority` and `is_overdue` and `User.is_admin` are unused. `marshmallow` and `requests` are in the manifest but never imported.
Impact: The dead code adds noise, suggests reuse that isn't happening, and enlarges the dependency surface.
Recommendation: Remove unused imports and dependencies, and either delete dead helpers or wire the useful ones in as the single source (playbook T-14).

================================
Total: 19 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
