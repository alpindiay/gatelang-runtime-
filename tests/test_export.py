"""
tests/test_export.py
---------------------
Tests for JSON export and REST API.
"""
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from gatelang import (
    PolicySnapshot, EvidenceRef, POLICY_ZERO,
    GGate, GSeq, GEmit, GPar, GTry, GWith, GWhile, GRet,
    GUnit, GRaw,
    run, compile2, verify_program
)
from gatelang.export import (
    to_json, record_to_json, event7_to_json, val_to_json,
    policy_to_json, policy_from_json, evidence_from_json,
    expr_from_json, expr_to_json, trace_to_json
)

# ── Fixtures ────────────────────────────────────────────
@pytest.fixture
def policy():
    return PolicySnapshot(id=1, min_evidence=2, effective_at=0)

@pytest.fixture
def evidence():
    return [EvidenceRef("doc-A"), EvidenceRef("doc-B")]

@pytest.fixture
def passing_prog(policy, evidence):
    return GGate(evidence, policy, agent_id=42)

@pytest.fixture
def trace(passing_prog):
    return run(passing_prog, scope=100)

# ── Policy JSON ──────────────────────────────────────────
def test_policy_to_json(policy):
    d = policy_to_json(policy)
    assert d["id"] == 1
    assert d["min_evidence"] == 2
    assert d["effective_at"] == 0

def test_policy_roundtrip(policy):
    d = policy_to_json(policy)
    p2 = policy_from_json(d)
    assert p2.id == policy.id
    assert p2.min_evidence == policy.min_evidence

# ── LedgerRecord JSON ────────────────────────────────────
def test_record_to_json(trace):
    assert len(trace.records) == 1
    d = record_to_json(trace.records[0])
    assert d["verdict"] == "pass"
    assert d["valid"] == True
    assert len(d["evidence"]) == 2
    assert d["evidence"][0]["ref"] == "doc-A"

def test_record_json_has_policy(trace):
    d = record_to_json(trace.records[0])
    assert "policy" in d
    assert d["policy"]["min_evidence"] == 2

# ── Event7 JSON ──────────────────────────────────────────
def test_event7_to_json(trace):
    assert len(trace.event7s) == 1
    d = event7_to_json(trace.event7s[0])
    assert d["S"] == 42
    assert d["omega"] == "pass"
    assert d["escalated"] == False
    assert d["well_formed"] == True
    assert "lambda" in d
    assert "pi" in d

def test_event7_7tuple_keys(trace):
    d = event7_to_json(trace.event7s[0])
    for key in ["S", "C", "X", "gamma", "escalated", "omega", "lambda", "pi"]:
        assert key in d, f"Missing key: {key}"

# ── GVal JSON ────────────────────────────────────────────
def test_gunit_to_json():
    d = val_to_json(GUnit())
    assert d["type"] == "gUnit"

def test_graw_to_json():
    d = val_to_json(GRaw(42))
    assert d["type"] == "gRaw"
    assert d["value"] == 42

# ── Trace JSON ───────────────────────────────────────────
def test_trace_to_json(trace):
    d = trace_to_json(trace)
    assert d["success"] == True
    assert d["scope"] == 100
    assert len(d["records"]) == 1
    assert len(d["event7s"]) == 1
    assert d["stats"]["pass_count"] == 1
    assert d["stats"]["fail_count"] == 0

def test_trace_to_json_string(trace):
    s = to_json(trace)
    parsed = json.loads(s)
    assert parsed["success"] == True

# ── GExpr serialization ──────────────────────────────────
def test_expr_to_json_ggate(passing_prog):
    d = expr_to_json(passing_prog)
    assert d["type"] == "gGate"
    assert d["agent_id"] == 42
    assert len(d["evidence"]) == 2

def test_expr_roundtrip_ggate(passing_prog, policy, evidence):
    d = expr_to_json(passing_prog)
    s = json.dumps(d)
    restored = expr_from_json(json.loads(s))
    trace1 = run(passing_prog, scope=0)
    trace2 = run(restored, scope=0)
    assert trace1.success == trace2.success
    assert len(trace1.records) == len(trace2.records)

def test_expr_roundtrip_gseq(policy, evidence):
    prog = GSeq(GEmit(7), GGate(evidence, policy, agent_id=1))
    d = expr_to_json(prog)
    restored = expr_from_json(d)
    t1 = run(prog, scope=0)
    t2 = run(restored, scope=0)
    assert t1.success == t2.success

def test_expr_roundtrip_gpar(policy, evidence):
    ev1 = [EvidenceRef("a")]
    p1 = PolicySnapshot(id=2, min_evidence=1, effective_at=0)
    prog = GPar(GGate(ev1, p1, agent_id=1), GGate(ev1, p1, agent_id=2))
    d = expr_to_json(prog)
    restored = expr_from_json(d)
    t1 = run(prog, scope=0)
    t2 = run(restored, scope=0)
    assert len(t1.records) == len(t2.records)

def test_expr_roundtrip_gwhile():
    p = PolicySnapshot(id=3, min_evidence=1, effective_at=0)
    ev = [EvidenceRef("tick")]
    prog = GWhile(3, GGate(ev, p, agent_id=0))
    d = expr_to_json(prog)
    restored = expr_from_json(d)
    t1 = run(prog, scope=0)
    t2 = run(restored, scope=0)
    assert len(t1.records) == len(t2.records) == 3

# ── REST API tests ───────────────────────────────────────
@pytest.fixture
def client():
    try:
        from gatelang.server import create_app
        app = create_app()
        app.config["TESTING"] = True
        with app.test_client() as c:
            yield c
    except ImportError:
        pytest.skip("Flask not available")

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    d = json.loads(r.data)
    assert d["ok"] == True
    assert d["status"] == "running"

def test_info(client):
    r = client.get("/info")
    assert r.status_code == 200
    d = json.loads(r.data)
    assert d["verified_theorems"] == 1213
    assert d["sorry_count"] == 0

def test_run_pass(client):
    payload = {
        "expr": {
            "type": "gGate",
            "evidence": [{"ref": "doc-1"}, {"ref": "doc-2"}],
            "policy": {"id": 1, "min_evidence": 2, "effective_at": 0},
            "agent_id": 42
        },
        "scope": 100
    }
    r = client.post("/run", json=payload)
    assert r.status_code == 200
    d = json.loads(r.data)
    assert d["ok"] == True
    assert d["success"] == True
    assert len(d["records"]) == 1
    assert d["records"][0]["verdict"] == "pass"
    assert d["stats"]["pass_count"] == 1

def test_run_fail(client):
    payload = {
        "expr": {
            "type": "gGate",
            "evidence": [{"ref": "doc-1"}],
            "policy": {"id": 1, "min_evidence": 3, "effective_at": 0},
            "agent_id": 1
        },
        "scope": 0
    }
    r = client.post("/run", json=payload)
    d = json.loads(r.data)
    assert d["ok"] == True
    assert len(d["records"]) == 0

def test_run_par(client):
    p = {"id": 1, "min_evidence": 1, "effective_at": 0}
    ev = [{"ref": "sig"}]
    payload = {
        "expr": {
            "type": "gPar",
            "e1": {"type": "gGate", "evidence": ev, "policy": p, "agent_id": 1},
            "e2": {"type": "gGate", "evidence": ev, "policy": p, "agent_id": 2}
        },
        "scope": 10
    }
    r = client.post("/run", json=payload)
    d = json.loads(r.data)
    assert d["stats"]["record_count"] == 2

def test_typecheck_pass(client):
    payload = {
        "expr": {
            "type": "gGate",
            "evidence": [{"ref": "d1"}, {"ref": "d2"}],
            "policy": {"id": 1, "min_evidence": 2, "effective_at": 0},
            "agent_id": 1
        }
    }
    r = client.post("/typecheck", json=payload)
    d = json.loads(r.data)
    assert d["ok"] == True
    assert d["type_checks"] == True
    assert d["type"]["type"] == "TFact"

def test_typecheck_emit(client):
    payload = {"expr": {"type": "gEmit", "code": 42}}
    r = client.post("/typecheck", json=payload)
    d = json.loads(r.data)
    assert d["type"]["type"] == "TUnit"

def test_compile(client):
    payload = {
        "expr": {
            "type": "gGate",
            "evidence": [{"ref": "e1"}, {"ref": "e2"}],
            "policy": {"id": 1, "min_evidence": 2, "effective_at": 0},
            "agent_id": 5
        },
        "scope": 0
    }
    r = client.post("/compile", json=payload)
    d = json.loads(r.data)
    assert d["ok"] == True
    assert d["count"] == 1
    assert d["all_valid"] == True

def test_batch(client):
    p = {"id": 1, "min_evidence": 1, "effective_at": 0}
    ev = [{"ref": "s"}]
    payload = {
        "programs": [
            {"id": "p1", "expr": {"type": "gGate", "evidence": ev, "policy": p, "agent_id": 1}, "scope": 0},
            {"id": "p2", "expr": {"type": "gEmit", "code": 7}, "scope": 0},
            {"id": "p3", "expr": {"type": "gGate", "evidence": ev, "policy": p, "agent_id": 2}, "scope": 1},
        ]
    }
    r = client.post("/batch", json=payload)
    d = json.loads(r.data)
    assert d["ok"] == True
    assert d["count"] == 3
    assert all(x["ok"] for x in d["results"])

def test_not_found(client):
    r = client.get("/nonexistent")
    assert r.status_code == 404

def test_invalid_expr(client):
    r = client.post("/run", json={"expr": {"type": "unknown_construct"}})
    assert r.status_code == 400
