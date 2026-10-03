"""End-to-end smoke test against a running API.

    python3 scripts/smoke_test.py [base_url]
"""
from __future__ import annotations

import json
import os
import sys

import requests

BASE = (sys.argv[1] if len(sys.argv) > 1 else os.getenv("BASE_URL", "http://localhost:8000")).rstrip("/")

results: list[tuple[str, bool, str]] = []


def check(name: str, fn) -> None:
    try:
        ok, detail = fn()
    except Exception as exc:  # noqa: BLE001
        ok, detail = False, f"{type(exc).__name__}: {exc}"
    results.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name:38} {detail}")


def get(path: str, **kw):
    r = requests.get(BASE + path, timeout=120, **kw)
    r.raise_for_status()
    return r.json()


def post(path: str, payload=None, **kw):
    r = requests.post(BASE + path, json=payload, timeout=300, **kw)
    r.raise_for_status()
    return r.json()


def has_envelope(j) -> bool:
    return isinstance(j, dict) and "data" in j and "provenance" in j


# ---------------------------------------------------------------------------

def t_health():
    j = get("/health")
    return j.get("status") == "ok", f"llm={j.get('llmBackend')} embed={j.get('embeddingModel')}"


def t_expeditions():
    j = get("/api/expeditions")
    n = len(j["data"])
    return has_envelope(j) and n > 0, f"{n} expeditions"


def t_expedition_detail():
    j = get("/api/expeditions/43rd-isea")
    d = j["data"]
    return (
        len(d.get("timeline", [])) > 0 and len(d.get("team", [])) > 0
    ), f"{len(d.get('timeline', []))} events, {len(d.get('team', []))} members"


def t_stations():
    j = get("/api/stations")
    return len(j["data"]) >= 3, f"{len(j['data'])} stations"


def t_station_detail():
    j = get("/api/stations/maitri")
    d = j["data"]
    return d["counts"]["documents"] > 0, f"docs={d['counts']['documents']} weather={'yes' if d.get('weatherPreview') else 'no'}"


def t_map():
    j = get("/api/map/features")
    return len(j["data"]["features"]) > 0, f"{len(j['data']['features'])} features, layers={j['data']['layers']}"


def t_search():
    j = post("/api/search", {"q": "sea ice thickness Prydz Bay", "limit": 5})
    d = j["data"]
    return d["total"] > 0, f"{len(d['documents'])} docs, {len(d['datasets'])} datasets, {len(d['media'])} media"


def t_search_filter():
    j = post("/api/search", {"q": "permafrost", "station": "himadri", "limit": 5})
    return j["data"]["total"] > 0, f"station filter -> {j['data']['total']} hits"


def t_ai_query():
    j = post("/api/ai/query", {"q": "What was the maximum sea ice thickness measured at Prydz Bay?", "top_k": 5})
    d = j["data"]
    return (
        len(d.get("answer", "")) > 40 and len(d.get("citations", [])) > 0
    ), f"generator={d.get('generator')} passages={d.get('passageCount')} citations={len(d.get('citations', []))}"


def t_ai_query_related():
    j = post("/api/ai/query", {"q": "aerosol optical depth at Maitri", "top_k": 5})
    d = j["data"]
    return len(d.get("citations", [])) > 0, f"related={len(d.get('related', []))}"


def t_analytics():
    j = post("/api/ai/analytics", {"dataset": "Maitri Air Temperature", "op": "mean"})
    d = j["data"]
    return len(d.get("series", [])) > 0, f"op={d['op']} value={d['value']} n={d['observations']}"


def t_analytics_trend():
    j = post("/api/ai/analytics", {"dataset": "Svalbard Glacier Mass Balance", "op": "trend"})
    return "value" in j["data"], f"trend={j['data']['value']} range={j['data']['range']}"


def t_upload():
    doc_id = post("/api/search", {"q": "ice shelf thinning", "limit": 1})["data"]["documents"][0]["id"]
    j = get(f"/api/documents/{doc_id}")
    d = j["data"]
    return d.get("chunkCount", 0) > 0, f"chunks={d.get('chunkCount')} entities={len(d.get('entities', []))}"


def t_upload_file():
    path = "/tmp/fieldnote.txt"
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(
            "Field note from the Larsemann Hills traverse. Firn temperature at 2 m was -14.2 "
            "degrees Celsius. Wind speed averaged 11 metres per second from the east. Two "
            "Weddell seals were observed on the fast ice near the survey line."
        )
    with open(path, "rb") as fh:
        r = requests.post(BASE + "/api/documents/upload", files={"file": ("fieldnote.txt", fh, "text/plain")}, timeout=180)
    r.raise_for_status()
    d = r.json()["data"]
    return d.get("chunks", 0) > 0, f"chunks={d.get('chunks')} status={d.get('status')}"


def t_outreach():
    src = post("/api/search", {"q": "ice shelf thinning Larsemann Hills", "limit": 1})["data"]["documents"][0]["id"]
    j = post(
        "/api/outreach/generate",
        {
            "sourceId": src,
            "audience": "General Public",
            "language": "en",
            "format": "Instagram Carousel",
        },
    )
    d = j["data"]
    t_outreach.post_id = d["id"]
    return len(d.get("content", "")) > 30, f"stage={d['stage']} claims={len(d.get('claims', []))} model={j['provenance'].get('model')}"


def t_approve():
    pid = getattr(t_outreach, "post_id", None)
    if not pid:
        return False, "no post id"
    j = post(f"/api/outreach/{pid}/approve", {"stage": "SCIENTIST_REVIEW", "reviewer": "Dr. R. Iyer"})
    return j["data"]["stage"] == "SCIENTIST_REVIEW", f"stage={j['data']['stage']} next={j['data'].get('nextStage')}"


def t_citizen():
    media = post("/api/search", {"q": "penguin", "type": "media", "limit": 1})["data"]["media"]
    mid = media[0]["id"] if media else None
    j = post("/api/citizen/annotation", {"mediaId": mid, "label": "Emperor penguin", "voter": "volunteer-1"})
    d = j["data"]
    return d["voteCount"] >= 1, f"votes={d['voteCount']} consensus={d['consensus']}"


def t_field():
    j = post("/api/field/observation", {"stationId": "maitri", "payload": {"temp": -18.4, "note": "test"}})
    return j["data"]["status"] == "queued", f"receipt={j['data']['receiptId'][:8]}"


def t_admin():
    j = get("/api/admin/repository-health")
    d = j["data"]
    return d["kpis"]["documents"] > 0, f"docs={d['kpis']['documents']} chunks={d['kpis']['chunks']} coverage={d['kpis']['indexCoverage']}"


def main() -> int:
    print(f"Smoke testing {BASE}\n")
    for name, fn in [
        ("GET /health", t_health),
        ("GET /api/expeditions", t_expeditions),
        ("GET /api/expeditions/{id}", t_expedition_detail),
        ("GET /api/stations", t_stations),
        ("GET /api/stations/{id}", t_station_detail),
        ("GET /api/map/features", t_map),
        ("POST /api/search", t_search),
        ("POST /api/search (filtered)", t_search_filter),
        ("POST /api/ai/query", t_ai_query),
        ("POST /api/ai/query (related)", t_ai_query_related),
        ("POST /api/ai/analytics", t_analytics),
        ("POST /api/ai/analytics (trend)", t_analytics_trend),
        ("GET /api/documents/{id}", t_upload),
        ("POST /api/documents/upload", t_upload_file),
        ("POST /api/outreach/generate", t_outreach),
        ("POST /api/outreach/{id}/approve", t_approve),
        ("POST /api/citizen/annotation", t_citizen),
        ("POST /api/field/observation", t_field),
        ("GET /api/admin/repository-health", t_admin),
    ]:
        check(name, fn)

    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n{passed}/{len(results)} passed")
    if passed != len(results):
        print("\nFailures:")
        for name, ok, detail in results:
            if not ok:
                print(f"  - {name}: {detail}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
