================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js) + Express 4
Files:   3 analyzed | ~180 lines of code

## Summary
CRITICAL: 4 | HIGH: 6 | MEDIUM: 4 | LOW: 4

## Findings

### [CRITICAL] Hardcoded credentials and secrets (AP-01)
File: src/utils.js:1-7
Description: A config object in the source code holds dbUser "admin_master", dbPass "senha_super_secreta_prod_123", paymentGatewayKey "pk_live_1234567890abcdef", smtpUser and the port. It is exported from a utils module.
Impact: Anyone who can read the repo gets production DB and payment gateway credentials. Rotating them means changing code.
Recommendation: Move the values to environment variables read by a config module, with no secret defaults (playbook T-01).

### [CRITICAL] Insecure credential storage and exposure (AP-03)
File: src/utils.js:17-23, src/AppManager.js:68, src/AppManager.js:18, src/AppManager.js:45
Description: Passwords go through badCrypto, a home-made scheme: base64 of the password, truncated, repeated 10000 times and cut to 10 characters. A missing password silently falls back to "123456". The seed inserts a plaintext password '123'. The full card number and the gateway key are written to the console.
Impact: The hashes can be reversed trivially, since they are deterministic and unsalted base64 prefixes. Accounts get a known default password. Card numbers (PAN) and the live key end up in logs, which is a PCI violation.
Recommendation: Hash with crypto.scrypt plus a random salt, require a password instead of defaulting it, hash the seed password, and never log the PAN or the key (log a masked last-4 only) (playbook T-03).

### [CRITICAL] Unprotected privileged or destructive endpoints (AP-04)
File: src/AppManager.js:80, src/AppManager.js:131-137
Description: GET /api/admin/financial-report returns every student's name and payment. DELETE /api/users/:id deletes any user. Neither route has an authentication or authorization check, and the project has no auth middleware at all.
Impact: Any anonymous caller can read all financial and personal data and delete any account.
Recommendation: Add an admin-guard middleware (token from an environment variable) on the admin and destructive routes (playbook T-04).

### [CRITICAL] God class / God module (AP-05)
File: src/AppManager.js:4-139
Description: The AppManager class creates the DB connection (7), creates the schema (12-16), seeds data (18-21), registers every route (25-137) and holds the checkout workflow and the financial-report aggregation.
Impact: No part can be tested or changed on its own. Every feature edit touches the same class.
Recommendation: Split into config, database, models, services, controllers and routes modules (playbook T-05, plus T-06 and T-07).

### [HIGH] Business logic in the controller / route layer (AP-06)
File: src/AppManager.js:28-78, src/AppManager.js:89-127
Description: The checkout handler (51 lines) finds or creates the user, decides payment approval (cc.startsWith("4") -> PAID/DENIED), and writes the enrollment, payment, audit row and cache entry. The report handler adds up revenue and builds the per-course student lists.
Impact: The checkout and revenue rules can't be reused or unit-tested without an HTTP request.
Recommendation: Move them into CheckoutService and ReportService. Controllers only parse input and map results to responses (playbook T-06).

### [HIGH] Data access outside the model layer (AP-07)
File: src/AppManager.js:37, 40, 50, 54, 57, 69, 83, 92, 104, 106, 133
Description: Raw db.get/db.run/db.all SQL calls live directly inside the route handlers.
Impact: Persistence details leak into HTTP code, so any schema change ripples through the handlers.
Recommendation: Put every query in model modules (User, Course, Enrollment, Payment, AuditLog) (playbook T-05, T-06).

### [HIGH] Global mutable state (AP-08)
File: src/utils.js:9-10, src/utils.js:14, src/utils.js:25
Description: globalCache = {} and totalRevenue = 0 are module-level mutable values that get exported. logAndCache writes request-derived keys into globalCache on every checkout.
Impact: Hidden coupling between requests, unbounded memory growth, and tests that depend on run order.
Recommendation: Remove the unused globals and wrap the cache in an injected, encapsulated component (playbook T-07).

### [HIGH] Tight coupling and no dependency injection (AP-09)
File: src/AppManager.js:1-2, src/AppManager.js:7
Description: The constructor creates its own new sqlite3.Database(':memory:'), and the class imports config and helpers directly from utils.
Impact: The database or payment gateway can't be swapped for a fake in tests.
Recommendation: Create the connection in a database module and pass it into models and services through factories (playbook T-07).

### [HIGH] Non-atomic multi-step writes and missing referential integrity (AP-10)
File: src/AppManager.js:50-61, src/AppManager.js:69-71, src/AppManager.js:133
Description: Checkout inserts the user, enrollment, payment and audit_log as separate statements with no transaction. If a later insert fails, the response is an error but the earlier rows remain. The DELETE removes the user and leaves its enrollments and payments behind as orphans; the response text itself admits this. No foreign keys are declared.
Impact: Partial checkouts (an enrollment without a payment) and orphaned financial records.
Recommendation: Wrap checkout in BEGIN/COMMIT/ROLLBACK. Delete the user's payments and enrollments in the same transaction as the user (playbook T-08).

### [HIGH] Callback hell / deeply nested asynchronous flow (AP-11)
File: src/AppManager.js:37-77, src/AppManager.js:83-128
Description: Checkout nests 5 levels of db callbacks. The report nests 4 levels inside forEach loops and uses manual counters (coursesPending, enrPending, 86, 93, 117-121) to know when to respond.
Impact: Hard to follow, and errors get lost. Easy to send zero or two responses.
Recommendation: Promisify the driver and rewrite as async/await (playbook T-09).

### [MEDIUM] N+1 queries (AP-13)
File: src/AppManager.js:83, 92, 104, 106
Description: The report runs 1 query for courses, then 1 per course for enrollments, then 2 per enrollment (user and payment).
Impact: The query count grows as 1 + C + 2E, so latency rises linearly with sales.
Recommendation: Use a single LEFT JOIN query across courses/enrollments/users/payments and group in memory (playbook T-10).

### [MEDIUM] Missing or weak input validation (AP-15)
File: src/AppManager.js:29-35, src/AppManager.js:132
Description: Checkout only checks that usr/eml/c_id/card are truthy: no type checks, no email format, no card format, and pwd is optional. cc.startsWith assumes card is a string, so a numeric card value throws a TypeError. The :id route parameter is not validated.
Impact: Malformed data is stored, and a non-string card crashes the handler with a 500.
Recommendation: Add a validation step that returns 400 with a clear message (playbook T-12).

### [MEDIUM] Fragmented or unsafe error handling (AP-16)
File: src/AppManager.js:57, 92-93, 104, 106, 133-135, src/app.js:5-10
Description: The err callback argument is ignored at 57, 92, 104, 106 and 133. At 92-93, a query error leaves enrollments undefined and enrollments.length throws inside the callback, which crashes the process. DELETE answers success even on a DB error. There is no global error middleware.
Impact: The process can crash, failures are silent, and the API returns false success responses.
Recommendation: Propagate errors with async/await to a centralized Express error middleware (playbook T-12).

### [MEDIUM] Inconsistent response contract (AP-18)
File: src/AppManager.js:35, 38, 41, 48, 51, 55, 70, 84, 135, src/AppManager.js:60, 87
Description: Errors and the DELETE success are plain-text res.send("..."), while checkout success and the report are JSON.
Impact: Clients have to parse each route differently, and errors have no machine-readable shape.
Recommendation: Use one response helper and error middleware. Keep success payloads unchanged (playbook T-12).

### [LOW] Magic numbers and magic strings (AP-19)
File: src/AppManager.js:46, 21, 108, src/utils.js:19-22, src/AppManager.js:68
Description: Literals with business meaning are scattered through the code: the card prefix "4", the statuses "PAID"/"DENIED" repeated across files, 10000 / substring(0, 2) / substring(0, 10) in the hash, and the "123456" default.
Impact: The intent is invisible, and changing a status means editing several places.
Recommendation: Define named constants (PAYMENT_STATUS, approval rule) in one module (playbook T-14).

### [LOW] Poor naming (AP-20)
File: src/AppManager.js:29-33, src/AppManager.js:4, src/utils.js:17, src/utils.js:1
Description: Variables are cryptic (u, e, p, cid, cc). Module and class names are vague (AppManager, utils), and badCrypto is named for its flaw. The abbreviated request fields (usr, eml, pwd, c_id) leak into the code.
Impact: Every reader slows down and the intent is hidden.
Recommendation: Map request fields to descriptive names at the controller boundary and give modules role-based names (playbook T-14).

### [LOW] Print-style logging (AP-21)
File: src/app.js:13, src/AppManager.js:45, src/utils.js:13
Description: Operational messages go through console.log, including one line that leaks the card number and key.
Impact: No log levels, noise in output, and data leakage.
Recommendation: Add a small logger module with levels and never log sensitive data (playbook T-14).

### [LOW] Dead code and unused imports (AP-22)
File: src/AppManager.js:2, src/utils.js:2-3, 5, 10, 25
Description: totalRevenue is imported but never used. config.dbUser, dbPass and smtpUser are never read; there is no DB authentication and no SMTP. totalRevenue and globalCache are exported but nothing reads them.
Impact: Noise, a misleading sense of features, and secrets kept around for nothing.
Recommendation: Remove the unused symbols and config keys (playbook T-14).

================================
Total: 18 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
