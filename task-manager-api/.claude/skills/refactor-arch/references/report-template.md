# Output templates

Print each phase with **exactly** this structure. Text between `<...>` is filled in; everything else
is literal. Use the banner width shown (32 `=` characters).

## Phase 1 - analysis summary

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <language and runtime version if known>
Framework:     <framework + version>
Dependencies:  <runtime dependencies from the manifest, comma separated>
Domain:        <one-line domain (main entities)>
Architecture:  <architecture label> - <one phrase of evidence>
Source files:  <N> files analyzed (~<LOC> lines of code)
DB tables:     <table names, or Not detected>
Entry point:   <file> (run: <command>)
Endpoints:     <count> routes inventoried
================================
```

## Phase 2 - architecture audit report

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <directory name>
Stack:   <language> + <framework>
Files:   <N> analyzed | ~<LOC> lines of code

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [CRITICAL] <Catalog name> (<AP-ID>)
File: <path>:<start>-<end>[, <path>:<line>, ...]
Description: <what the code does, factually>
Impact: <what can go wrong>
Recommendation: <the change to make> (playbook <T-ID>)

### [HIGH] <Catalog name> (<AP-ID>)
...

================================
Total: <N> findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

### Rules for filling the report

1. **Order**: all CRITICAL, then HIGH, MEDIUM, LOW. Inside a severity, order by catalog ID.
2. **One finding per root cause.** Repeated occurrences go into a single `File:` line listing every
   location, each with exact lines (`models.py:28, 48-49, 58-60`). A range is `start-end`; a single
   line is `line`.
3. **Line numbers are verified**, copied from a numbered read of the file. A range covers the code
   that exhibits the problem, not the whole file, unless the problem is the whole file (God module).
4. **Description is factual** (what the code does, with the offending value or construct quoted
   briefly), **Impact** is concrete (an attack, a failure, a maintenance cost), **Recommendation** is
   actionable and names the playbook transformation.
5. **Summary counts must equal the findings printed**, and `Total` is their sum.
6. **Deprecated APIs** are ordinary findings (catalog AP-17); name the obsolete call and its modern
   replacement in the Recommendation. If none exist, do not invent one.
7. The report ends with the confirmation line, and nothing is printed after it.

### Worked example of one finding

```
### [CRITICAL] SQL injection through dynamic query construction (AP-02)
File: repository.py:21-23, repository.py:40
Description: Queries are built by concatenating request values: "... WHERE email = '" + email + "'".
Impact: An attacker can read, alter or delete any table and bypass login with ' OR '1'='1.
Recommendation: Use bound parameters for every value (playbook T-02).
```

## Phase 3 - refactoring summary

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<tree of the project after refactoring, one line per file with a short role comment>

## Findings
Resolved:  <n> of <N>
Remaining: <list of AP-IDs with one-line reason, or None>

## Behavior changes
<one bullet per intentional change (what, why), or: None>

## Validation
  [x] Application boots without errors            (<command>)
  [x] <n>/<n> endpoints match the baseline         (<number of differences explained>)
  [x] MVC structure present                        (models, views/routes, controllers)
  [x] Configuration extracted, no hardcoded secrets
  [x] Centralized error handling
  [x] Anti-pattern re-scan                         (<remaining count> remaining)
================================
```

Use `[x]` only for checks that were executed and passed. Use `[ ]` followed by the reason for any
check that failed or could not be run. Never print "Zero anti-patterns remaining" unless the
re-scan found none.
