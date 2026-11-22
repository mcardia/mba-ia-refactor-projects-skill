================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~780 lines of code

## Summary
CRITICAL: 5 | HIGH: 6 | MEDIUM: 5 | LOW: 4

## Findings

### [CRITICAL] Hardcoded credentials and secrets (AP-01)
File: app.py:7, controllers.py:289
Description: The Flask signing key is a literal, app.config["SECRET_KEY"] = "minha-chave-super-secreta-123". The same value appears again as a literal in the /health response.
Impact: Anyone with repo access can forge signed session cookies. Rotating the key means changing code in two places.
Recommendation: Load SECRET_KEY from an environment variable in a config module, with a random fallback for development only (playbook T-01).

### [CRITICAL] SQL injection through dynamic query construction (AP-02)
File: models.py:28, 48-49, 58-60, 68, 92, 110, 127-128, 140, 149-150, 155, 158-160, 164-165, 174, 188, 192, 220, 224, 280, 291, 293, 295, 297
Description: Every query that takes a value builds it by string concatenation, e.g. "SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'" and "nome LIKE '%" + termo + "%'". The values come from the JSON body and query string.
Impact: Login bypass with ' OR '1'='1. Through /produtos/busca?q= or POST bodies an attacker can read any table, including plaintext passwords, or change/delete data.
Recommendation: Use "?" bound parameters for every value, including the LIKE pattern (playbook T-02).

### [CRITICAL] Insecure credential storage and exposure (AP-03)
File: models.py:110, 127-128, models.py:83, 99, database.py:76-78, controllers.py:286-289, controllers.py:161, 179, 182
Description: Passwords are stored and compared in plaintext. The user serializers return "senha", so GET /usuarios and GET /usuarios/<id> expose every password. The seed inserts plaintext passwords ("admin123", "123456"). /health echoes secret_key, debug and db_path. User emails are written to stdout on every create/login.
Impact: One request to GET /usuarios leaks every credential, including the admin's. This violates LGPD and lets anyone take over any account.
Recommendation: Hash passwords with werkzeug.security (generate_password_hash / check_password_hash), remove "senha" from serializers, drop secrets from /health and personal data from logs (playbook T-03).

### [CRITICAL] Unprotected privileged or destructive endpoints (AP-04)
File: app.py:47-57, app.py:59-78, app.py:16, app.py:26
Description: POST /admin/reset-db deletes every row in all four tables. POST /admin/query runs any SQL string the client sends (cursor.execute(query)). Neither has any authentication. DELETE /produtos/<id> and PUT /pedidos/<id>/status are also open, and there is no auth guard anywhere in the project.
Impact: Any anonymous caller can wipe or dump the whole database or run arbitrary DDL/DML.
Recommendation: Remove the arbitrary-SQL endpoint. Put reset-db behind an admin token read from config, and disable it when no token is configured (playbook T-04).

### [CRITICAL] God class / God module (AP-05)
File: app.py:1-88, models.py:133-169, models.py:235-273
Description: app.py holds configuration, route registration, inline handlers and raw SQL (reset/query), plus server bootstrap. models.py combines data access with business rules: the order workflow with stock checks and totals at 139-166, and discount tiers at 256-262. It also builds HTTP-shaped dicts by hand.
Impact: No layer can be tested on its own. Every change to a rule, query or route touches the same files.
Recommendation: Split into config, routes (views), controllers, services and models, with app.py as a thin entry point (playbook T-05, T-06, T-07).

### [HIGH] Business logic in the controller / route layer (AP-06)
File: controllers.py:24-62, controllers.py:52-54, controllers.py:208-210, controllers.py:242-250
Description: Handlers hold domain rules: the valid-category list, the name length limits, the allowed status transitions, and post-order and status-change notifications (simulated as prints of "ENVIANDO EMAIL/SMS/PUSH").
Impact: These rules cannot be reused or unit-tested without an HTTP request, and they drift between handlers.
Recommendation: Move the rules and notification side effects into service functions that controllers call (playbook T-06).

### [HIGH] Data access outside the model layer (AP-07)
File: app.py:49-55, app.py:66-76, controllers.py:266-274
Description: app.py runs DELETE statements and client SQL directly through get_db(). health_check in controllers.py runs four queries itself.
Impact: Persistence details leak into the entry point and controllers, so schema changes ripple across layers.
Recommendation: Move these queries into model functions such as reset_all and contagens (playbook T-05, T-06).

### [HIGH] Global mutable state (AP-08)
File: database.py:4, database.py:8-11
Description: A module-level db_connection = None is set lazily through "global db_connection". It is a single connection shared by every request thread, with check_same_thread=False.
Impact: Concurrent requests share one connection and its open transaction. One request's commit can commit another request's half-done writes, and errors on one thread corrupt state for the others.
Recommendation: Open one connection per request in flask.g and close it in teardown_appcontext; read the DB path from config (playbook T-07).

### [HIGH] Tight coupling and no dependency injection (AP-09)
File: database.py:5, database.py:10, models.py:1, controllers.py:3
Description: The DB path "loja.db" is hardcoded and sqlite3.connect is called directly. Every model function, and the controllers, import the concrete get_db and call it.
Impact: A test cannot point the app at another database (for example in-memory) without editing source code.
Recommendation: Use an app factory with configuration injection (DATABASE path from config/env) and a per-request connection provider (playbook T-07).

### [HIGH] Non-atomic multi-step writes and missing referential integrity (AP-10)
File: models.py:139-168, models.py:65-70, database.py:37-53
Description: criar_pedido reads stock, inserts the order, re-reads prices, inserts items and decrements stock in separate statements, with one commit at the end and no rollback. If an exception is raised mid-loop (for example a missing "quantidade" key), the writes stay pending on the shared connection. Stock is checked and decremented separately (check-then-act). deletar_produto removes products that itens_pedido still references, and the tables declare no foreign keys.
Impact: Oversold stock under concurrency, orphan order rows committed later by unrelated requests, and dangling item references.
Recommendation: Wrap the order flow in an explicit transaction with rollback and use a conditional stock decrement (UPDATE ... WHERE estoque >= ?) (playbook T-08).

### [HIGH] Insecure runtime configuration (AP-12)
File: app.py:8, app.py:88, app.py:9, controllers.py:285-289
Description: DEBUG is on in config and in app.run(debug=True), together with host="0.0.0.0", which exposes the Werkzeug interactive debugger on every interface. CORS(app) allows any origin. /health reports "ambiente": "producao" with "debug": True and the secret key.
Impact: Anyone on the network can reach the Werkzeug debugger and run code remotely, and internal details are disclosed.
Recommendation: Read DEBUG, HOST, PORT and CORS origins from environment-backed config with safe defaults, and stop echoing config in responses (playbook T-01, T-12).

### [MEDIUM] N+1 queries (AP-13)
File: models.py:187-199, models.py:219-231, models.py:154-156, models.py:239-254, controllers.py:268-274
Description: Order listings run one query per order for its items and another per item for the product name, using nested cursor2/cursor3. criar_pedido re-selects each product's price. The sales report runs 5 separate COUNT/SUM queries and health runs 4 COUNT queries.
Impact: Query count grows as orders × items, so latency grows with data size.
Recommendation: Use a single JOIN for orders/items/product names and conditional aggregation (SUM(CASE ...)) for the report (playbook T-10).

### [MEDIUM] Duplicated code (AP-14)
File: models.py:12-21, 31-40, 304-313, models.py:79-86, 95-102, models.py:171-201, 203-233, controllers.py:28-46, 72-90
Description: The product row-to-dict mapping is copied 3 times and the user mapping twice. get_pedidos_usuario and get_todos_pedidos are identical apart from the WHERE clause. The create/update product validation chain is duplicated, and the update copy has already drifted: it skips the name length and category checks.
Impact: Every fix has to be applied several times, and the copies already behave differently.
Recommendation: Use one serializer per entity, one order-listing query with an optional filter, and one shared product validator (playbook T-11).

### [MEDIUM] Missing or weak input validation (AP-15)
File: controllers.py:169-170, controllers.py:239-240, app.py:61-62, controllers.py:43-50, controllers.py:118-121, controllers.py:81-90, controllers.py:153-158, controllers.py:245, models.py:140, 144
Description: login, the status update and admin/query call .get() on the result of request.get_json() without a None check. preco and estoque are compared with "< 0" without a type check, so a string causes a TypeError. float() on preco_min/preco_max is not guarded. Update skips the category and name checks. There is no email format check. Order items are indexed as item["produto_id"] without validation. The status update returns 200 for an order that does not exist.
Impact: Malformed input produces 500 errors instead of 400, and invalid data (unknown categories, bad emails) gets persisted.
Recommendation: Validate body presence, types, ranges and existence in the controller/service, returning 400/404 (playbook T-12).

### [MEDIUM] Fragmented or unsafe error handling (AP-16)
File: controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292, app.py:77-78
Description: Every handler wraps its body in "try/except Exception" and returns {"erro": str(e)} with 500. There is no app-level errorhandler.
Impact: Exception text (SQL errors, schema details) leaks to clients, and the boilerplate hides bugs and repeats 17 times.
Recommendation: Add centralized error handlers (generic 500 that logs server-side, plus 404/405 JSON) and drop the per-handler catch-alls (playbook T-12).

### [MEDIUM] Inconsistent response contract (AP-18)
File: controllers.py:20, controllers.py:70, controllers.py:103, controllers.py:142, controllers.py:292
Description: Not-found bodies are sometimes {"erro", "sucesso": false} (line 20) and sometimes only {"erro"} (lines 70, 103, 142). The health failure uses a different shape, {"status": "erro", "detalhes"}.
Impact: Clients need per-route parsing of error responses.
Recommendation: Use a single error-response helper for all failures (playbook T-12).

### [LOW] Magic numbers and magic strings (AP-19)
File: models.py:257-262, controllers.py:47-50, controllers.py:52, controllers.py:242, models.py:150, 247, 250, 253, app.py:35, controllers.py:285
Description: Discount tiers (10000/0.1, 5000/0.05, 1000/0.02), name limits 2/200, the category list, status literals ('pendente', 'aprovado', 'cancelado') and the version "1.0.0" are all inline, some repeated across files.
Impact: Business meaning is hidden, and changing a rule means editing several places.
Recommendation: Extract named constants into a single module (playbook T-14).

### [LOW] Poor naming (AP-20)
File: controllers.py:14, 56, 64, 98, 136, 160, models.py:24, 54, 65, 89, models.py:187, 191, 219, 223
Description: The parameter/variable "id" shadows the builtin, and cursors are named cursor2/cursor3.
Impact: Readers lose intent, and shadowing invites subtle bugs.
Recommendation: Rename to produto_id/usuario_id/novo_id; the JOIN refactor removes the extra cursors (playbook T-14).

### [LOW] Print-style logging (AP-21)
File: controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250, app.py:56, 83-86
Description: Operational messages and simulated notifications ("ENVIANDO EMAIL: ...") use print(), sometimes with user emails.
Impact: No levels or structure, noisy output, and personal data in logs.
Recommendation: Use the logging module with a module logger, and send notifications through a notification service that logs (playbook T-14).

### [LOW] Dead code and unused imports (AP-22)
File: database.py:2, models.py:2
Description: "import os" in database.py and "import sqlite3" in models.py are never referenced; a project-wide search finds no os. or sqlite3. usage in those files.
Impact: Noise that suggests dependencies which don't exist.
Recommendation: Remove the unused imports (playbook T-14).

================================
Total: 20 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
