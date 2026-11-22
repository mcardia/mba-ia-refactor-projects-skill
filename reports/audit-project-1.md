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
Description: The Flask signing key is a string literal in the code: app.config["SECRET_KEY"] = "minha-chave-super-secreta-123". The same value is copied into the /health response as "secret_key".
Impact: Anyone who can read the repo, or anyone who calls GET /health, gets the signing key. That lets them forge signed cookies or sessions. Changing the key means editing the code.
Recommendation: Move the secret into a config module that reads environment variables, generate a random value when none is set, and never return it in a response (playbook T-01).

### [CRITICAL] SQL injection through dynamic query construction (AP-02)
File: models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 148-151, 155, 157-161, 163-166, 174, 188, 192, 220, 224, 279-281, 289-297
Description: Almost every query is built by joining strings with request values, for example "SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'" and "nome LIKE '%" + termo + "%'".
Impact: Login can be bypassed with ' OR '1'='1. An attacker can read every table through /produtos/busca?q= and change or delete data through POST /produtos and POST /usuarios. A legitimate value that contains an apostrophe breaks the query.
Recommendation: Use bound "?" parameters for every value, and build the dynamic search filter as a list of clauses plus a list of parameters (playbook T-02).

### [CRITICAL] Insecure credential storage and exposure (AP-03)
File: database.py:75-79, models.py:83, 99, 109-111, 126-129, controllers.py:161, 179, 182
Description: Passwords are stored in plaintext (seed rows such as "admin123" and "123456", and criar_usuario saves "senha" as received). Login compares the plaintext password in SQL. GET /usuarios and GET /usuarios/<id> return the "senha" field. User emails are printed to the log.
Impact: Any read of the database or of the public user list exposes every password, including the admin's. This violates LGPD.
Recommendation: Hash passwords with werkzeug.security (generate_password_hash / check_password_hash), migrate existing plaintext rows, remove "senha" from the serializers, and stop logging personal data (playbook T-03).

### [CRITICAL] Unprotected privileged or destructive endpoints (AP-04)
File: app.py:47-57, 59-78, 16
Description: POST /admin/reset-db deletes all four tables, and POST /admin/query runs any SQL the client sends (cursor.execute(query)). Neither route checks authentication. DELETE /produtos/<id> is also anonymous, and the project has no auth mechanism at all.
Impact: Any anonymous caller can wipe the database, dump the users table or run arbitrary statements.
Recommendation: Remove the raw-SQL endpoint. Put the admin routes behind an admin token read from config (disabled when no token is set) (playbook T-04).

### [CRITICAL] God class / God module (AP-05)
File: app.py:6-88, models.py:133-169, 235-273
Description: app.py does configuration, route registration, inline handlers that run SQL, and server bootstrap. models.py mixes data access with business rules (order total and stock workflow, discount tiers in relatorio_vendas) and returns error dicts that are shaped for HTTP ({"erro": ...}).
Impact: Rules cannot be tested without the database or HTTP, and every change touches unrelated concerns.
Recommendation: Split into config / models (data access) / services (business rules) / controllers / routes, with an app factory (playbooks T-05, T-06, T-07).

### [HIGH] Business logic in the controller / route layer (AP-06)
File: controllers.py:52-54, 205-210, 242-250
Description: Handlers define the allowed categories and statuses, decide the side effects of each status change ("aprovado" means prepare shipping, "cancelado" means return stock), and fire the email/SMS/push notifications after an order is created.
Impact: The workflow cannot be reused or unit-tested without an HTTP request. The "return stock on cancel" step is announced but never done.
Recommendation: Move the order workflow and notifications into a service layer called by thin controllers (playbook T-06).

### [HIGH] Data access outside the model layer (AP-07)
File: app.py:49-55, 66-76, controllers.py:266-274
Description: reset_database and executar_query in app.py, and health_check in controllers.py, call get_db() and cursor.execute directly.
Impact: Persistence details leak into the routes and controllers, so a schema change has to be made in several layers.
Recommendation: Put these queries in model functions (playbooks T-05, T-06).

### [HIGH] Global mutable state (AP-08)
File: database.py:4, 8-10
Description: A module-level db_connection = None is set lazily through `global` and shared by all requests and threads (check_same_thread=False).
Impact: Requests share uncommitted work on that one connection. Concurrent threaded requests can interleave on it, and tests depend on the order they run in.
Recommendation: Open one connection per request in Flask's `g` and close it on teardown (playbook T-07).

### [HIGH] Tight coupling and no dependency injection (AP-09)
File: database.py:5, 10, models.py:1, 5, 25, 44, 55, 66, 73, 90, 106, 123, 134, 172, 204, 236, 276, 286
Description: Every model function imports and calls the concrete get_db(), which connects to the hardcoded path "loja.db".
Impact: The database cannot be pointed elsewhere, for example to a test DB, without editing the code.
Recommendation: Read the DB path from app config and resolve the connection through the app context (playbook T-07).

### [HIGH] Non-atomic multi-step writes and missing referential integrity (AP-10)
File: models.py:139-168, 65-70, database.py:36-53
Description: criar_pedido checks stock in one loop and then inserts the order, its items and the stock decrements in later statements, with no transaction and no rollback. An exception in the middle leaves pending writes on the shared connection, and the next request's commit saves them. Deleting a product leaves itens_pedido rows pointing to nothing. The tables declare no foreign keys.
Impact: Stock can be oversold, partial orders can be persisted, and orphan item rows accumulate.
Recommendation: Wrap the order in one transaction (`with conn:`) with an atomic conditional stock decrement, and roll back on failure (playbook T-08).

### [HIGH] Insecure runtime configuration (AP-12)
File: app.py:8, 9, 88, controllers.py:285-289
Description: DEBUG is hardcoded to True. app.run(host="0.0.0.0", debug=True) exposes the Werkzeug debugger on every interface. CORS(app) allows any origin. /health returns "debug": True, "db_path" and the secret key.
Impact: The interactive debugger allows remote code execution, and internal details are disclosed.
Recommendation: Read DEBUG, HOST and CORS origins from environment-based config with safe defaults, and return only the status and counts from /health (playbooks T-01, T-12).

### [MEDIUM] N+1 queries (AP-13)
File: models.py:186-199, 219-231, 239-254, controllers.py:268-274
Description: Each order listing runs one query per order for its items and one query per item for the product name. The sales report and /health each run several separate COUNT/SUM statements.
Impact: The number of queries grows with orders × items, and latency grows with it.
Recommendation: Use a JOIN for items with product names, and a single aggregate query using SUM(CASE ...) (playbook T-10).

### [MEDIUM] Duplicated code (AP-14)
File: models.py:12-21, 31-40, 304-313, 79-86, 95-102, 177-200, 209-232, controllers.py:28-46, 72-90
Description: The product row-to-dict mapping is written 3 times and the user mapping 2 times. The order-with-items assembly is copied in two functions. The create and update product validation chains are near copies.
Impact: Fixes must be made several times. The copies have already drifted: the update path skips the name-length and category checks.
Recommendation: Use one serializer per entity, one order loader, and one shared product validator (playbook T-11).

### [MEDIUM] Missing or weak input validation (AP-15)
File: controllers.py:43-50, 81-90, 118-121, 153-158, 169-170, 195-201, 239-245, app.py:61-62
Description: preco/estoque are compared without a type check (a string causes a TypeError and a 500). The update path skips the name and category rules. Calling float() on query params is not guarded. The email format is not checked. Order item fields (produto_id, quantidade) are not validated, so a negative quantidade increases stock. dados.get is called when the body is the JSON null. The status update does not check that the order exists.
Impact: Bad input returns 500 errors, and the stored data can be corrupted (negative quantities inflate stock).
Recommendation: Add explicit validation that returns 400 with the existing error messages (playbook T-12).

### [MEDIUM] Fragmented or unsafe error handling (AP-16)
File: controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292, app.py:77-78
Description: Every handler wraps its body in try/except Exception and returns {"erro": str(e)} with a 500. There is no global error handler.
Impact: Internal exception text (SQL errors, tracebacks) leaks to clients, and handling is inconsistent across routes.
Recommendation: Use centralized @app.errorhandler handlers with a generic 500 message and server-side logging (playbook T-12).

### [MEDIUM] Inconsistent response contract (AP-18)
File: controllers.py:20, 183, 206, 70, 103, 142, 292, 245-252
Description: Some error bodies include "sucesso": False and others do not. /health errors use {"status", "detalhes"} instead of {"erro"}. PUT /pedidos/<id>/status returns 200 "Status atualizado" for an order that does not exist.
Impact: Clients have to parse each route differently, and a failed update looks like a success.
Recommendation: Use one error helper ({"erro", "sucesso": False}) and return 404 for unknown orders (playbook T-12).

### [LOW] Magic numbers and magic strings (AP-19)
File: models.py:257-262, 150, 247-253, controllers.py:47-50, 52, 242, app.py:36, controllers.py:285-286, database.py:40
Description: Discount tiers (10000/0.1, 5000/0.05, 1000/0.02), name length limits 2 and 200, and status strings such as 'pendente' are repeated as literals in several files. The version "1.0.0" appears twice.
Impact: Their meaning is hidden, and a change has to be made in several places.
Recommendation: Move them into named constants in one module (playbook T-14).

### [LOW] Poor naming (AP-20)
File: controllers.py:14, 56, 64, 98, 136, 160, models.py:24, 54, 65, 89, 187, 191, 193, 219, 223, 225
Description: `id` shadows the built-in, and there are throwaway names such as cursor2, cursor3 and prod.
Impact: The code is slower to read and the intent is hidden.
Recommendation: Use descriptive names (produto_id, usuario_id) (playbook T-14).

### [LOW] Print-style logging (AP-21)
File: app.py:56, 83-86, controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250
Description: Operational messages and simulated notifications ("ENVIANDO EMAIL ...") use print().
Impact: Logs have no levels or structure, and personal data ends up in stdout.
Recommendation: Use the logging module with module loggers (playbook T-14).

### [LOW] Dead code and unused imports (AP-22)
File: database.py:2, models.py:2
Description: `import os` (database.py) and `import sqlite3` (models.py) are never referenced in their modules.
Impact: Noise and a misleading picture of the dependencies.
Recommendation: Remove the unused imports (playbook T-14).

================================
Total: 20 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
