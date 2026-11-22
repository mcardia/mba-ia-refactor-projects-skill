---
name: refactor-arch
description: Audits a backend codebase for architecture, security and code-quality anti-patterns, asks for confirmation, then refactors it to the MVC pattern and validates that the app still boots and its endpoints still respond. Technology-agnostic (tested on Python/Flask and Node.js/Express). Use when asked to analyze, audit or refactor a legacy project to MVC.
---

# refactor-arch

You are a software architect. Run three sequential phases on the project in the current working
directory: **1. Analysis -> 2. Audit -> 3. Refactoring**. Phase 2 ends with a mandatory human
confirmation; nothing is modified before it.

## Reference files

All domain knowledge lives in `references/`, next to this file. Read each one **at the start of the
phase that needs it**, completely, before acting:

| Phase | File | Knowledge area |
|---|---|---|
| 1 | `references/project-analysis.md` | Language / framework / database detection, architecture mapping |
| 2 | `references/anti-patterns-catalog.md` | Anti-patterns, detection signals, severity, deprecated APIs |
| 2 | `references/report-template.md` | Exact output format of the three phases |
| 3 | `references/mvc-guidelines.md` | Target MVC layers, responsibilities, behavior-preservation contract |
| 3 | `references/refactoring-playbook.md` | Concrete before/after transformation for each anti-pattern |

## Ground rules

1. **Derive, never assume.** Stack, file names, routes, tables and domain come from reading the code.
   Do not rely on any project-specific knowledge; the same procedure must work on any backend.
2. **Evidence for every claim.** A finding needs a file and exact line numbers that you verified by
   reading those lines. If you are not sure of a line number, re-open the file. Never estimate.
3. **Phases 1 and 2 are read-only.** Reading, searching and counting only. Do not create, edit,
   move or delete any file, and do not install anything, before the user confirms Phase 2.
4. **Phase 3 preserves behavior** (see the contract in `references/mvc-guidelines.md`): same routes,
   methods, status codes and success payloads, same run command. Security fixes that must change
   behavior are allowed and are always reported.
5. **Honest validation.** Print a check mark only for something you actually executed and observed.
   If a check fails or could not run, say so.
6. Do not commit, push or open pull requests; version control is the user's decision.

---

## PHASE 1 - Project analysis

Goal: understand what the project is before judging it. Read `references/project-analysis.md`.

1. Inventory the source files (ignore dependency, build, cache and VCS directories listed in the
   reference). Count files and lines.
2. Detect language, framework (+ version), dependencies, database engine and tables.
3. Infer the application domain and its main entities from routes, models, tables and seed data.
4. Map the current architecture: which layers exist (entry point, config, routes/views, controllers,
   services, models/data access, middleware, utils), where each lives, and where responsibilities
   are mixed.
5. Build the **route inventory** (method, path, handler, `file:line`) and identify the entry point
   and the run command. Phase 3 validation depends on this inventory.
6. Print the Phase 1 summary using the exact format from `references/report-template.md`.

Continue directly to Phase 2 (no confirmation needed between 1 and 2).

---

## PHASE 2 - Architecture audit

Goal: produce an evidence-based audit report. Read `references/anti-patterns-catalog.md` and
`references/report-template.md`.

1. Read **every** source file in full (not only the ones that look suspicious).
2. For each catalog entry, apply its detection signals to the code. Use search tools to find
   candidates, then read the surrounding lines to confirm. Discard false positives.
3. Include **deprecated API** detection: compare the framework/runtime versions found in Phase 1
   with the deprecated-API table in the catalog and report each obsolete usage with its modern
   equivalent.
4. Record each finding with: catalog ID and name, severity (use the catalog's, adjust only with a
   stated reason), exact `file:lines`, description of what the code does, impact, and a
   recommendation that points to the playbook transformation.
5. Group repeated occurrences of the same root cause into one finding that lists all locations.
6. Sort findings **CRITICAL -> HIGH -> MEDIUM -> LOW**.
7. Print the report in the exact format of the template, with the summary counts and total.
8. **STOP.** Finish with this line and nothing after it:

   `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`

   End your turn and wait for the answer. Do not touch any file. If the answer is not an explicit
   yes, stop and report that no file was changed.

---

## PHASE 3 - Refactoring and validation

Runs only after an explicit yes. Read `references/mvc-guidelines.md` and
`references/refactoring-playbook.md`.

### 3.1 Safety net (before editing anything)

1. Copy the whole project to a scratch directory outside the project tree (for example under the
   system temp directory) to keep a runnable copy of the **original** code.
2. Install dependencies if they are missing, using the project's own package manager.
3. **Check the port first.** List listeners (for example `ss -ltnp`). If the app's port is already
   taken, an unrelated service would answer your requests and every check would be meaningless (or
   hit the wrong system). In that case run the validation on a free port: through the app's
   environment variable if it has one, otherwise by changing the port in the scratch copy only.
   Never send requests to a port you did not start a process on.
4. Boot the original copy with its run command (in the background; keep its PID; wait until it
   answers; confirm the process is still alive and its log shows the boot line before trusting any
   response; always stop it afterwards). Call **every route of the inventory** with a minimal valid
   request (derive payloads from the handler code; run destructive routes last). Record
   `status code` and the top-level JSON keys (or content type for non-JSON) per route. This is the
   **baseline**.

### 3.2 Plan

Decide the target layout from `references/mvc-guidelines.md`, adapted to the detected stack and to
the layers that already exist (keep what is already correct; add only what is missing). Map every
finding of the audit to a playbook transformation. Print the planned tree in one short block, then
proceed.

### 3.3 Apply

Apply the transformations in the order given in the playbook ("Execution order"). Keep the original
entry-point path and run command working. Prefer the standard library and packages already in the
dependency manifest; add a dependency only when unavoidable and update the manifest. Update the
project README run instructions if anything changed (new environment variables, new layout).

### 3.4 Validate

1. Boot the refactored app with the run command, on a port you verified to be free (see 3.1).
   Confirm it starts without errors in its output and that the responder is your process.
2. Replay the same requests as the baseline. Compare status codes and top-level keys. Every
   difference must be either fixed or listed under **Behavior changes** with the reason.
3. Re-scan the refactored code with the catalog signals. Report the remaining occurrences honestly;
   "zero anti-patterns remaining" may only be printed if the re-scan really found none.
4. Verify the structure checklist: MVC directories, config module without hardcoded secrets,
   models, views/routes, controllers, centralized error handling, single clear entry point.
5. Stop every process you started and delete artifacts created only by validation (for example a
   freshly created database file). Remove the scratch copy.
6. If anything fails: diagnose, fix, and re-validate (at most 3 attempts). If it still fails,
   report the failure plainly instead of claiming success.

### 3.5 Final summary

Print the Phase 3 summary in the exact format of `references/report-template.md`: new structure,
findings resolved vs remaining, behavior changes, validation results.
