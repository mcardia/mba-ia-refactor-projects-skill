================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0
Files:   13 analyzed | ~1158 lines of code

## Summary
CRITICAL: 3 | HIGH: 5 | MEDIUM: 5 | LOW: 4

## Findings

### [CRITICAL] Hardcoded credentials and secrets (AP-01)
File: app.py:13, services/notification_service.py:7-10
Description: The Flask signing key is a literal, `app.config['SECRET_KEY'] = 'super-secret-key-123'`. The SMTP host, user and password are also literals inside the class: `self.email_user = 'taskmanager@gmail.com'`, `self.email_password = 'senha123'`.
Impact: Anyone with repo access can forge signed session data and log in to the mail account. Rotating either secret means changing the code.
Recommendation: Move these values into a config module that reads environment variables, with no secret defaults in source (playbook T-01).

### [CRITICAL] Insecure credential storage and exposure (AP-03)
File: models/user.py:21, models/user.py:27-32, routes/user_routes.py:33, routes/user_routes.py:64, routes/user_routes.py:85, routes/user_routes.py:129, routes/user_routes.py:209-210, seed.py:19, seed.py:26, seed.py:33
Description: Passwords are hashed with unsalted `hashlib.md5`. `User.to_dict()` includes `'password': self.password`, so the hash comes back from GET/POST/PUT /users and from /login. The login "token" is `'fake-jwt-token-' + str(user.id)`. The minimum password length is 4, and the seed uses passwords such as '1234'.
Impact: Unsalted MD5 hashes crack almost instantly, and every API caller receives them. Anyone can forge a token for any user id.
Recommendation: Use salted adaptive hashing (werkzeug `generate_password_hash`/`check_password_hash`), drop `password` from the serializer, and return a signed token instead of a concatenated one (playbook T-03).

### [CRITICAL] Unprotected privileged or destructive endpoints (AP-04)
File: routes/user_routes.py:52, routes/user_routes.py:71, routes/user_routes.py:119-122, routes/user_routes.py:134-151, routes/task_routes.py:225-238, routes/report_routes.py:12-101, routes/report_routes.py:211-223, app.py:18-20
Description: No route has an authentication or authorization check, and there is no auth middleware anywhere. The client-supplied `role` (including 'admin') is accepted on POST and PUT /users. DELETE on users, tasks and categories, and the full summary report, are open to anonymous callers.
Impact: Any anonymous caller can make themselves admin, delete every user and task, or read productivity data for every user.
Recommendation: Add a token-verifying guard to the mutating and privileged routes, and only let an authenticated admin change roles (playbook T-04).

### [HIGH] Business logic in the controller / route layer (AP-06)
File: routes/task_routes.py:12-63, routes/task_routes.py:85-154, routes/task_routes.py:156-223, routes/task_routes.py:273-299, routes/user_routes.py:42-90, routes/user_routes.py:140-142, routes/report_routes.py:12-101, routes/report_routes.py:103-155
Description: The handlers compute overdue state, completion rates, per-status and per-priority statistics, 7-day activity and per-user productivity. They also run the validation chains and the cascading delete of a user's tasks. Several handlers are 50-90 lines long.
Impact: None of these rules can be reused or unit-tested without an HTTP request, and a rule change means editing several handlers.
Recommendation: Move each rule into a model method or a service (task/report services), and leave handlers to parse the request, call the service and choose the status code (playbook T-06).

### [HIGH] Data access outside the model layer (AP-07)
File: routes/task_routes.py:14, 42, 51, 67, 117, 122, 147-148, 158, 188, 195, 218, 227, 232-233, 247-266, 275-281; routes/user_routes.py:12, 29, 35, 67, 81-82, 94, 109, 128, 136, 140-146, 155, 159, 197; routes/report_routes.py:15-30, 46-56, 105, 109, 159, 163, 183-184, 192, 205, 213, 218-219
Description: Every route module calls `Model.query...`, `db.session.add/delete/commit` and `db.or_` filters directly. Category CRUD also lives in `report_routes.py`.
Impact: Persistence details are spread across the HTTP layer, so a schema or query change touches every handler.
Recommendation: Put queries behind model/repository functions, and move category routes into their own controller and blueprint (playbook T-05, T-06).

### [HIGH] Tight coupling and no dependency injection (AP-09)
File: app.py:9-31, services/notification_service.py:5-20
Description: The app is configured and `db.create_all()` runs at import time, with no app factory, so tests cannot build the app with different settings. `NotificationService` hardcodes its own SMTP settings and calls `smtplib.SMTP(...)` directly.
Impact: The app cannot be tested against another database or config, and the mail transport cannot be faked.
Recommendation: Add a `create_app(config)` factory, and give the notification service its settings and transport through its constructor (playbook T-07).

### [HIGH] Non-atomic multi-step writes and missing referential integrity (AP-10)
File: routes/report_routes.py:211-223, models/task.py:13-14, routes/user_routes.py:67-69, routes/user_routes.py:109-111
Description: DELETE /categories removes the category but leaves tasks whose `category_id` points to it. SQLite foreign keys are never enabled (no `PRAGMA foreign_keys=ON`). Email uniqueness is checked first and inserted later (check-then-act), so a concurrent duplicate fails as a generic 500.
Impact: Orphan tasks reference missing categories, and duplicate-email races return an unexplained error.
Recommendation: Clean up or null out child rows inside the same transaction, enable FK enforcement, and turn the IntegrityError into a 409 (playbook T-08).

### [HIGH] Insecure runtime configuration (AP-12)
File: app.py:34, app.py:15
Description: `app.run(debug=True, host='0.0.0.0', port=5000)` turns on the Werkzeug debugger on every interface. `CORS(app)` allows any origin.
Impact: Anyone who can reach the server can run code through the interactive debugger, and any website can call the API from a browser.
Recommendation: Read debug, host, port and allowed CORS origins from config, with safe defaults (debug off, localhost) (playbook T-01, T-12).

### [MEDIUM] N+1 queries (AP-13)
File: routes/task_routes.py:41-57, routes/user_routes.py:22, routes/report_routes.py:53-56, routes/report_routes.py:163, routes/task_routes.py:275-279, routes/report_routes.py:15-28
Description: GET /tasks runs `User.query.get` and `Category.query.get` for each task. GET /users reads the lazy `len(u.tasks)` per user. The summary report queries tasks once per user, and GET /categories counts once per category. The stats and summary routes run 5 and 12 separate `COUNT(*)` queries.
Impact: The number of queries grows with row count, so latency rises as data grows.
Recommendation: Use eager loading or joins and `GROUP BY` aggregates (playbook T-10).

### [MEDIUM] Duplicated code (AP-14)
File: routes/task_routes.py:30-39, 71-80, 283-287; routes/user_routes.py:171-180; routes/report_routes.py:34-36, 132-135; routes/task_routes.py:17-28; routes/user_routes.py:15-23, 162-169; routes/task_routes.py:96-100 vs 166-170, 110-114 vs 176-184; routes/user_routes.py:61, 106; utils/helpers.py:21, 57-108
Description: The overdue rule is copied 6 times, although `Task.is_overdue()` (models/task.py:50-60) already implements it. Serialization is copied by hand next to `to_dict()`. The title, status and priority validation is duplicated between create and update, and the email regex appears 3 times. `process_task_data` reimplements the same rules and is never used.
Impact: Fixes must be applied in several places, and the copies already differ (helpers strips titles and accepts dd/mm/YYYY dates, the routes do not).
Recommendation: Keep one validator and one serializer per entity and call `is_overdue()` everywhere (playbook T-11).

### [MEDIUM] Missing or weak input validation (AP-15)
File: routes/task_routes.py:113, 167-170, 182, 261, 264; routes/report_routes.py:196-202, 180; routes/user_routes.py:102-103, 124-125
Description: The code compares `priority < 1` without a type check (a string raises TypeError), calls `len(data['title'])` on possible None or non-string values, and calls `int(priority)`/`int(user_id)` on query params without handling errors. PUT /categories never checks `request.get_json()` for None. Color, name and `active` values are stored without validation.
Impact: Malformed input causes 500 errors instead of 400, and invalid data reaches the database.
Recommendation: Add type, format and length checks in one validation layer and return 400 for bad input (playbook T-12).

### [MEDIUM] Fragmented or unsafe error handling (AP-16)
File: routes/task_routes.py:62-63, 137, 151-154, 204, 221-223, 236; routes/user_routes.py:87-90, 130, 149; routes/report_routes.py:186, 207, 221; app.py:9-31
Description: Handlers use bare `except:` clauses throughout. GET /tasks wraps the whole handler in one and hides every error as `{'error': 'Erro interno'}`. No global `errorhandler` is registered.
Impact: Bugs are hidden (including SystemExit/KeyboardInterrupt), and error handling is repeated and inconsistent.
Recommendation: Register central error handlers, raise domain exceptions, and catch only specific exceptions (playbook T-12).

### [MEDIUM] Deprecated or obsolete API usage (AP-17)
File: models/task.py:15, 16, 52; models/user.py:14; models/category.py:11; routes/task_routes.py:31, 72, 215, 285; routes/user_routes.py:172; routes/report_routes.py:35, 42, 45, 71, 133; services/notification_service.py:35; utils/helpers.py:38; seed.py:66-74 — and routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227; routes/user_routes.py:29, 94, 136, 155; routes/report_routes.py:105, 192, 213
Description: `datetime.utcnow()` is deprecated since Python 3.12 (the runtime is 3.14), and `Model.query.get(id)` is legacy in SQLAlchemy 2.x / Flask-SQLAlchemy 3.x.
Impact: Both emit deprecation warnings and will break on future upgrades.
Recommendation: Replace them with a `utcnow()` helper built on `datetime.now(timezone.utc)` (stored naive-UTC) and with `db.session.get(Model, id)` (playbook T-13).

### [LOW] Magic numbers and magic strings (AP-19)
File: routes/task_routes.py:96, 99, 110, 113, 177, 182; routes/user_routes.py:64, 71, 115, 120; routes/report_routes.py:24-28, 45, 84-88, 129; models/task.py:39, 46; utils/helpers.py:110-116
Description: Status lists, role lists, priority bounds 1-5, title lengths 3/200, password length 4, the 7-day window and `priority <= 2` are literals repeated across files. Matching constants exist in `utils/helpers.py:110-116`, but nothing uses them.
Impact: The meaning of each value is hidden, and changing a rule means editing many places.
Recommendation: Use named constants from one module (playbook T-14).

### [LOW] Poor naming (AP-20)
File: routes/report_routes.py:24-28; routes/task_routes.py:16, 51, 268; routes/user_routes.py:14; models/task.py:45; models/user.py:27, 31; models/category.py:14; routes/task_routes.py:242
Description: The code uses cryptic names such as `p1..p5`, `t`, `u`, `c`, `cat`, `p`, `pwd` and `d`, and `query` holds the search term right next to the ORM `Task.query`.
Impact: The code is slower to read and its intent is unclear.
Recommendation: Use descriptive names (playbook T-14).

### [LOW] Print-style logging (AP-21)
File: routes/task_routes.py:149, 153, 219, 234; routes/user_routes.py:83, 89, 147; services/notification_service.py:21, 24; utils/helpers.py:39-41
Description: Operational events and exception text are written with `print(...)`.
Impact: Output has no log levels or structure and cannot be filtered or routed.
Recommendation: Use the `logging` module with a module logger (playbook T-14).

### [LOW] Dead code and unused imports (AP-22)
File: app.py:7; routes/task_routes.py:7; routes/user_routes.py:6; routes/report_routes.py:7-8; models/task.py:3; utils/helpers.py:3-7, 9-108; services/notification_service.py:1-48; models/task.py:38-60; models/user.py:34-38; requirements.txt:4-6
Description: These imports are never used: `os, sys, json` (app.py), `json, os, sys, time` (task_routes), `hashlib, json` (user_routes), `format_date, calculate_percentage, json` (report_routes), `json` (task.py), and `os, json, sys, math, hashlib` (helpers). No module calls any helpers function or imports `NotificationService`. `Task.validate_status/validate_priority/is_overdue` and `User.is_admin` are never called. `marshmallow`, `requests` and `python-dotenv` are never imported.
Impact: The unused code looks reusable but is not, adds noise, and enlarges the dependency surface.
Recommendation: Delete unused imports and symbols, or wire the useful ones in (`is_overdue`, constants, validators), and trim the manifest (playbook T-14).

================================
Total: 17 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
