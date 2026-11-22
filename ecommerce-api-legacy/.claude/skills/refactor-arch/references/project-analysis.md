# Project analysis heuristics (Phase 1)

Goal: describe the project accurately **from the code**, in a stack-neutral way. If a signal is not
found, write `Not detected`; never guess.

## 1. File inventory

Include source, templates, SQL, config and manifests. Exclude:

| Ignore | Reason |
|---|---|
| `node_modules/`, `venv/`, `.venv/`, `vendor/`, `target/`, `build/`, `dist/`, `.gradle/` | dependencies / build output |
| `.git/`, `.idea/`, `.vscode/`, `__pycache__/`, `*.pyc`, `.pytest_cache/` | tooling and caches |
| `package-lock.json`, `yarn.lock`, `poetry.lock`, `Pipfile.lock`, `go.sum` | lock files (read for versions only) |
| `*.db`, `*.sqlite*`, images, fonts, minified bundles | data / binaries |

"Source files analyzed" counts only files that contain application logic (code files). Report lines
of code with `wc -l` over exactly those files (rounded with `~`).

## 2. Language

Count source files per extension and confirm with the manifest. The dominant extension wins; report
secondary languages only if they contain logic.

| Manifest | Language / ecosystem | Source extensions |
|---|---|---|
| `requirements.txt`, `pyproject.toml`, `Pipfile`, `setup.py` | Python | `.py` |
| `package.json` (+ `tsconfig.json` => TypeScript) | JavaScript / TypeScript (Node.js) | `.js` `.mjs` `.cjs` `.ts` |
| `pom.xml`, `build.gradle(.kts)` | Java / Kotlin | `.java` `.kt` |
| `go.mod` | Go | `.go` |
| `composer.json` | PHP | `.php` |
| `Gemfile` | Ruby | `.rb` |
| `*.csproj`, `*.sln` | C# / .NET | `.cs` |
| `Cargo.toml` | Rust | `.rs` |

## 3. Framework and version

Find the framework by **dependency name first, import statements second**. Read the version from the
manifest (`==1.2.3`, `^4.18.2`, `<version>` tag) or from the lock file; if only a range exists, report
the range.

| Signal (dependency or import) | Framework |
|---|---|
| `flask`, `from flask import` | Flask (Flask-SQLAlchemy / Flask-CORS are extensions, list them as dependencies) |
| `fastapi`, `APIRouter` | FastAPI |
| `django`, `manage.py`, `settings.py`, `urls.py` | Django |
| `express`, `require('express')`, `from 'express'` | Express |
| `@nestjs/core` | NestJS |
| `fastify`, `koa`, `hapi` | Fastify / Koa / Hapi |
| `spring-boot-starter-web`, `@SpringBootApplication`, `@RestController` | Spring Boot |
| `gin-gonic/gin`, `labstack/echo`, `net/http` only | Gin / Echo / plain Go |
| `laravel/framework`, `artisan` | Laravel |
| `rails` | Ruby on Rails |
| `Microsoft.AspNetCore` | ASP.NET Core |

No web framework found => say so (CLI, library, worker) and adapt the route inventory to the actual
entry points.

## 4. Database

| Signal | Engine / access style |
|---|---|
| `sqlite3` (Python stdlib), `sqlite3` npm package, `*.db` path, `:memory:` | SQLite (note if in-memory) |
| `psycopg2`, `asyncpg`, `pg`, `postgresql://` | PostgreSQL |
| `mysql-connector`, `PyMySQL`, `mysql2`, `mysql://` | MySQL / MariaDB |
| `pymongo`, `mongoose`, `mongodb://` | MongoDB |
| `redis`, `ioredis` | Redis (cache/queue) |
| `SQLAlchemy`, `db.Model`, `Sequelize`, `TypeORM`, `Prisma`, `Hibernate`, `ActiveRecord` | ORM in use (name it) |
| Raw `cursor.execute(...)`, `db.run(...)`, `db.query(...)` | Raw SQL driver (no ORM) |

Tables/collections: collect them from `CREATE TABLE` statements, migrations, ORM model classes
(`__tablename__`, `@Entity`, `define(...)`) or schema files. List the names. Note where the
connection is created and whether it is shared globally.

## 5. Domain

Infer in one line from: route paths and names, table/model names, README, seed data, log messages.
Name the main entities in parentheses, for example `E-commerce API (products, orders, users)`.
Keep the language of the domain terms as they appear in the code.

## 6. Architecture mapping

Locate each layer by what the code **does**, not by what the file is called.

| Layer | What to look for |
|---|---|
| Entry point / bootstrap | file that creates the app and starts the server (`app.run`, `app.listen`, `main()`); whatever the README or `scripts.start` runs |
| Configuration | constants, `config` objects, env reads, `app.config[...]`, secrets, ports, URIs |
| Routes / Views | URL + method to handler mapping (`@app.route`, `Blueprint`, `app.get`, `router.post`, `add_url_rule`); response formatting |
| Controllers | functions that read the request, validate, call lower layers and choose the status code |
| Services | multi-step business flows, external side effects (email, payment, notification) |
| Models / data access | classes or functions that touch the database or ORM; entity definitions |
| Middleware / error handling | `errorhandler`, `app.use((err, ...)`, auth guards, request logging |
| Utils / helpers | stateless helpers, formatters, constants |

Classify the overall architecture with one label and one sentence of evidence:

| Label | Typical evidence |
|---|---|
| Monolithic single-file | one file holds routes, logic and SQL |
| Monolithic, flat modules | several files but no layering (each file mixes concerns) |
| God class | one class holds schema, routes, logic and reporting |
| Partially layered | folders such as `models/ routes/ services/ utils/` exist but responsibilities leak (routes with queries, services unused, helpers dead) |
| Layered MVC | clear dependency direction views -> controllers -> models |

For each layer record: present or absent, location, and contamination (for example "routes contain
ORM queries and business rules").

## 7. Route inventory (required for Phase 3 validation)

Produce a table `METHOD  path  handler  file:line`. Where to look:

| Stack | Where routes are declared |
|---|---|
| Flask | `@app.route`, `@bp.route`, `app.add_url_rule`, `register_blueprint(url_prefix=...)` |
| FastAPI | `@app.get/post/...`, `APIRouter(prefix=...)` |
| Django | `urlpatterns` entries |
| Express / Koa | `app.get/post/put/patch/delete`, `router.*`, `app.use('/prefix', router)` |
| Spring | `@GetMapping`, `@PostMapping`, `@RequestMapping` |

Resolve prefixes (blueprints, routers) so the path is the full public path. Note path parameters
and the type of body each route expects (read the handler).

## 8. Entry point and run command

In order of authority: README "how to run", `package.json` `scripts.start`, `Procfile`,
`Dockerfile` `CMD`, `if __name__ == "__main__"`. Record the exact command, the port, and any
prerequisite (seed script, env var, migration). Phase 3 must keep this command working.

## 9. Output of Phase 1

Use the format in `report-template.md`. `Dependencies` lists runtime dependencies from the
manifest, excluding the framework itself. `Architecture` is the label plus one clarifying phrase.
`DB tables` lists names, or `Not detected`.

## Pitfalls

- A folder named `controllers/` or `services/` does not prove the layer exists; check its contents.
- A framework version in `requirements.txt` may differ from what the code needs; report the manifest.
- In-memory databases and seed data inside code count as part of the data layer.
- Do not count generated files, lock files or `node_modules` as source.
