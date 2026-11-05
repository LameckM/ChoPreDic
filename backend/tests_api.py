"""Quick checks that every endpoint answers sensibly:  python tests_api.py"""
from fastapi.testclient import TestClient
from app.main import app

c = TestClient(app)


def get(path, **kw):
    r = c.get(path, **kw)
    assert r.status_code == 200, (path, r.status_code, r.text)
    return r.json()


assert get("/health")["status"] == "ok"

risk = get("/api/risk")
d = risk["districts"]
assert len(d) == 72, len(d)
assert all(0 <= x["risk"] <= 1 for x in d)
assert d[0]["risk"] >= d[-1]["risk"], "not sorted"
print("forecast year:", risk["forecast_year"], "| top:", d[0]["district"], d[0]["risk"])

s = get("/api/summary")
assert sum(s["levels"].values()) == 72
print("levels:", s["levels"])

a = get("/api/alerts?min_level=high")
assert a["count"] == s["levels"]["high"]
assert get("/api/alerts?min_level=medium")["count"] == s["levels"]["high"] + s["levels"]["medium"]

lus = get("/api/districts/lusaka")
assert lus["district"] == "Lusaka" and len(lus["history"]) == 11
assert c.get("/api/districts/Nowhere").status_code == 404
assert c.get("/api/alerts?min_level=bogus").status_code == 422

assert len(get("/api/districts")) == 72
assert len(get("/api/trends/national")) == 11
assert get("/api/model")["selected"] == risk["model"]
print("ALL API CHECKS PASSED")
