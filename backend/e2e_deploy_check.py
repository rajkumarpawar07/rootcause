"""Post-deploy verification against a live RootCause deployment.

Usage:
    python e2e_deploy_check.py https://rootcause-api.onrender.com [https://rootcause.vercel.app]

Checks: health, CORS preflight from the frontend origin, the 422
insufficient-responses split, and a full batch C paste — verifying the
~3-second cached response and the locked dashboard shape.
"""

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
rows = json.loads(
    (ROOT / "demo_data" / "synthetic_responses_30_batchC.json").read_text(encoding="utf-8")
)

API = sys.argv[1].rstrip("/")
WEB = sys.argv[2].rstrip("/") if len(sys.argv) > 2 else "http://localhost:3000"

failures = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail else ""))
    if not ok:
        failures.append(name)


def request(url: str, method: str = "GET", body: dict | None = None, headers: dict | None = None):
    data = json.dumps(body).encode() if body is not None else None
    all_headers = dict(headers or {})
    if data is not None:
        # urllib defaults to form encoding, which FastAPI rejects with a
        # pydantic list-detail 422 before the handler ever runs.
        all_headers.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=data, method=method, headers=all_headers)
    try:
        with urllib.request.urlopen(req, timeout=1800) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()


def header(headers: dict, name: str) -> str:
    """Case-insensitive lookup — ASGI servers send lowercase header names."""
    for key, value in headers.items():
        if key.lower() == name.lower():
            return value
    return ""


# 1. health
status, _, body = request(f"{API}/health")
check("health", status == 200 and json.loads(body).get("status") == "ok", f"{status}")

# 2. CORS preflight from deployed frontend origin
status, headers, _ = request(
    f"{API}/api/diagnose",
    method="OPTIONS",
    headers={"Origin": WEB, "Access-Control-Request-Method": "POST"},
)
allow = header(headers, "Access-Control-Allow-Origin")
check("CORS preflight", status == 200 and (allow == "*" or allow == WEB), f"allow-origin={allow!r}")

# 3. insufficient-responses split
status, _, body = request(
    f"{API}/api/diagnose",
    method="POST",
    body={"question": "q", "responses": [{"response": "a"}, {"response": "b"}]},
)
detail = json.loads(body).get("detail", {}) if body else {}
if not isinstance(detail, dict):  # pydantic validation errors use a list
    detail = {}
check(
    "422 split",
    status == 422 and detail.get("error") == "insufficient_responses",
    f"{status}, received={detail.get('received')}, minimum={detail.get('minimum')}",
)

# 4. batch C paste — cached response must be fast and identical
payload = {
    "question": "Why does ice float on water?",
    "correct_concept": "Density determines whether an object floats",
    "include_feedback": False,
    "responses": [{"student_id": r["student_id"], "response": r["response"]} for r in rows],
}
t0 = time.time()
status, _, body = request(f"{API}/api/diagnose", method="POST", body=payload)
elapsed = time.time() - t0
out = json.loads(body) if body else {}
solid = next((c for c in out.get("clusters", []) if c.get("category") == "solid_understanding"), None)
trio_ok = bool(solid) and {"s13", "s14", "s15"} <= set(solid["student_ids"])
check("batch C paste", status == 200 and out.get("responses_analyzed") == 30, f"{status}")
check("cached speed (<30s)", elapsed < 30, f"{elapsed:.1f}s")
check("locked cards intact (trio in solid slice)", trio_ok)
print("\nDashboard shape:")
for c in sorted(out.get("clusters", []), key=lambda c: (c["category"] != "misconception", -c["size"])):
    print(f"  [{c['category']}] {c['label']} ({c['size']} · {c['percentage']}%)")

print(f"\n{'ALL CHECKS PASSED' if not failures else 'FAILURES: ' + ', '.join(failures)}")
sys.exit(0 if not failures else 1)
