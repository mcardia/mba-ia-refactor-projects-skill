# Refactoring playbook (Phase 3)

14 transformations. Each one states the anti-patterns it removes, the steps, and a before/after
example. Examples use neutral names and Python or JavaScript; apply the **same idea** idiomatically
in the project's stack and keep the project's own names, keys and messages.

General rules for every transformation:

- Change one concern at a time; keep the app runnable between steps.
- Keep route paths, methods, status codes and success payloads (contract in `mvc-guidelines.md`).
- Search the whole project for every use of a symbol before moving, renaming or deleting it.

## Execution order

1. T-01 config -> 2. T-13 deprecated APIs and T-14 constants/logging (small, mechanical)
3. T-02 queries, T-03 credentials, T-08 transactions, T-10 N+1 (inside the model/data layer)
4. T-05 split into layers, T-07 state and injection, T-11 duplication
5. T-06 logic out of controllers, T-09 async flow
6. T-12 validation and error handling, T-04 admin guard
7. Entry point wiring, dead-code cleanup (T-14), README/manifest updates, validation.

## Finding -> transformation

| Anti-pattern | Transformation |
|---|---|
| AP-01 hardcoded secrets | T-01 |
| AP-02 SQL injection | T-02 |
| AP-03 insecure credentials | T-03 |
| AP-04 unprotected endpoints | T-04 |
| AP-05 God class/module | T-05 (+ T-06, T-07) |
| AP-06 logic in controllers | T-06 |
| AP-07 data access outside models | T-05, T-06 |
| AP-08 global state, AP-09 coupling | T-07 |
| AP-10 non-atomic writes/integrity | T-08 |
| AP-11 callback hell | T-09 |
| AP-12 insecure runtime config | T-01, T-12 |
| AP-13 N+1 | T-10 |
| AP-14 duplication | T-11 |
| AP-15 validation, AP-16 errors, AP-18 contract | T-12 |
| AP-17 deprecated APIs | T-13 |
| AP-19 magic values, AP-20 naming, AP-21 logging, AP-22 dead code | T-14 |

---

## T-01 Extract configuration to a config module
**Fixes**: AP-01, AP-12 (and AP-19 for settings).
**Steps**: list every secret, port, URI, flag and host literal; create one config module reading
environment variables; give development-safe defaults that are **not** real secrets; update every
consumer; add `.env.example` (placeholders) and document variables in the project README.

Before (Python):
```python
app.config["SECRET_KEY"] = "my-hardcoded-secret"
app.config["DEBUG"] = True
app.run(host="0.0.0.0", port=5000, debug=True)
```
After:
```python
# config/settings.py
import os
import secrets

class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)  # random per boot if unset
    DEBUG = os.environ.get("APP_DEBUG", "0") == "1"
    HOST = os.environ.get("APP_HOST", "127.0.0.1")
    PORT = int(os.environ.get("APP_PORT", "5000"))
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "app.db")
    ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")      # empty => admin endpoints disabled
```
Before (Node):
```js
const config = { dbPass: "super-secret", paymentGatewayKey: "pk_live_123", port: 3000 };
```
After:
```js
// src/config/index.js
module.exports = {
  port: Number(process.env.PORT) || 3000,
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
  adminToken: process.env.ADMIN_TOKEN || '',
};
```
Unused credentials (never read anywhere) are deleted, not moved.

## T-02 Parameterize every query
**Fixes**: AP-02.
**Steps**: find every query built from variables; replace values with bound parameters; for `LIKE`
bind the pattern (`%term%`) as the parameter; identifiers (table/column/order-by) cannot be bound:
choose them from a fixed whitelist; build optional filters by appending clauses and parameters in
parallel.

Before:
```python
cur.execute("SELECT * FROM users WHERE email = '" + email + "' AND pwd = '" + pwd + "'")
cur.execute("SELECT * FROM items WHERE name LIKE '%" + term + "%'")
```
After:
```python
cur.execute("SELECT * FROM users WHERE email = ?", (email,))
cur.execute("SELECT * FROM items WHERE name LIKE ?", (f"%{term}%",))

clauses, params = ["1=1"], []
if category:
    clauses.append("category = ?"); params.append(category)
if price_min is not None:
    clauses.append("price >= ?"); params.append(price_min)
rows = conn.execute("SELECT * FROM items WHERE " + " AND ".join(clauses), params).fetchall()
```
Node: `db.get("SELECT * FROM users WHERE email = ?", [email], cb)`. ORMs: use the query API; never
interpolate into `text()`/`raw()`.

## T-03 Secure credential handling
**Fixes**: AP-03.
**Steps**: hash passwords with a salted, slow hash from the stack's standard tooling; verify with the
library's constant-time check; remove password/hash fields from every serializer and response;
remove secrets and card data from logs and from health/debug payloads; hash seed passwords; replace
guessable tokens with signed ones; remove default-password fallbacks. Keep the existing column and
keep seed credentials usable. If a database with legacy plaintext/weak values may already exist,
verify the legacy format once and re-hash on successful login.

Before (Python):
```python
user.password = hashlib.md5(pwd.encode()).hexdigest()
return {"id": u.id, "email": u.email, "password": u.password}
token = "fake-jwt-token-" + str(u.id)
```
After:
```python
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer

user.password = generate_password_hash(pwd)
ok = check_password_hash(user.password, candidate)
def serialize_user(u):                       # no password field, ever
    return {"id": u.id, "email": u.email, "role": u.role}
token = URLSafeTimedSerializer(Settings.SECRET_KEY).dumps({"uid": u.id})
```
Before (Node):
```js
function weakHash(pwd) { /* base64 loop truncated to 10 chars */ }
console.log(`Charging card ${card} with key ${config.paymentGatewayKey}`);
```
After:
```js
const crypto = require('crypto');
const hashPassword = (pwd) => {
  const salt = crypto.randomBytes(16);
  return `${salt.toString('hex')}:${crypto.scryptSync(pwd, salt, 64).toString('hex')}`;
};
const verifyPassword = (pwd, stored) => {
  const [salt, hash] = String(stored).split(':');
  if (!salt || !hash) return false;
  const candidate = crypto.scryptSync(pwd, Buffer.from(salt, 'hex'), 64);
  return crypto.timingSafeEqual(candidate, Buffer.from(hash, 'hex'));
};
logger.info('Processing payment', { cardLast4: card.slice(-4) });   // never the full number
```

## T-04 Protect privileged and destructive endpoints
**Fixes**: AP-04.
**Scope**: guard only the routes the audit names under AP-04. A route that was an open read or an
ordinary write stays open (reported as residual risk). Pick the guard by what the project has:
if it already has a login that issues a token, use the **session variant** at the end of this
section (validate the token, require the user's role); if it has no login, use the admin-token
header guard below.
**Steps**: list admin/destructive/privileged routes; put a guard in front of each (middleware or
decorator) that checks an admin token from configuration; if the token is not configured the
endpoint is disabled (403). Never let a client set its own `role`. An endpoint that runs
client-supplied SQL is removed unless the contract must be preserved: then keep it behind the guard
**and** an explicit opt-in flag, limited to one read-only statement. If the project has no
authentication system at all, add only this minimal guard and report the missing auth system as a
residual risk; do not invent a full auth framework.

Before:
```python
@app.route("/admin/query", methods=["POST"])
def run_query():
    cursor.execute(request.get_json()["sql"])
```
After:
```python
import hmac
from functools import wraps

def require_admin(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        expected = Settings.ADMIN_TOKEN
        if not expected:
            raise ForbiddenError("Endpoint disabled")
        supplied = request.headers.get("X-Admin-Token", "")
        if not hmac.compare_digest(supplied, expected):
            raise UnauthorizedError("Admin token required")
        return view(*args, **kwargs)
    return wrapper

@views.route("/admin/query", methods=["POST"])
@require_admin
def run_query():
    return admin_controller.run_readonly_query()
```
Node:
```js
const crypto = require('crypto');
module.exports = (config) => (req, res, next) => {
  if (!config.adminToken) return next(new HttpError(403, 'Endpoint disabled'));
  const supplied = Buffer.from(req.get('X-Admin-Token') || '');
  const expected = Buffer.from(config.adminToken);
  if (supplied.length !== expected.length || !crypto.timingSafeEqual(supplied, expected))
    return next(new HttpError(401, 'Admin token required'));
  next();
};
```

### T-04, session variant: the project already has a login
Use this when the project exposes a login that issues a token (after T-03 the token is signed and
expires). The guard must check **both** the session and the role; a fixed shared header is not
enough here because it never looks at who is calling.

Steps: (1) issue the token at login with the same signer the guard verifies, with an expiry
(configurable); (2) the guard reads `Authorization: Bearer <token>`, verifies signature and expiry,
reloads the user from the database, rejects missing, invalid, expired or inactive users with 401,
and rejects a valid user without the required role with 403; (3) the role and the active flag come
from the database, never from the token payload or the request; (4) apply the guard only to the
AP-04 routes, plus every operation that creates or promotes a user to a privileged role (creating a
user with the default role stays anonymous); (5) keep the seed's admin user able to log in so the
guarded routes can be exercised; (6) report the routes that stayed open as residual risk.

```python
# middlewares/auth.py
from functools import wraps
from flask import current_app, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

def _signer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])

def issue_token(user):                       # called by the login controller
    return _signer().dumps({"uid": user.id})

def current_user():
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        raise UnauthorizedError("Authentication token required")
    try:
        claims = _signer().loads(header[len("Bearer "):],
                                 max_age=current_app.config["TOKEN_MAX_AGE_SECONDS"])
    except (BadSignature, SignatureExpired):
        raise UnauthorizedError("Invalid or expired token")
    user = User.get_by_id(claims["uid"])     # role and active flag come from the database
    if user is None or not user.active:
        raise UnauthorizedError("Invalid or expired token")
    return user

def require_role(role):
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            if current_user().role != role:
                raise ForbiddenError("Role required: " + role)
            return view(*args, **kwargs)
        return wrapper
    return decorator

# routes: @require_role("admin") on the AP-04 routes only
```
Node, same idea (the token service is injected; it checks signature and expiry):
```js
module.exports = ({ tokenService, userModel }) => (role) => async (req, res, next) => {
  const [scheme, token] = (req.get('Authorization') || '').split(' ');
  if (scheme !== 'Bearer' || !token) return next(new HttpError(401, 'Authentication token required'));
  const claims = tokenService.verify(token);
  const user = claims && await userModel.findById(claims.uid);
  if (!user || !user.active) return next(new HttpError(401, 'Invalid or expired token'));
  if (user.role !== role) return next(new HttpError(403, 'Role required: ' + role));
  req.user = user;
  next();
};
```

## T-05 Split a God class / God module into layers
**Fixes**: AP-05, AP-07.
**Steps**: (1) list each function/method and tag its responsibility: schema/seed, routing, request
handling, business rule, data access, side effect, formatting; (2) create the layer files from the
layout in `mvc-guidelines.md`; (3) move code by tag, one resource or entity per file; (4) leave the
entry point only wiring; (5) delete the old file once nothing imports it.

Before: one class does everything.
```js
class GodManager {
  constructor() { this.db = new sqlite3.Database(':memory:'); }
  initSchema() { /* tables + seed */ }
  registerRoutes(app) { /* purchase logic, report logic, delete logic, all with SQL */ }
}
```
After:
```
src/
├── app.js                       # wiring only
├── config/index.js
├── database/connection.js       # schema + seed + helpers      (was initSchema)
├── models/{user,item,order,payment}.js                  (SQL moved here)
├── services/{purchaseService,paymentGateway,reportService}.js  (use cases)
├── controllers/{purchaseController,adminController,userController}.js
├── routes/{purchaseRoutes,adminRoutes,userRoutes}.js
└── middlewares/{errorHandler,requireAdmin}.js
```
Composition root:
```js
async function main() {
  const db = await createDatabase(config);
  const models = buildModels(db);
  const services = buildServices({ models, config, db });
  const app = express();
  app.use(express.json());
  app.use(buildRoutes(buildControllers({ services, models })));
  app.use(errorHandler);
  app.listen(config.port);
}
```
Flask equivalent: `app.py` keeps `create_app()` and `app.run`; `models/`, `controllers/`,
`views/routes.py`, `middlewares/error_handler.py`, `config/settings.py`, `database/connection.py`.

## T-06 Move business logic out of controllers/routes
**Fixes**: AP-06, AP-07.
**Steps**: leave in the controller only: read input, validate, call, map result to HTTP. Move rules
that concern one entity into the model; flows across entities or with side effects into a service.
Side effects (email, payment) go to a service that is injected and logged properly.

Before:
```python
@app.route("/orders", methods=["POST"])
def create_order():
    data = request.get_json()
    total = 0
    for it in data["items"]:
        p = db.execute("SELECT * FROM products WHERE id = " + str(it["product_id"])).fetchone()
        total += p["price"] * it["qty"]
    if total > 1000:
        total = total * 0.9                       # discount rule
    db.execute("INSERT INTO orders ...")
    print("SENDING EMAIL ...")                    # side effect
    return jsonify({"total": total}), 201
```
After:
```python
# controllers/order_controller.py
def create_order():
    payload = parse_order_payload(request.get_json())      # validation (T-12)
    result = order_service.place_order(payload["user_id"], payload["items"])
    return jsonify({"data": result, "success": True}), 201

# services/order_service.py
def place_order(user_id, items):
    total = pricing.apply_volume_discount(order_model.price_items(items))
    order_id = order_model.create(user_id, items, total)   # atomic, see T-08
    notification_service.order_created(order_id, user_id)
    return {"order_id": order_id, "total": total}
```
Before (Node): the route handler checks the card, creates the user, creates an order, inserts the payment and
logs. After: `purchaseController.handle` validates and delegates to
`purchaseService.purchase({user, email, password, itemId, card})`, which calls models and the
payment gateway module.

## T-07 Replace global state and hard-wired dependencies
**Fixes**: AP-08, AP-09.
**Steps**: for each module-level mutable, decide: delete (unused), make request-scoped (database
connection), or make an instance created once in the composition root and **passed in** (cache,
gateway client). Constructors/factories receive their collaborators.

Before (Python):
```python
db_connection = None
def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect("app.db", check_same_thread=False)
    return db_connection
```
After:
```python
# database/connection.py
import sqlite3
from flask import g
from config.settings import Settings

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(Settings.DATABASE_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(_exc=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()

# in create_app(): app.teardown_appcontext(close_db)
```
Before (Node):
```js
let sharedCache = {};
function cacheValue(key, data) { sharedCache[key] = data; }
class GodManager { constructor() { this.db = new sqlite3.Database(':memory:'); } }
```
After:
```js
class PurchaseService {
  constructor({ userModel, orderModel, paymentGateway, cache, logger }) { Object.assign(this, {
    userModel, orderModel, paymentGateway, cache, logger }); }
}
// app.js (composition root): new PurchaseService({ userModel, ..., cache: new Map() })
```
If a "cache" is written and never read, delete it.

## T-08 Atomic writes and referential integrity
**Fixes**: AP-10.
**Steps**: wrap every multi-statement write in one transaction with rollback on any failure; replace
check-then-act with a conditional update and check the affected row count; enforce or emulate
foreign keys and cascade deletes inside the same transaction.

Before:
```python
for it in items:                                   # check
    if stock(it) < it["qty"]: return {"error": "..."}
cur.execute("INSERT INTO orders ...")              # act, later, with no rollback
for it in items:
    cur.execute("UPDATE products SET stock = stock - " + str(it["qty"]) + " ...")
db.commit()
```
After:
```python
def create(conn, user_id, items, total):
    with conn:                                     # commit on success, rollback on exception
        order_id = conn.execute(
            "INSERT INTO orders (user_id, status, total) VALUES (?, 'pending', ?)",
            (user_id, total)).lastrowid
        for it in items:
            cur = conn.execute(
                "UPDATE products SET stock = stock - ? WHERE id = ? AND stock >= ?",
                (it["qty"], it["product_id"], it["qty"]))
            if cur.rowcount == 0:
                raise InsufficientStockError(it["product_id"])   # rolls everything back
            conn.execute("INSERT INTO order_items (order_id, product_id, qty, unit_price) "
                         "SELECT ?, id, ?, price FROM products WHERE id = ?",
                         (order_id, it["qty"], it["product_id"]))
        return order_id
```
Node (single connection, so serialize transactions):
```js
let queue = Promise.resolve();
function inTransaction(db, work) {
  const run = queue.then(async () => {
    await dbRun(db, 'BEGIN');
    try { const out = await work(); await dbRun(db, 'COMMIT'); return out; }
    catch (err) { await dbRun(db, 'ROLLBACK'); throw err; }
  });
  queue = run.catch(() => {});
  return run;
}
```
Deleting a parent: delete or detach its children in the same transaction (ORM:
`relationship(..., cascade="all, delete-orphan")`; SQL: `ON DELETE CASCADE` with
`PRAGMA foreign_keys = ON`).

## T-09 Flatten callback hell
**Fixes**: AP-11.
**Steps**: wrap the driver once in promise-returning helpers (`util.promisify` or a tiny wrapper);
rewrite flows with `async/await`; collect results with `Promise.all` instead of counters; let errors
propagate to the centralized handler through an async wrapper (Express 4 does not catch rejected
promises by itself).

Before:
```js
db.get(sqlItem, [cid], (err, item) => {
  db.get(sqlUser, [email], (err, user) => {
    db.run(sqlOrder, [uid, cid], function (err) {
      db.run(sqlPay, [this.lastID, price, 'PAID'], (err) => res.json({ ok: true }));
    });
  });
});
```
After:
```js
// database/connection.js
const run = (db, sql, p = []) => new Promise((ok, ko) =>
  db.run(sql, p, function (err) { err ? ko(err) : ok({ lastID: this.lastID, changes: this.changes }); }));
const get = (db, sql, p = []) => new Promise((ok, ko) => db.get(sql, p, (e, r) => e ? ko(e) : ok(r)));
const all = (db, sql, p = []) => new Promise((ok, ko) => db.all(sql, p, (e, r) => e ? ko(e) : ok(r)));

// middlewares/asyncHandler.js
module.exports = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);

// service
async function purchase(input) {
  const item = await itemModel.findAvailable(input.itemId);
  if (!item) throw new HttpError(404, 'Item not found');
  const user = (await userModel.findByEmail(input.email)) || (await userModel.create(input));
  return inTransaction(db, async () => {
    const order = await orderModel.create(user.id, item.id);
    await paymentModel.create(order.id, item.price, 'PAID');
    return order;
  });
}
```

## T-10 Remove N+1 queries
**Fixes**: AP-13.
**Steps**: find queries inside loops and lazy relationship reads in loops; fetch everything the
response needs in one joined query (or eager-load), group in memory; collapse several `COUNT`s into
one aggregate with `GROUP BY` / conditional sums.

Before:
```python
for order in orders:
    items = conn.execute("SELECT * FROM order_items WHERE order_id = " + str(order["id"])).fetchall()
    for it in items:
        name = conn.execute("SELECT name FROM products WHERE id = " + str(it["product_id"])).fetchone()
```
After:
```python
rows = conn.execute("""
    SELECT o.id AS order_id, o.status, o.total, i.product_id, i.qty, i.unit_price, p.name AS product_name
    FROM orders o
    LEFT JOIN order_items i ON i.order_id = o.id
    LEFT JOIN products p ON p.id = i.product_id
    ORDER BY o.id""").fetchall()
orders = {}
for r in rows:
    order = orders.setdefault(r["order_id"], {"id": r["order_id"], "status": r["status"],
                                              "total": r["total"], "items": []})
    if r["product_id"] is not None:
        order["items"].append({"product_id": r["product_id"], "name": r["product_name"],
                               "qty": r["qty"], "unit_price": r["unit_price"]})
result = list(orders.values())
```
SQLAlchemy: `select(Ticket).options(selectinload(Ticket.user), selectinload(Ticket.category))`; counts per
group: `select(Ticket.status, func.count()).group_by(Ticket.status)`.
Node report: one query
`SELECT i.id, i.title, u.name, y.amount, y.status FROM items i LEFT JOIN orders o ON o.item_id = i.id LEFT JOIN users u ON u.id = o.user_id LEFT JOIN payments y ON y.order_id = o.id ORDER BY i.id, o.id`,
then group by item.

## T-11 Extract duplicated logic
**Fixes**: AP-14.
**Steps**: pick the best existing copy (or the model method that already exists); put it in one
place (model method, serializer function, constants module); replace every copy; delete unused
duplicates.

Before:
```python
# repeated in 5 handlers
if t.due_date and t.due_date < datetime.utcnow() and t.status not in ("done", "cancelled"):
    data["overdue"] = True
else:
    data["overdue"] = False
```
After:
```python
# models/ticket.py (single source of truth)
def is_overdue(self):
    return bool(self.due_date and self.due_date < utc_now()
                and self.status not in (STATUS_DONE, STATUS_CANCELLED))

# views/serializers.py
def ticket_to_dict(ticket):
    data = ticket.to_dict()
    data["overdue"] = ticket.is_overdue()
    return data
```
Same for row-to-dict mapping (`product_to_dict(row)` used by every query), validation chains shared
by create and update, and regexes/lists defined once.

## T-12 Centralized validation and error handling
**Fixes**: AP-15, AP-16, AP-18, AP-12 (leaks).
**Steps**: define domain exceptions (`ValidationError` 400, `NotFoundError` 404, `UnauthorizedError`
401, `ForbiddenError` 403, `ConflictError` 409); validators raise them; controllers contain no
try/except for normal failures; register one handler that maps exceptions to the project's existing
error envelope and logs unexpected errors (client sees a generic message). Keep the original key
name and message text. Check types, ranges and existence of every input; a missing or malformed JSON
body is a 400, not a crash.

Before:
```python
def create_item():
    try:
        data = request.get_json()
        if data["price"] < 0:                      # TypeError if price is a string -> 500
            return jsonify({"error": "Invalid price"}), 400
        ...
    except Exception as e:
        return jsonify({"error": str(e)}), 500      # leaks internals
```
After:
```python
# middlewares/error_handler.py
from werkzeug.exceptions import HTTPException

class AppError(Exception):
    status = 500
class ValidationError(AppError): status = 400
class NotFoundError(AppError):   status = 404

def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({"error": str(err), "success": False}), err.status

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        if isinstance(err, HTTPException):
            return err
        app.logger.exception("Unhandled error")
        return jsonify({"error": "Internal server error", "success": False}), 500

# controllers/validators.py
def number_field(data, key, minimum=None):
    value = data.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError(f"{key} deve ser numérico")
    if minimum is not None and value < minimum:
        raise ValidationError(f"{key} não pode ser menor que {minimum}")
    return value
```
Node:
```js
class HttpError extends Error { constructor(status, message) { super(message); this.status = status; } }

module.exports = (err, req, res, next) => {            // 4 arguments: error middleware
  const status = err.status || 500;
  if (status >= 500) console.error(err);
  res.status(status).json({ error: status >= 500 ? 'Internal server error' : err.message });
};
```
Also register a 404 handler for unknown routes if the app returned 404 for them before.

## T-13 Modernize deprecated APIs
**Fixes**: AP-17.
**Steps**: for each finding replace the call with the equivalent from the catalog table; keep value
semantics identical (see the naive-UTC note); rerun the app to be sure no warning remains.

Before / After (Python, SQLAlchemy 2.x):
```python
ticket = Ticket.query.get(ticket_id)                       # legacy Query.get
created_at = db.Column(db.DateTime, default=datetime.utcnow)   # deprecated since Python 3.12
```
```python
# utils/time.py
from datetime import datetime, timezone
def utc_now():
    """Naive UTC datetime: the value utcnow() returned, without the deprecated call.
    Naive values keep comparisons valid against rows already stored without timezone."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

ticket = db.session.get(Ticket, ticket_id)
created_at = db.Column(db.DateTime, default=utc_now)
```
Node:
```js
const buf = new Buffer(str);          // Buffer() deprecated
app.use(bodyParser.json());           // standalone body-parser on Express >= 4.16
```
```js
const buf = Buffer.from(str);
app.use(express.json());
```

## T-14 Constants, naming, logging and dead code
**Fixes**: AP-19, AP-20, AP-21, AP-22.
**Steps**: replace business literals with named constants (config or a constants module) used in one
place; rename cryptic identifiers to intent-revealing names (update every reference); replace
`print`/`console.log` with a logger (levels, no sensitive data); delete unused imports, functions,
constants and manifest dependencies **after** proving by search that nothing references them.

Before:
```python
if revenue > 10000: discount = revenue * 0.1
elif revenue > 5000: discount = revenue * 0.05
print("SENDING EMAIL: order " + str(order_id))
```
After:
```python
# config/constants.py
DISCOUNT_TIERS = ((10000, 0.10), (5000, 0.05), (1000, 0.02))   # (threshold, rate)
ORDER_STATUSES = ("pending", "approved", "shipped", "delivered", "cancelled")

def volume_discount(revenue):
    return next((revenue * rate for threshold, rate in DISCOUNT_TIERS if revenue > threshold), 0)

import logging
logger = logging.getLogger(__name__)
logger.info("Order %s created for user %s", order_id, user_id)
```
Node: `const logger = require('./logger')` wrapping `console` with levels, or the project's logger.
Naming: `u, e, p, cc, pid` -> `name, email, password, cardNumber, productId`.
