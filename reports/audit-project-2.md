================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js) + Express 4.22.1
Files:   3 analyzed | ~180 lines of code

## Summary
CRITICAL: 4 | HIGH: 6 | MEDIUM: 4 | LOW: 4

## Findings

### [CRITICAL] Hardcoded credentials and secrets (AP-01)
File: src/utils.js:1-7, src/AppManager.js:2
Description: A config object exported from utils hardcodes dbUser "admin_master", dbPass "senha_super_secreta_prod_123", paymentGatewayKey "pk_live_1234567890abcdef", smtpUser and port 3000.
Impact: Anyone with repo access gets the production DB password and the live payment key. Rotating them needs a code change.
Recommendation: Move the values to a config module that reads environment variables (with safe non-secret defaults for port) (playbook T-01).

### [CRITICAL] Insecure credential storage and exposure (AP-03)
File: src/utils.js:17-23, src/AppManager.js:18, 45, 68
Description: Passwords are "hashed" with a home-made loop that repeats base64(pwd).substring(0, 2) and cuts the result to 10 chars. The seed stores the plaintext password '123'. A missing password falls back to "123456". The full card number and the gateway key are written to console.log.
Impact: The hashes can be reversed trivially, and passwords that share a prefix collide. Card data and the live key end up in logs (a PCI violation). Every account created without a password gets a known default.
Recommendation: Hash with crypto.scrypt plus a per-user salt, stop logging card and key (log a masked card at most), and drop the default password fallback (playbook T-03).

### [CRITICAL] Unprotected privileged or destructive endpoints (AP-04)
File: src/AppManager.js:80, 131-137
Description: GET /api/admin/financial-report exposes revenue and student names, and DELETE /api/users/:id deletes users. Neither has any authentication or authorization, and the project has no auth middleware at all.
Impact: Any anonymous caller can read financial and personal data or delete any user.
Recommendation: Add an admin-guard middleware (token from env config) on admin/destructive routes (playbook T-04).

### [CRITICAL] God class / God module (AP-05)
File: src/AppManager.js:4-139
Description: The AppManager class creates the DB connection (7), the schema (12-16) and the seed data (18-21), registers every route (25-137), and holds the payment logic, the reporting and all the SQL.
Impact: No piece can be tested on its own, and every change touches the same class.
Recommendation: Split into config, db (connection + schema/seed), models (repositories), services (checkout, report), controllers, routes (playbook T-05, T-06, T-07).

### [HIGH] Business logic in the controller / route layer (AP-06)
File: src/AppManager.js:43-75, 89-127
Description: The checkout handler decides the payment result itself (cc.startsWith("4") ? "PAID" : "DENIED"), creates the user automatically, enrolls them, records the payment and writes the audit log. The report handler adds up revenue and builds the per-student rows.
Impact: Neither the payment flow nor the revenue calculation can be reused or unit-tested without an HTTP request.
Recommendation: Move them to CheckoutService and ReportService. Handlers keep only request parsing and choosing the status code (playbook T-06).

### [HIGH] Data access outside the model layer (AP-07)
File: src/AppManager.js:37, 40, 50, 54, 57, 69, 83, 92, 104, 106, 133
Description: db.get/db.run/db.all calls with raw SQL are made directly inside route handlers.
Impact: Persistence details leak into HTTP code, so a schema change means editing the handlers.
Recommendation: Put every query into model/repository modules (playbook T-05, T-06).

### [HIGH] Global mutable state (AP-08)
File: src/utils.js:9-10, 14, 25
Description: A module-level `globalCache = {}` is filled on every checkout through logAndCache and exported. A module-level `let totalRevenue = 0` is also exported.
Impact: State is hidden, shared across requests, grows without limit, and makes behavior depend on the order of calls.
Recommendation: Replace it with an injected cache instance owned by the service, and remove totalRevenue (playbook T-07).

### [HIGH] Tight coupling and no dependency injection (AP-09)
File: src/AppManager.js:1-2, 7
Description: The constructor creates its own `new sqlite3.Database(':memory:')` and imports config and helpers from utils directly.
Impact: The DB or payment gateway cannot be swapped for a fake in tests, so changing a dependency means editing business code.
Recommendation: Create the connection in a db module and pass it into repositories and services through constructors or factories (playbook T-07).

### [HIGH] Non-atomic multi-step writes and missing referential integrity (AP-10)
File: src/AppManager.js:12-16, 50-61, 69-71, 133
Description: Checkout runs separate INSERTs into users, enrollments, payments and audit_logs with no transaction. A user row is created before the payment is decided. DELETE removes the user and leaves its enrollments and payments behind (the response text admits it). The schema declares no foreign keys.
Impact: A failure partway through leaves partial records (an enrollment without a payment, or a user created for a denied payment), and deleted users leave orphan rows behind.
Recommendation: Wrap the checkout writes in BEGIN/COMMIT/ROLLBACK and delete the child rows (payments, enrollments) in the same transaction as the user (playbook T-08).

### [HIGH] Callback hell / deeply nested asynchronous flow (AP-11)
File: src/AppManager.js:37-77, 83-128
Description: Checkout nests 6 levels of db callbacks. The report nests 5 levels and tracks completion with the manual counters `coursesPending--` and `enrPending--`.
Impact: The code is hard to read, errors are dropped, and two responses or none can be sent.
Recommendation: Promisify the db wrapper and rewrite the flows with async/await (playbook T-09).

### [MEDIUM] N+1 queries (AP-13)
File: src/AppManager.js:89-106
Description: The report runs one query per course for enrollments (92), then for each enrollment one query for the user (104) and one for the payment (106).
Impact: The number of queries grows as 1 + C + 2E, so latency rises with the data.
Recommendation: Use a single LEFT JOIN query over courses, enrollments, users and payments, grouped in code (playbook T-10).

### [MEDIUM] Missing or weak input validation (AP-15)
File: src/AppManager.js:29-35, 132
Description: Checkout only checks that usr, eml, c_id and card are present. There is no type check on c_id, no email format check, no card format check and no length limits. The :id in DELETE is used without validation.
Impact: Malformed data gets stored, and a non-string card makes cc.startsWith throw.
Recommendation: Validate types and formats in the controller and return 400 on invalid input (playbook T-12).

### [MEDIUM] Fragmented or unsafe error handling (AP-16)
File: src/AppManager.js:38, 57, 92-93, 104, 106, 133
Description: The callback `err` is ignored in several places (57, 92, 104, 106, 133). If line 92 fails, `enrollments` is undefined and `.length` crashes the process. Line 38 treats a DB error as a 404. There is no global error middleware.
Impact: The process can crash, real failures are hidden or reported with the wrong status, and status codes are inconsistent.
Recommendation: Propagate errors with async/await and add a centralized Express error handler (playbook T-12).

### [MEDIUM] Inconsistent response contract (AP-18)
File: src/AppManager.js:35, 38, 41, 48, 60, 87, 135
Description: Errors come back as plain text (res.send("Bad Request"), "Curso não encontrado") while successes are JSON. DELETE answers 200 with a text message even when the user does not exist or the query failed.
Impact: Clients have to parse each route differently, and failures look like successes.
Recommendation: Use one JSON error shape from the error handler, and keep the existing success payloads (playbook T-12).

### [LOW] Magic numbers and magic strings (AP-19)
File: src/AppManager.js:21, 46, 48, 68, 108, src/utils.js:19, 22
Description: The status literals 'PAID' and 'DENIED' are repeated. The card approval rule is startsWith("4"). The loop count 10000, substring(0, 10) and the default "123456" are bare literals.
Impact: Their meaning is invisible, and the status strings can drift apart between files.
Recommendation: Use named constants (PAYMENT_STATUS) in one module (playbook T-14).

### [LOW] Poor naming (AP-20)
File: src/AppManager.js:4, 29-33, 89, 102, src/utils.js:17
Description: The code uses cryptic variables (u, e, p, cid, cc, c, enr), the vague names AppManager and utils, and the misleading badCrypto. The abbreviated request fields usr/eml/pwd/c_id leak into the logic.
Impact: Every reader is slowed down and the intent is hidden.
Recommendation: Give things descriptive names and map the request fields once in the controller, keeping the public field names (playbook T-14).

### [LOW] Print-style logging (AP-21)
File: src/AppManager.js:45, src/utils.js:13, src/app.js:13
Description: Operational messages go through console.log with no levels, and one of them contains card data.
Impact: Output is noisy, there is no level control, and data can leak.
Recommendation: Add a small logger module with levels and no sensitive data (playbook T-14).

### [LOW] Dead code and unused imports (AP-22)
File: src/AppManager.js:2, src/utils.js:2-3, 5, 9-10, 25
Description: totalRevenue is imported in AppManager but never used. globalCache is exported but never imported. The config keys dbUser, dbPass and smtpUser are never read.
Impact: These names add noise, suggest reuse that does not exist, and keep secrets sitting in the code for nothing.
Recommendation: Remove the unused symbols and config keys (playbook T-14).

================================
Total: 18 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
