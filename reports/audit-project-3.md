================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0
Files:   12 analyzed | ~1155 lines of code

## Summary
CRITICAL: 3 | HIGH: 5 | MEDIUM: 6 | LOW: 4

## Findings

### [CRITICAL] Hardcoded credentials and secrets (AP-01)
File: app.py:13, services/notification_service.py:7-10
Description: The Flask signing key is a literal, app.config['SECRET_KEY'] = 'super-secret-key-123'. The SMTP host, user and password are literals in the constructor: email_user = 'taskmanager@gmail.com', email_password = 'senha123'.
Impact: Anyone with access to the repo can forge signed sessions/cookies and use the mail account. Rotating a secret requires a code change and a redeploy.
Recommendation: Move the secrets and the DB URI to a config module that reads environment variables (python-dotenv is already in the manifest). Add a dev-only fallback for SECRET_KEY and no default for the SMTP password (playbook T-01).

### [CRITICAL] Insecure credential storage and exposure (AP-03)
File: models/user.py:21, models/user.py:27-32, routes/user_routes.py:64, 115, routes/user_routes.py:207-210, seed.py:19, 26, 33
Description: User.to_dict() includes 'password', so GET /users/<id>, POST/PUT /users and POST /login all return the hash. Passwords are hashed with unsalted hashlib.md5. The minimum password length is 4. Login returns a forgeable token, 'fake-jwt-token-' + str(user.id). The seed uses passwords such as '1234' and 'abcd'.
Impact: A leaked unsalted MD5 hash can be reversed almost instantly with rainbow tables. Any client can make up a token for any user id.
Recommendation: Remove password from the serializer. Hash with werkzeug.security generate_password_hash/check_password_hash (Werkzeug is already a Flask dependency) and keep verifying legacy MD5 hashes so existing logins still work. Generate a signed token with itsdangerous using SECRET_KEY (playbook T-03).

### [CRITICAL] Unprotected privileged or destructive endpoints (AP-04)
File: routes/user_routes.py:52, 71-72, routes/user_routes.py:119-122, routes/user_routes.py:134-151, routes/task_routes.py:225-238, routes/report_routes.py:211-223
Description: The project has no authentication or authorization anywhere. Any caller can create a user with role 'admin' (POST /users accepts role from the body), promote any user (PUT /users role), and delete users together with their tasks, as well as tasks and categories.
Impact: Any anonymous caller can escalate privileges and delete the whole dataset.
Recommendation: Add an auth guard (decorator) that validates the signed token, and require the admin role for role changes and destructive routes. This changes behavior for callers without a token and must be reported (playbook T-04).

### [HIGH] God class / God module (AP-05)
File: routes/task_routes.py:1-299, routes/user_routes.py:1-211, routes/report_routes.py:1-223
Description: Each route module (211-299 lines) registers URLs, validates input, runs ORM queries, applies business rules (overdue, statistics, cascading deletes) and builds response dicts. report_routes.py also contains the full category CRUD.
Impact: The modules cannot be tested in isolation, and every change touches routing, rules and persistence together.
Recommendation: Split each module into a thin routes blueprint, a controller and service/model functions; move categories into their own module (playbook T-05, T-06, T-07). Severity lowered from CRITICAL because a separate model layer exists, so the collapse is per module, not total.

### [HIGH] Business logic in the controller / route layer (AP-06)
File: routes/task_routes.py:30-39, 71-80, routes/task_routes.py:140-144, routes/task_routes.py:273-299, routes/user_routes.py:140-142, routes/report_routes.py:30-68, routes/report_routes.py:109-153
Description: The handlers compute overdue status, per-status and per-priority statistics, completion rates and days overdue. They also convert tags and decide to delete a user's tasks before deleting the user.
Impact: The rules can only be reused or unit-tested through HTTP requests, and the same rule is implemented differently in different places.
Recommendation: Move these rules into service functions and model methods such as Task.is_overdue; controllers keep only the HTTP mapping (playbook T-06).

### [HIGH] Data access outside the model layer (AP-07)
File: routes/task_routes.py:14, 42, 51, 67, 147-148, routes/task_routes.py:247-266, 275-281, routes/user_routes.py:12, 35, 67, 140-146, routes/report_routes.py:15-28, 46-56, 159-163, 183-184
Description: Task.query, User.query, Category.query, db.session.add/commit/delete and query composition are called directly inside the route handlers.
Impact: Persistence details are spread over every handler, so a schema change affects all route files.
Recommendation: Put the queries in repository/model functions that the services call (playbook T-05, T-06).

### [HIGH] Tight coupling and no dependency injection (AP-09)
File: app.py:9-31, seed.py:2, services/notification_service.py:5-10, 15
Description: The app is built at import time as a module global, with no factory, and db.create_all() also runs on import. seed.py imports app and gets those side effects. NotificationService builds smtplib.SMTP itself, with its own hardcoded configuration.
Impact: A test cannot create an app with a different config or database, and the mail gateway cannot be replaced by a fake.
Recommendation: Add a create_app(config) factory, keep `app = create_app()` in app.py for the run command, and pass the configuration to the service (playbook T-07).

### [HIGH] Insecure runtime configuration (AP-12)
File: app.py:34, app.py:15
Description: The app starts with app.run(debug=True, host='0.0.0.0', port=5000) and enables CORS(app) for every origin.
Impact: The Werkzeug interactive debugger is reachable from the network, which allows remote code execution. Any website can call the API from a browser.
Recommendation: Read debug, host, port and CORS origins from config/env, with debug off and host 127.0.0.1 by default (playbook T-01, T-12).

### [MEDIUM] N+1 queries (AP-13)
File: routes/task_routes.py:41-57, routes/user_routes.py:22, routes/report_routes.py:55-56, routes/report_routes.py:162-163, routes/task_routes.py:275-279, routes/report_routes.py:19-28
Description: GET /tasks runs User.query.get and Category.query.get for every task. GET /users loads u.tasks lazily for every user. The summary report runs one query per user, GET /categories runs one count per category, and the stats endpoints run 4 to 9 separate COUNT queries.
Impact: The number of queries grows with the number of rows, which raises latency and database load.
Recommendation: Use joined/eager loading and GROUP BY aggregates (func.count with group_by status/priority/user_id/category_id) (playbook T-10).

### [MEDIUM] Duplicated code (AP-14)
File: routes/task_routes.py:30-39, 71-80, 283-287, routes/user_routes.py:171-180, routes/report_routes.py:34-36, 132-135, routes/task_routes.py:17-28, routes/user_routes.py:15-21, 162-169, routes/task_routes.py:96-114, 166-184, utils/helpers.py:57-108, routes/user_routes.py:61, 106, utils/helpers.py:21, routes/task_routes.py:296, routes/report_routes.py:67, 151
Description: The overdue check is copied 6 times even though Task.is_overdue (models/task.py:50-60) exists. Task and user serialization is rebuilt by hand instead of calling to_dict(). The same title/status/priority validation appears in create_task, in update_task and in the unused process_task_data. The email regex is defined 3 times, and the completion-rate formula is repeated 3 times instead of using calculate_percentage.
Impact: Each fix has to be applied to every copy, and the copies already differ (helpers strips titles, the routes do not).
Recommendation: Keep one implementation each: Task.is_overdue, serializers, one validator per entity, shared constants and calculate_percentage (playbook T-11).

### [MEDIUM] Missing or weak input validation (AP-15)
File: routes/task_routes.py:96, 113, 167, 182, routes/task_routes.py:261, 264, routes/user_routes.py:64, 102-103, 124-125, routes/report_routes.py:180, 196-197
Description: The handlers call len(title) and compare priority < 1 without checking the type, so a numeric title or a string priority raises TypeError. int(priority) and int(user_id) on query params raise ValueError. User name and active are stored without validation, category color is stored without calling the existing is_valid_color, and update_category runs 'name' in data without checking that the JSON body is not None.
Impact: Bad input produces 500 errors instead of 400, and invalid data is persisted.
Recommendation: Add type/format validation in a per-entity validator that returns 400 with {'error': ...} (playbook T-12).

### [MEDIUM] Fragmented or unsafe error handling (AP-16)
File: routes/task_routes.py:62-63, 137, 204, 236, routes/user_routes.py:130, 149, routes/report_routes.py:186, 207, 221, utils/helpers.py:46, 48, 88
Description: There are bare except: clauses in every write handler, and get_tasks wraps its whole body in except: and returns a generic 500. The app has no errorhandler, so unhandled errors return Flask's HTML 500 page.
Impact: Real bugs (including SystemExit/KeyboardInterrupt) are swallowed, failures are not logged, and errors come back as JSON or HTML depending on the route.
Recommendation: Register central JSON error handlers (400/404/405/415/500 and a domain ValidationError), and catch only SQLAlchemyError around commits, with rollback (playbook T-12).

### [MEDIUM] Deprecated or obsolete API usage - datetime.utcnow (AP-17)
File: models/task.py:15-16, 52, models/user.py:14, models/category.py:11, routes/task_routes.py:31, 72, 215, 285, routes/user_routes.py:172, routes/report_routes.py:35, 42, 45, 71, 133, services/notification_service.py:35, utils/helpers.py:38, seed.py:66-67, 69-70, 74
Description: datetime.utcnow() and default=datetime.utcnow are used throughout. They have been deprecated since Python 3.12, and the runtime is 3.14.
Impact: Each call emits a DeprecationWarning and will break when the function is removed.
Recommendation: Replace them with a utc_now() helper that returns datetime.now(timezone.utc).replace(tzinfo=None), which keeps the naive-UTC storage format (playbook T-13).

### [MEDIUM] Deprecated or obsolete API usage - Query.get (AP-17)
File: routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227, routes/user_routes.py:29, 94, 136, 155, routes/report_routes.py:105, 192, 213
Description: Model.query.get(id) is legacy in SQLAlchemy 2.x (2.1.9 installed) and Flask-SQLAlchemy 3.1.
Impact: It emits LegacyAPIWarning and is scheduled for removal.
Recommendation: Use db.session.get(Model, id) (playbook T-13).

### [LOW] Magic numbers and magic strings (AP-19)
File: routes/task_routes.py:110, 113, 177, 182, 276-279, models/task.py:39, routes/report_routes.py:19-28, 129, routes/user_routes.py:64, 71, 115, 120
Description: Status strings ('pending', 'done'...), roles, the priority range 1-5, the high-priority threshold `<= 2` and the minimum password length 4 are repeated as literals. The constants already defined in utils/helpers.py:110-116 are never used.
Impact: The meaning of the values is not visible, and a change has to be made in many places.
Recommendation: Use one constants module (statuses, roles, priority bounds, lengths) everywhere (playbook T-14).

### [LOW] Poor naming (AP-20)
File: routes/report_routes.py:24-28, routes/task_routes.py:16, 51, routes/user_routes.py:14, models/task.py:45, models/category.py:14, utils/helpers.py:25
Description: Variables use cryptic names (p1..p5, t, u, cat, p, d, s), and the module name utils/helpers.py is vague. Category routes live in report_routes.py.
Impact: The code is slower to read and the intent is hidden.
Recommendation: Use descriptive names and place each module by its domain (playbook T-14).

### [LOW] Print-style logging (AP-21)
File: routes/task_routes.py:149, 153, 219, 234, routes/user_routes.py:83, 89, 147, services/notification_service.py:21, 24, utils/helpers.py:39-41
Description: Operational events and exception text are written with print().
Impact: There are no log levels or structure, the output is noisy, and exception details are exposed on stdout.
Recommendation: Use the logging module with a module-level logger (playbook T-14).

### [LOW] Dead code and unused imports (AP-22)
File: app.py:7, routes/task_routes.py:7, routes/user_routes.py:6, routes/report_routes.py:7-8, models/task.py:3, utils/helpers.py:3-7, utils/helpers.py:9-116, services/notification_service.py:1-48, models/task.py:38-60, models/user.py:34-38, requirements.txt:4-6
Description: Several imports are unused: os/sys/json in app.py, json/os/sys/time, hashlib/json, format_date/calculate_percentage/json, json, and os/json/sys/math/hashlib. Every helper function and constant in utils/helpers.py is unused. NotificationService is never imported, Task.validate_status/validate_priority/is_overdue and User.is_admin are never called, and marshmallow, requests and python-dotenv are never imported. All of this was checked with a project-wide search.
Impact: The unused code adds noise, suggests reuse that does not exist, and widens the attack surface.
Recommendation: Remove the dead code, or reuse it where it is the intended single implementation (is_overdue, the constants, calculate_percentage). Drop the unused requirements and keep python-dotenv only if config uses it (playbook T-14).

================================
Total: 18 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
