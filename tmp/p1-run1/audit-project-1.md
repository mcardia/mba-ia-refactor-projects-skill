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
Description: The Flask signing key is written in the source: `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"`. The same literal is copied into the `/health` response.
Impact: Anyone with repo access, or anyone who calls `/health`, gets the signing key. Changing it means editing code.
Recommendation: Read the key from an environment variable in a `config` module, generate a random fallback for development, and never put it in a response (playbook T-01).

### [CRITICAL] SQL injection through dynamic query construction (AP-02)
File: models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 148-151, 155, 157-161, 163-166, 174, 188, 192, 220, 224, 279-281, 291, 293, 295, 297
Description: Every query that takes a value is built by string concatenation. Examples: `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"`, `"... LIKE '%" + termo + "%'"`, and `"... WHERE id = " + str(id)`.
Impact: Login can be bypassed with `' OR '1'='1`. An attacker can also read or change any table through `/produtos/busca?q=`, `POST /produtos` or `POST /usuarios`. Even a legitimate name containing an apostrophe breaks the insert.
Recommendation: Use `?` bound parameters for every value, and build the dynamic search filter from fixed fragments plus a parameter list (playbook T-02).

### [CRITICAL] Insecure credential storage and exposure (AP-03)
File: models.py:83, 99, 109-111, 126-129, database.py:75-79, controllers.py:161, 179, 182, 289
Description:
- Passwords are stored in plaintext (`criar_usuario`) and compared in plaintext inside the SQL (`login_usuario`).
- The seed data contains plaintext passwords (`"admin123"`).
- `GET /usuarios` and `GET /usuarios/<id>` return the `senha` field.
- User emails are printed to stdout on signup and login.
- `/health` returns the secret key.
Impact: Any anonymous caller can download every user's password (`GET /usuarios`). One database leak exposes every account. This violates LGPD.
Recommendation: Hash passwords with `werkzeug.security` (`generate_password_hash`/`check_password_hash`), remove `senha` from serializers, hash the seed passwords, and stop logging personal data (playbook T-03).

### [CRITICAL] Unprotected privileged or destructive endpoints (AP-04)
File: app.py:47-57, app.py:59-78, app.py:16, app.py:26
Description:
- `POST /admin/reset-db` deletes all four tables.
- `POST /admin/query` runs any SQL sent by the client: `cursor.execute(query)` on `dados.get("sql")`.
- There is no authentication or authorization anywhere in the project, including `DELETE /produtos/<id>` and `PUT /pedidos/<id>/status`.
Impact: Any anonymous caller can wipe the database, read or alter any table, or run DDL.
Recommendation: Put the admin routes behind an admin token read from config (return 401/403 when it is missing or wrong), and disable the raw-SQL endpoint by default (playbook T-04).

### [CRITICAL] God class / God module (AP-05)
File: models.py:133-169, models.py:235-273, app.py:1-88, database.py:7-86
Description:
- `models.py` holds data access, the order workflow (stock check, total, stock decrement), the discount policy (`> 10000 -> 0.1`) and dict serialization.
- `app.py` combines configuration, route registration, inline handlers and raw SQL.
- `get_db()` creates the connection, the schema and the seed data in one function.
Impact: Business rules cannot be tested without a database, and every change touches several unrelated concerns.
Recommendation: Split into config, `database` (connection, schema, seed), models (data access only), services (orders, reports), controllers and routes (playbook T-05, T-06, T-07).

### [HIGH] Business logic in the controller / route layer (AP-06)
File: controllers.py:24-62, controllers.py:188-220, controllers.py:237-255
Description:
- `criar_produto` contains the domain rules: valid categories, name length limits and non-negative price/stock.
- `criar_pedido` triggers the email, SMS and push notifications (lines 208-210).
- `atualizar_status_pedido` defines the allowed status transitions and the per-status side effects (lines 242-250).
Impact: These rules cannot be reused or unit-tested without an HTTP request, and create/update have already drifted apart.
Recommendation: Move validation and workflows into a service layer. Controllers should only parse the request, call the service and map the result to a status code (playbook T-06).

### [HIGH] Data access outside the model layer (AP-07)
File: app.py:49-55, app.py:66-76, controllers.py:266-274
Description: `reset_database` and `executar_query` in `app.py` run `cursor.execute` directly. `health_check` in the controller calls `get_db()` and runs four `COUNT(*)` queries.
Impact: Persistence logic is scattered, so schema changes have to be made in several layers.
Recommendation: Move these queries into model functions such as `reset_all()` and `count_entities()` (playbook T-05, T-06).

### [HIGH] Global mutable state (AP-08)
File: database.py:4-5, database.py:7-10
Description: A module-level `db_connection = None` is set lazily through `global db_connection`. All threads share it (`check_same_thread=False`).
Impact: Concurrent requests share one connection and its transaction state, so one request's commit can persist another request's half-finished writes. Tests depend on execution order.
Recommendation: Open one connection per request with `flask.g` and close it in `teardown_appcontext` (playbook T-07).

### [HIGH] Tight coupling and no dependency injection (AP-09)
File: database.py:5, database.py:10, models.py:1, controllers.py:2-3
Description: The database path `"loja.db"` is hardcoded. Every model function imports and calls the concrete `get_db()`, and controllers import `models` and `database` directly.
Impact: The database cannot be pointed at a test or temporary file without editing code.
Recommendation: Read the DB path from config through `current_app`, use an app factory (`create_app(config)`), and give models their connection from one provider (playbook T-07).

### [HIGH] Non-atomic multi-step writes and missing referential integrity (AP-10)
File: models.py:139-168, models.py:65-70, database.py:36-53
Description:
- `criar_pedido` reads stock (line 144), then inserts the order, its items and the stock decrements, with a single `commit` and no rollback path.
- The stock check and the decrement are separate statements (check-then-act).
- `deletar_produto` deletes a product even when `itens_pedido` rows still reference it.
- The schema declares no foreign keys.
Impact: An exception halfway through leaves partial writes on the shared connection, and the next commit persists them. Concurrent orders can oversell stock. Deleting a product leaves orphaned order items.
Recommendation: Wrap the order flow in a single transaction (`with conn:`) with rollback, decrement stock conditionally (`WHERE estoque >= ?`), and refuse to delete a product that is referenced by orders (playbook T-08).

### [HIGH] Insecure runtime configuration (AP-12)
File: app.py:8, app.py:9, app.py:88, controllers.py:285-289
Description:
- `DEBUG = True` is set in config, and `app.run(host="0.0.0.0", debug=True)` starts the server.
- `CORS(app)` has no origin restriction.
- `/health` returns `"debug": True`, `"db_path"`, `"ambiente"` and the secret key.
Impact: The Werkzeug debugger is reachable on every network interface, which allows remote code execution. Internal details are disclosed.
Recommendation: Read debug, host, port and CORS origins from environment-driven config with safe defaults, and strip internal details from `/health` (playbook T-01, T-12).

### [MEDIUM] N+1 queries (AP-13)
File: models.py:139-141, models.py:154-156, models.py:187-193, models.py:219-225, models.py:239-254, controllers.py:268-274
Description:
- Order listings run one query for the orders, then one per order for its items, then one per item for the product name.
- `criar_pedido` looks up each product twice, once per loop.
- The sales report runs five separate aggregate queries, and the health check runs four.
Impact: The number of queries grows with orders × items, so latency grows with the data.
Recommendation: Fetch items with a single `JOIN` for the whole list (`WHERE pedido_id IN (...)`), reuse the products already fetched, and combine the counts into one aggregate query with `SUM(CASE ...)` (playbook T-10).

### [MEDIUM] Duplicated code (AP-14)
File: models.py:12-21, 31-40, 304-313, models.py:79-86, 95-102, models.py:171-201, 203-233, controllers.py:28-46, 72-90
Description:
- The product row-to-dict mapping is repeated 3 times, and the user mapping twice.
- `get_pedidos_usuario` and `get_todos_pedidos` are identical apart from the `WHERE` clause.
- The create and update product validation chains are copies of each other, and the update copy already lost the name and category checks.
Impact: Every fix has to be made several times, and the copies already behave differently.
Recommendation: Extract row serializers, one order-loading function with an optional filter, and one product validator (playbook T-11).

### [MEDIUM] Missing or weak input validation (AP-15)
File: controllers.py:169-170, controllers.py:239-240, app.py:61-62, controllers.py:43-50, controllers.py:85-92, controllers.py:118-121, controllers.py:153-160, controllers.py:245, models.py:140, 144-146
Description:
- `login`, `atualizar_status_pedido` and `executar_query` call `dados.get` on a possibly `None` body.
- `preco < 0` is compared on values whose type is never checked, and `float()` is called on query parameters without error handling.
- The update route skips the category and name checks.
- Users are created with no email format check and no uniqueness check.
- A status update on a non-existent order returns 200.
- Order items are not validated (`item["produto_id"]` raises `KeyError`), and a negative `quantidade` passes the stock check and increases stock.
Impact: Bad input produces 500 errors, and stock and order totals can be corrupted (negative quantities create negative totals).
Recommendation: Validate types, ranges and existence at the service boundary, returning 400/404, and require positive integer quantities (playbook T-12).

### [MEDIUM] Fragmented or unsafe error handling (AP-16)
File: controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292, app.py:77-78
Description: Every handler wraps its body in `try/except Exception` and returns `{"erro": str(e)}` with status 500. There is no global `errorhandler`.
Impact: Internal details (SQL errors, schema names) leak to clients, real bugs are hidden, and the same handling is copied 17 times.
Recommendation: Use domain exceptions plus centralized `@app.errorhandler` handlers that return a generic message for 500s and log the traceback (playbook T-12).

### [MEDIUM] Inconsistent response contract (AP-18)
File: controllers.py:20, 142, 183, 206, 292
Description: Error bodies sometimes include `"sucesso": False` (lines 20, 183, 206) and sometimes do not (line 142, and most 400s). `/health` reports errors as `{"status": "erro", "detalhes": ...}` instead of `{"erro": ...}`.
Impact: Clients have to parse errors differently per route.
Recommendation: Build every error with a single helper (`{"erro": msg, "sucesso": False}`) used by the error handlers (playbook T-12).

### [LOW] Magic numbers and magic strings (AP-19)
File: models.py:257-262, controllers.py:47-50, controllers.py:52, controllers.py:242, models.py:150, 247, 250, 253, app.py:36, controllers.py:285
Description:
- The discount thresholds and rates (`10000`, `0.1`, `5000`, `0.05`, `1000`, `0.02`) are literals.
- The name length limits `2` and `200` are literals.
- The category list and the status strings are repeated across files.
- The version `"1.0.0"` is duplicated.
Impact: The business rules have no names, and changing one means editing several files.
Recommendation: Define named constants in a single domain constants module (playbook T-14).

### [LOW] Poor naming (AP-20)
File: controllers.py:14, 56, 64, 98, 136, 160, models.py:24, 54, 65, 89, models.py:187, 191, 219, 223, models.py:4
Description:
- `id` is used as a parameter or local name, shadowing the built-in.
- The cursors are named `cursor2` and `cursor3`.
- Naming conventions are mixed (`get_todos_produtos` vs `listar_produtos`, `get_` vs `buscar_`).
Impact: The code is harder to read.
Recommendation: Rename internals to `produto_id`, `usuario_id` and so on, and use one naming convention. URL parameter names keep their public meaning (playbook T-14).

### [LOW] Print-style logging (AP-21)
File: controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250, app.py:56, 83-86
Description: Operational messages use `print`, and the notifications are faked with `print("ENVIANDO EMAIL: ...")`.
Impact: There are no log levels or structure, and personal data ends up in stdout.
Recommendation: Use the `logging` module with module loggers, and put a notification service behind an interface (playbook T-14).

### [LOW] Dead code and unused imports (AP-22)
File: database.py:2, models.py:2
Description: `import os` in `database.py` and `import sqlite3` in `models.py` are never used; a project-wide search finds no `os.` or `sqlite3.` reference in those files.
Impact: Noise.
Recommendation: Remove the unused imports (playbook T-14).

Deprecated APIs (AP-17): none detected. The code uses no `datetime.utcnow`, no `before_first_request`, no `flask.escape`/`Markup`, and no SQLAlchemy calls on Flask 3.1.1 / Python 3.14. AP-11 (callback hell) does not apply because the code is synchronous Python.

================================
Total: 20 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
