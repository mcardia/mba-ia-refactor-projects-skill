# MVC architecture guidelines (Phase 3 target)

The target is Model-View-Controller adapted to a backend API: the **View** is the HTTP-facing layer
(routes plus response shaping). Names of folders follow the stack's conventions; **roles** are what
matter.

## 1. Layers and responsibilities

| Layer | Owns | Must NOT contain |
|---|---|---|
| **Config** | One module that reads settings (env vars with safe defaults): secrets, ports, database location, debug flag, CORS origins, business constants. | Secrets as literals, logic, I/O |
| **Models** | Entities and persistence: queries (parameterized/ORM), mapping rows to domain objects/dicts, domain invariants and rules that belong to one entity (for example `is_overdue`, price rules, status validity). | HTTP objects (request/response), status codes, template/JSON envelopes |
| **Views / Routes** | URL + HTTP method -> controller function mapping; request/response shaping (serialization, envelopes); route grouping (blueprints/routers). | Business rules, SQL/ORM calls, validation chains |
| **Controllers** | Application flow per use case: read input, validate, call models/services, translate the result or a domain error into the HTTP response. | SQL, schema knowledge, long calculations, global state |
| **Services** *(optional)* | Orchestration across several models, or an external side effect (payment gateway, e-mail/notification, report assembly). Called by controllers. | HTTP concerns |
| **Middleware / error handling** | One centralized error handler, domain exceptions, auth guards, request logging. | Per-route try/except copies |
| **Entry point (composition root)** | Create the app, load config, initialize the database, register middleware and routes, wire dependencies, start the server. | Handlers, queries, business rules |

Add a **Services** layer only when a use case spans several models or has external side effects.
Do not create empty layers or one-line pass-through classes.

## 2. Dependency direction

```
Entry point -> Views/Routes -> Controllers -> (Services) -> Models -> Database
                    Config is read by the entry point and injected downward
```

- A layer may call only the layer on its right. Never the reverse, never skipping from Views to
  Models for logic.
- No import cycles. No layer imports the entry point.
- Collaborators (database handle, gateway client, config) are passed in (constructor, factory
  argument, application context), not created inside business code.
- Cross-cutting pieces (error classes, logger, constants) live in a neutral module that every layer
  may import.

## 3. Target layout by stack

Keep the original entry-point path so the documented run command still works.

### Python / Flask (application factory)

```
<project>/
├── app.py                    # entry point: create_app() + run (python app.py keeps working)
├── config/settings.py        # Settings read from environment
├── database/                 # connection per request, schema init, seed
│   └── connection.py
├── models/                   # one file per entity (+ __init__.py)
├── services/                 # only where needed (orders, notifications, reports)
├── controllers/              # one file per resource
├── views/                    # route registration (Blueprints) + serializers
│   └── routes.py
├── middlewares/error_handler.py
└── utils/                    # small, used helpers only
```

### Node.js / Express

```
<project>/
├── src/
│   ├── app.js                # entry point: composition root, listens (npm start keeps working)
│   ├── config/index.js       # settings from process.env
│   ├── database/connection.js# connection, schema, seed, promisified helpers, transaction helper
│   ├── models/               # one file per entity
│   ├── services/             # payment, purchase orchestration, reports
│   ├── controllers/          # one file per resource
│   ├── routes/               # express.Router per resource, mounted in app.js
│   └── middlewares/          # error handler, async wrapper, auth guard
└── package.json              # scripts.start unchanged
```

### Other stacks

Map the same roles onto the stack's idioms: Spring Boot (`@RestController` = controller, `@Service`,
`@Repository`/entity = model, `@ControllerAdvice` = error handling, `@ConfigurationProperties` =
config); Django (`urls.py` = views/routes, `views.py` = controllers, `models.py`, `middleware.py`,
`settings.py` from env); Laravel, Rails, ASP.NET likewise. Do not impose a foreign folder scheme on a
framework that already prescribes one.

## 4. Adapting to what already exists

Run the target against the layers found in Phase 1:

| Situation | Action |
|---|---|
| Monolith (one or few files) | Create all layers; split by responsibility, then by resource/entity. |
| God class | Split the class by responsibility (schema, routes, use cases, reports); the class disappears. |
| Already has `models/ routes/ services/ utils/` | Keep correct folders and names. Add what is missing (typically `controllers/`, `config/`, `middlewares/`). Slim routes to routing only. Move logic from routes to controllers/services/models. Wire or delete unused services/helpers. |
| Layers exist but are polluted | Fix the pollution (queries in routes, rules in controllers) instead of renaming files. |

Rule of thumb: the diff should be as small as the target allows. Do not move or rename a file that
already satisfies its role.

## 5. Behavior-preservation contract

Refactoring must not change what clients observe.

**Must stay identical**: route paths and methods; status codes for success and for each existing
failure; success payload shape (keys, nesting, value types); headers that matter (content type);
run command and default port; seed data and credentials needed to try the app.

**Allowed, and always listed under "Behavior changes"** (each one removes a flaw from the audit):

1. Secrets, password hashes and card data removed from responses and logs.
2. Privileged/destructive endpoints now require the admin guard (they still respond: 401/403).
   Guard only the routes the audit lists under AP-04 (destructive operations, raw SQL, role
   changes). Routes that were open reads or ordinary writes stay open; report that as residual
   risk. Never introduce login enforcement, Bearer authentication, sessions or per-user ownership
   checks: that builds an auth system, which is out of scope and breaks the contract.
3. Password storage moves to a salted hash; seed users keep working with the same plaintext
   credentials.
4. Issued tokens become signed instead of guessable.
5. Error bodies no longer expose internal messages; they are normalized to one JSON envelope while
   keeping the project's existing key name (`erro`, `error`, ...) and message text.
6. Safer defaults: debug off, loopback bind, CORS limited to configured origins, all configurable
   through the environment.
7. Input that previously crashed with a 500, or was silently accepted and corrupted data, is now
   rejected: malformed bodies and wrong types return 400; references to missing records return 400
   or 404; deleting a record that other rows depend on returns 409; negative or zero quantities
   return 400. Only changes that fix a defect named in the audit qualify.

Anything else that differs from the baseline is a regression to fix, not a change to report.

## 6. Dependencies and tooling

- Prefer the standard library and packages already in the manifest (for example Werkzeug ships with
  Flask; Node has `crypto.scrypt`). Add a dependency only when unavoidable, and update the manifest.
- Keep the package manager and the run command. If new environment variables appear, document them
  in the project README and provide a `.env.example` with placeholder values (never real secrets).

## 7. Naming and style

- Files: follow the stack (`snake_case.py`, `camelCase.js` or `kebab-case.js` consistent with the
  project). One entity or resource per file.
- Functions named for intent (`create_order`, `findByEmail`); no abbreviations, no shadowed built-ins.
- Constants in the config or a constants module, not inline literals.
- Logging through the stack's logger with levels; no `print`/`console.log` for operational output.
- Keep the project's existing natural language for user-facing messages and domain words.

## 8. Done criteria for the structure

- [ ] Layers from section 1 exist wherever the project needs them; no empty ceremony.
- [ ] No SQL/ORM calls outside models (and the database module).
- [ ] No business rules in routes or controllers.
- [ ] Config module holds every setting; no secret literals remain.
- [ ] One centralized error handler; handlers do not repeat try/except.
- [ ] Single, clear entry point that only wires and starts.
- [ ] Original run command works; original routes respond.
