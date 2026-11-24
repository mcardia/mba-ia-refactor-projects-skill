#!/usr/bin/env python3
"""Check the session + role guard of task-manager-api against a running server.

usage: auth-check-p3.py <base_url>
Expects the seeded data (joao admin 1234, maria user abcd). Exits 1 if any check fails.
"""
import json
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1]
failures = []


def call(method, path, body=None, token=None):
    headers = {"Content-Type": "application/json"} if body is not None else {}
    if token:
        headers["Authorization"] = "Bearer " + token
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(BASE + path, data=data, method=method, headers=headers)
    try:
        response = urllib.request.urlopen(request, timeout=15)
        raw, status = response.read(), response.status
    except urllib.error.HTTPError as err:
        raw, status = err.read(), err.code
    try:
        return status, json.loads(raw)
    except ValueError:
        return status, raw


def check(label, got, expected):
    mark = "ok  " if got == expected else "FAIL"
    print(f"{mark} {label}: {got} (expected {expected})")
    if got != expected:
        failures.append(label)


def login(email, password):
    status, body = call("POST", "/login", {"email": email, "password": password})
    return body["token"] if status == 200 else None


admin = login("joao@email.com", "1234")
user = login("maria@email.com", "abcd")
check("admin and user can log in", bool(admin and user), True)
check("login token is not the old fake one", admin.startswith("fake-jwt-token"), False)

check("anonymous DELETE /tasks/1", call("DELETE", "/tasks/1")[0], 401)
check("fake token DELETE /tasks/1", call("DELETE", "/tasks/1", token="fake-jwt-token-1")[0], 401)
check("tampered token DELETE /tasks/1", call("DELETE", "/tasks/1", token=admin[:-3] + "xyz")[0], 401)
check("user-role token DELETE /tasks/1", call("DELETE", "/tasks/1", token=user)[0], 403)
check("admin token DELETE /tasks/1", call("DELETE", "/tasks/1", token=admin)[0], 200)

check("anonymous creates admin user", call("POST", "/users", {"name": "A", "email": "a@x.com", "password": "abcd", "role": "admin"})[0], 401)
check("user-role creates admin user", call("POST", "/users", {"name": "A", "email": "a@x.com", "password": "abcd", "role": "admin"}, user)[0], 403)
check("admin creates admin user", call("POST", "/users", {"name": "A", "email": "a@x.com", "password": "abcd", "role": "admin"}, admin)[0], 201)
check("anonymous creates default-role user", call("POST", "/users", {"name": "B", "email": "b@x.com", "password": "abcd"})[0], 201)
check("anonymous promotes a user to admin", call("PUT", "/users/2", {"role": "admin"})[0], 401)
check("user-role promotes a user to admin", call("PUT", "/users/2", {"role": "admin"}, user)[0], 403)

check("anonymous GET /reports/summary", call("GET", "/reports/summary")[0], 401)
check("admin GET /reports/summary", call("GET", "/reports/summary", token=admin)[0], 200)
check("anonymous DELETE /categories/1", call("DELETE", "/categories/1")[0], 401)
check("admin DELETE /categories/1", call("DELETE", "/categories/1", token=admin)[0], 200)

check("open route GET /tasks stays anonymous", call("GET", "/tasks")[0], 200)
check("open route POST /tasks stays anonymous", call("POST", "/tasks", {"title": "Aberta"})[0], 201)

status, created = call("POST", "/users", {"name": "C", "email": "c@x.com", "password": "abcd"})
token_c = login("c@x.com", "abcd")
check("new user token works on a guarded route as 403 (not 401)", call("DELETE", "/tasks/2", token=token_c)[0], 403)
call("PUT", "/users/%s" % created["id"], {"active": False}, admin)
check("token of a deactivated user is rejected", call("DELETE", "/tasks/2", token=token_c)[0], 401)

print("FAILED: " + ", ".join(failures) if failures else "all auth checks passed")
sys.exit(1 if failures else 0)
