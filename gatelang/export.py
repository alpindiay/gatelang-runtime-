"""
gatelang/export.py
-------------------
JSON export for GateLang types.
Mirrors: Lang/GateLangE7Tuple.lean · TLI/Core.lean
Author: A. A. Noh · UTE TLI SYSTEMS · DOI: 10.17605/OSF.IO/49UMB
"""

from __future__ import annotations
import json
from typing import Any, Dict, List, Optional, Union
from .types import (
    GVal, GUnit, GFact, GAgent, GRaw, GPair, GLeft, GRight,
    GExpr, GRet, GEmit, GGate, GSeq, GGuard, GPar, GTry, GWith, GWhile, GLoop,
    GType, TUnit, TFact, TAgent, TRaw, TPair, TLeft, TRight, TWith, TGuarded,
    PolicySnapshot, LedgerRecord, EvidenceRef, Verdict,
    Event7, POLICY_ZERO
)
from .semantics import ExecutionTrace


# ══════════════════════════════════════════════
# SERIALIZATION: Python → JSON-compatible dict
# ══════════════════════════════════════════════

def verdict_to_json(v: Verdict) -> str:
    return v.value


def evidence_to_json(e: EvidenceRef) -> Dict:
    return {"ref": e.ref}


def policy_to_json(p: PolicySnapshot) -> Dict:
    return {
        "id": p.id,
        "min_evidence": p.min_evidence,
        "effective_at": p.effective_at
    }


def record_to_json(r: LedgerRecord) -> Dict:
    return {
        "scope": r.scope,
        "verdict": verdict_to_json(r.verdict),
        "policy": policy_to_json(r.policy),
        "evidence": [evidence_to_json(e) for e in r.evidence],
        "closed_at": r.closed_at,
        "valid": r.valid
    }


def event7_to_json(e: Event7) -> Dict:
    return {
        "S": e.subject,
        "C": e.context,
        "X": [evidence_to_json(ev) for ev in e.execution],
        "gamma": e.conflict,
        "escalated": e.escalated,
        "omega": verdict_to_json(e.outcome),
        "lambda": record_to_json(e.ledger),
        "pi": policy_to_json(e.policy),
        "well_formed": e.well_formed
    }


def val_to_json(v: GVal) -> Dict:
    if isinstance(v, GUnit):
        return {"type": "gUnit"}
    elif isinstance(v, GFact):
        return {"type": "gFact", "record": record_to_json(v.record)}
    elif isinstance(v, GAgent):
        return {"type": "gAgent", "agent_id": v.agent_id}
    elif isinstance(v, GRaw):
        return {"type": "gRaw", "value": v.value}
    elif isinstance(v, GPair):
        return {"type": "gPair", "left": val_to_json(v.left), "right": val_to_json(v.right)}
    elif isinstance(v, GLeft):
        return {"type": "gLeft", "value": val_to_json(v.value)}
    elif isinstance(v, GRight):
        return {"type": "gRight", "value": val_to_json(v.value)}
    return {"type": "unknown"}


def type_to_json(t: GType) -> Dict:
    if isinstance(t, TUnit):
        return {"type": "TUnit"}
    elif isinstance(t, TFact):
        return {"type": "TFact", "policy": policy_to_json(t.policy)}
    elif isinstance(t, TAgent):
        return {"type": "TAgent"}
    elif isinstance(t, TRaw):
        return {"type": "TRaw"}
    elif isinstance(t, TPair):
        return {"type": "TPair", "left": type_to_json(t.left), "right": type_to_json(t.right)}
    elif isinstance(t, TWith):
        return {"type": "TWith", "policy": policy_to_json(t.policy), "inner": type_to_json(t.inner)}
    elif isinstance(t, TGuarded):
        return {"type": "TGuarded", "policy": policy_to_json(t.policy), "inner": type_to_json(t.inner)}
    return {"type": "unknown"}


def trace_to_json(trace: ExecutionTrace) -> Dict:
    return {
        "scope": trace.scope,
        "context_policy": policy_to_json(trace.context_policy),
        "success": trace.success,
        "result": val_to_json(trace.result) if trace.result is not None else None,
        "records": [record_to_json(r) for r in trace.records],
        "event7s": [event7_to_json(e) for e in trace.event7s],
        "emit_codes": trace.emit_codes,
        "stats": {
            "record_count": len(trace.records),
            "event7_count": len(trace.event7s),
            "emit_count": len(trace.emit_codes),
            "pass_count": sum(1 for r in trace.records if r.verdict == Verdict.PASS),
            "fail_count": sum(1 for r in trace.records if r.verdict != Verdict.PASS),
        }
    }


def to_json(obj: Any, indent: int = 2) -> str:
    """Serialize any GateLang object to JSON string."""
    if isinstance(obj, ExecutionTrace):
        data = trace_to_json(obj)
    elif isinstance(obj, LedgerRecord):
        data = record_to_json(obj)
    elif isinstance(obj, Event7):
        data = event7_to_json(obj)
    elif isinstance(obj, GVal):
        data = val_to_json(obj)
    elif isinstance(obj, PolicySnapshot):
        data = policy_to_json(obj)
    elif isinstance(obj, list):
        if all(isinstance(x, LedgerRecord) for x in obj):
            data = [record_to_json(r) for r in obj]
        elif all(isinstance(x, Event7) for x in obj):
            data = [event7_to_json(e) for e in obj]
        else:
            data = obj
    else:
        data = obj
    return json.dumps(data, indent=indent, ensure_ascii=False)


# ══════════════════════════════════════════════
# DESERIALIZATION: JSON dict → Python
# ══════════════════════════════════════════════

def policy_from_json(d: Dict) -> PolicySnapshot:
    return PolicySnapshot(
        id=d["id"],
        min_evidence=d["min_evidence"],
        effective_at=d.get("effective_at", 0)
    )


def evidence_from_json(d: Dict) -> EvidenceRef:
    return EvidenceRef(ref=str(d["ref"]))


def expr_from_json(d: Dict) -> GExpr:
    """Deserialize GExpr from JSON dict."""
    t = d["type"]
    if t == "gRet":
        return GRet(val_from_json(d["value"]))
    elif t == "gEmit":
        return GEmit(code=d["code"])
    elif t == "gGate":
        return GGate(
            evidence=[evidence_from_json(e) for e in d["evidence"]],
            policy=policy_from_json(d["policy"]),
            agent_id=d["agent_id"]
        )
    elif t == "gSeq":
        return GSeq(expr_from_json(d["e1"]), expr_from_json(d["e2"]))
    elif t == "gPar":
        return GPar(expr_from_json(d["e1"]), expr_from_json(d["e2"]))
    elif t == "gTry":
        return GTry(expr_from_json(d["e1"]), expr_from_json(d["e2"]))
    elif t == "gWith":
        return GWith(policy_from_json(d["policy"]), expr_from_json(d["body"]))
    elif t == "gWhile":
        return GWhile(fuel=d["fuel"], body=expr_from_json(d["body"]))
    elif t == "gLoop":
        return GLoop(fuel=d["fuel"], body=expr_from_json(d["body"]))
    raise ValueError(f"Unknown expression type: {t}")


def val_from_json(d: Dict) -> GVal:
    t = d["type"]
    if t == "gUnit":
        return GUnit()
    elif t == "gRaw":
        return GRaw(value=d["value"])
    elif t == "gAgent":
        return GAgent(agent_id=d["agent_id"])
    raise ValueError(f"Cannot deserialize value type: {t}")


def expr_from_json_str(s: str) -> GExpr:
    """Parse GExpr from JSON string."""
    return expr_from_json(json.loads(s))


def expr_to_json(expr: GExpr) -> Dict:
    """Serialize GExpr to JSON dict."""
    if isinstance(expr, GRet):
        return {"type": "gRet", "value": val_to_json(expr.value)}
    elif isinstance(expr, GEmit):
        return {"type": "gEmit", "code": expr.code}
    elif isinstance(expr, GGate):
        return {
            "type": "gGate",
            "evidence": [evidence_to_json(e) for e in expr.evidence],
            "policy": policy_to_json(expr.policy),
            "agent_id": expr.agent_id
        }
    elif isinstance(expr, GSeq):
        return {"type": "gSeq", "e1": expr_to_json(expr.e1), "e2": expr_to_json(expr.e2)}
    elif isinstance(expr, GPar):
        return {"type": "gPar", "e1": expr_to_json(expr.e1), "e2": expr_to_json(expr.e2)}
    elif isinstance(expr, GTry):
        return {"type": "gTry", "e1": expr_to_json(expr.e1), "e2": expr_to_json(expr.e2)}
    elif isinstance(expr, GWith):
        return {"type": "gWith", "policy": policy_to_json(expr.policy), "body": expr_to_json(expr.body)}
    elif isinstance(expr, GWhile):
        return {"type": "gWhile", "fuel": expr.fuel, "body": expr_to_json(expr.body)}
    elif isinstance(expr, GLoop):
        return {"type": "gLoop", "fuel": expr.fuel, "body": expr_to_json(expr.body)}
    raise ValueError(f"Unknown expression: {type(expr)}")
