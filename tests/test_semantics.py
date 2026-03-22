"""
tests/test_semantics.py
Тесты семантики GateLang — зеркалят теоремы Lean 4.
"""
import pytest
from gatelang import (
    GRet, GEmit, GGate, GSeq, GPar, GTry, GWith, GWhile, GLoop, GGuard,
    GRaw, GUnit, GFact, GPair,
    PolicySnapshot, EvidenceRef, POLICY_ZERO,
    run, verify_program
)
from gatelang.semantics import eval2, gstep2, GDone, GCont, GError, GStuck
from gatelang.types import closure_gate, Verdict, policy_seq

POL2 = PolicySnapshot(id=1, min_evidence=2, effective_at=0)
EV2  = [EvidenceRef("a"), EvidenceRef("b")]
EV1  = [EvidenceRef("x")]

# ── Теорема: bigstep2_deterministic ──────────────────────────────────────
def test_gate_pass():
    r = run(GGate(EV2, POL2, agent_id=1), scope=0)
    assert isinstance(r.result, GFact)
    assert r.result.record.verdict == Verdict.PASS

def test_gate_fail():
    r = run(GGate(EV1, POL2, agent_id=1), scope=0)
    assert isinstance(r.result, GUnit)

def test_ret():
    r = run(GRet(GRaw(42)), scope=0)
    assert isinstance(r.result, GRaw)
    assert r.result.value == 42

def test_emit_no_record():
    """Теорема: no_spurious_facts — emit не создаёт записей."""
    r = run(GEmit(7), scope=0)
    assert isinstance(r.result, GUnit)
    assert r.records == []

# ── Теорема: eval2_monotone ───────────────────────────────────────────────
def test_eval2_monotone():
    """Если завершается за n шагов, завершается за m>=n."""
    prog = GRet(GRaw(1))
    v1 = eval2(prog, 0, POLICY_ZERO, 1)
    v2 = eval2(prog, 0, POLICY_ZERO, 100)
    assert v1 == v2

# ── gSeq ──────────────────────────────────────────────────────────────────
def test_seq_returns_second():
    """gSeq e1 e2 возвращает значение e2."""
    prog = GSeq(GGate(EV2, POL2, 1), GRet(GRaw(99)))
    r = run(prog, scope=0)
    assert isinstance(r.result, GRaw)
    assert r.result.value == 99

def test_seq_collects_records():
    prog = GSeq(GGate(EV2, POL2, 1), GGate(EV2, POL2, 2))
    r = run(prog, scope=0)
    assert len(r.records) == 2

# ── gPar ──────────────────────────────────────────────────────────────────
def test_par_returns_pair():
    """Теорема: par_ret_confluence."""
    prog = GPar(GRet(GRaw(1)), GRet(GRaw(2)))
    r = run(prog, scope=0)
    assert isinstance(r.result, GPair)

def test_par_both_records():
    prog = GPar(GGate(EV2, POL2, 1), GGate(EV2, POL2, 2))
    r = run(prog, scope=0)
    assert len(r.records) == 2

# ── gTry ──────────────────────────────────────────────────────────────────
def test_try_success():
    prog = GTry(GRet(GRaw(1)), GRet(GRaw(2)))
    r = run(prog, scope=0)
    assert isinstance(r.result, GRaw)
    assert r.result.value == 1

# ── gWith ─────────────────────────────────────────────────────────────────
def test_with_stricter_policy():
    """Теорема: with_policy_stricter."""
    strict = PolicySnapshot(id=2, min_evidence=3, effective_at=0)
    prog = GWith(strict, GGate(EV2, POL2, 1))
    r = run(prog, scope=0)
    # EV2 len=2 < strict min=3 → fail
    assert isinstance(r.result, GUnit)

# ── gWhile ────────────────────────────────────────────────────────────────
def test_while_zero():
    """Теорема: bigstep2_while_zero."""
    prog = GWhile(0, GGate(EV2, POL2, 1))
    r = run(prog, scope=0)
    assert isinstance(r.result, GUnit)

def test_while_n():
    """gWhile n body: завершается, n записей."""
    prog = GWhile(3, GGate(EV2, POL2, 1))
    r = run(prog, scope=0)
    assert isinstance(r.result, GUnit)
    assert len(r.records) == 3

# ── gLoop ─────────────────────────────────────────────────────────────────
def test_loop_n():
    prog = GLoop(4, GGate(EV2, POL2, 1))
    r = run(prog, scope=0)
    assert isinstance(r.result, GUnit)
    assert len(r.records) == 4

# ── closureGate детерминирован ────────────────────────────────────────────
def test_closuregate_deterministic():
    """Теорема: gate_is_deterministic."""
    v1 = closure_gate(EV2, POL2)
    v2 = closure_gate(EV2, POL2)
    assert v1 == v2

# ── policy_seq ────────────────────────────────────────────────────────────
def test_policy_seq_stricter():
    """Теорема: policySeq_stricter."""
    p1 = PolicySnapshot(id=1, min_evidence=2, effective_at=0)
    p2 = PolicySnapshot(id=2, min_evidence=3, effective_at=0)
    ps = policy_seq(p1, p2)
    assert ps.min_evidence >= p1.min_evidence
    assert ps.min_evidence >= p2.min_evidence

# ── 7-tuple well_formed ───────────────────────────────────────────────────
def test_7tuple_wellformed():
    """Теорема: gate_7tuple_wellformed."""
    from gatelang.types import gate_to_7tuple
    e7 = gate_to_7tuple(EV2, POL2, 1, 0, POLICY_ZERO)
    assert e7.well_formed

def test_7tuple_not_escalated():
    from gatelang.types import gate_to_7tuple
    e7 = gate_to_7tuple(EV2, POL2, 1, 0, POLICY_ZERO)
    assert not e7.escalated

# ── типизация ────────────────────────────────────────────────────────────
def test_typecheck_gate_pass():
    from gatelang.typechecker import verify_program
    from gatelang.types import TFact
    ok, typ, err = verify_program(GGate(EV2, POL2, 1))
    assert ok
    assert isinstance(typ, TFact)

def test_typecheck_emit():
    from gatelang.typechecker import verify_program
    from gatelang.types import TUnit
    ok, typ, err = verify_program(GEmit(0))
    assert ok
    assert isinstance(typ, TUnit)
