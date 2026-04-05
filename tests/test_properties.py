"""
tests/test_properties.py
-------------------------
Property-based тесты для GateLang runtime.

Использует hypothesis для проверки алгебраических свойств:
  - Детерминизм eval2 и closure_gate
  - Коммутативность policy_par.min_evidence
  - Монотонность eval2 по fuel
  - Идемпотентность closure_gate
  - Валидность скомпилированных записей
  - Well-formedness Event7

Author: A. A. Noh · UTE TLI SYSTEMS · DOI: 10.17605/OSF.IO/49UMB
"""
import pytest
from hypothesis import given, strategies as st, settings, assume

from gatelang.types import (
    GVal, GUnit, GFact, GRaw, GPair,
    GExpr, GRet, GEmit, GGate, GSeq, GPar, GWhile,
    PolicySnapshot, EvidenceRef, Verdict, POLICY_ZERO,
    closure_gate, policy_seq, policy_par, ledger_mk, gate_to_7tuple,
)
from gatelang.semantics import eval2, compile2, run


# ══════════════════════════════════════════════
# Strategies
# ══════════════════════════════════════════════

st_min_evidence = st.integers(min_value=0, max_value=10)
st_policy_id = st.integers(min_value=0, max_value=100)
st_effective_at = st.integers(min_value=0, max_value=100)


@st.composite
def st_policy(draw):
    return PolicySnapshot(
        id=draw(st_policy_id),
        min_evidence=draw(st_min_evidence),
        effective_at=draw(st_effective_at),
    )


@st.composite
def st_evidence_list(draw, max_size=5):
    n = draw(st.integers(min_value=0, max_value=max_size))
    return [EvidenceRef(ref=f"ev_{i}") for i in range(n)]


# ══════════════════════════════════════════════
# 1. Детерминизм closure_gate
# Lean: gate_is_deterministic
# ══════════════════════════════════════════════

@given(evidence=st_evidence_list(), policy=st_policy())
def test_closure_gate_deterministic(evidence, policy):
    """closure_gate(ev, pol) == closure_gate(ev, pol) — всегда."""
    v1 = closure_gate(evidence, policy)
    v2 = closure_gate(evidence, policy)
    assert v1 == v2


# ══════════════════════════════════════════════
# 2. Идемпотентность closure_gate
# Повторный вызов с теми же аргументами → тот же результат
# ══════════════════════════════════════════════

@given(evidence=st_evidence_list(), policy=st_policy())
def test_closure_gate_idempotent(evidence, policy):
    """closure_gate чистая функция: повторный вызов стабилен."""
    result = closure_gate(evidence, policy)
    assert closure_gate(evidence, policy) == result
    assert closure_gate(evidence, policy) == result


# ══════════════════════════════════════════════
# 3. Коммутативность policy_par по min_evidence
# Lean: policyPar_weaker — min(p1.min, p2.min)
# ══════════════════════════════════════════════

@given(p1=st_policy(), p2=st_policy())
def test_policy_par_min_evidence_commutative(p1, p2):
    """policy_par(p1, p2).min_evidence == policy_par(p2, p1).min_evidence."""
    r12 = policy_par(p1, p2)
    r21 = policy_par(p2, p1)
    assert r12.min_evidence == r21.min_evidence


# ══════════════════════════════════════════════
# 4. policy_seq строже обоих аргументов
# Lean: policySeq_stricter
# ══════════════════════════════════════════════

@given(p1=st_policy(), p2=st_policy())
def test_policy_seq_stricter(p1, p2):
    """policy_seq(p1, p2).min_evidence >= max(p1.min, p2.min)."""
    result = policy_seq(p1, p2)
    assert result.min_evidence >= p1.min_evidence
    assert result.min_evidence >= p2.min_evidence


# ══════════════════════════════════════════════
# 5. policy_par мягче обоих аргументов
# Lean: policyPar_weaker
# ══════════════════════════════════════════════

@given(p1=st_policy(), p2=st_policy())
def test_policy_par_weaker(p1, p2):
    """policy_par(p1, p2).min_evidence <= min(p1.min, p2.min)."""
    result = policy_par(p1, p2)
    assert result.min_evidence <= p1.min_evidence
    assert result.min_evidence <= p2.min_evidence


# ══════════════════════════════════════════════
# 6. Детерминизм eval2
# Lean: bigstep2_deterministic
# ══════════════════════════════════════════════

@given(n=st.integers(min_value=0, max_value=1000))
def test_eval2_deterministic_ret(n):
    """eval2(gRet(gRaw(n))) вызванный дважды даёт одинаковый результат."""
    prog = GRet(GRaw(n))
    r1 = eval2(prog, 0, POLICY_ZERO, 100)
    r2 = eval2(prog, 0, POLICY_ZERO, 100)
    assert r1 == r2


@given(evidence=st_evidence_list(), policy=st_policy())
def test_eval2_deterministic_gate(evidence, policy):
    """eval2(gGate(ev, pol, ag)) вызванный дважды даёт одинаковый результат."""
    prog = GGate(evidence, policy, agent_id=0)
    r1 = eval2(prog, 0, POLICY_ZERO, 100)
    r2 = eval2(prog, 0, POLICY_ZERO, 100)
    assert r1 == r2


# ══════════════════════════════════════════════
# 7. Монотонность eval2 по fuel
# Lean: eval2_monotone
# ══════════════════════════════════════════════

@given(
    evidence=st_evidence_list(),
    policy=st_policy(),
    fuel1=st.integers(min_value=1, max_value=50),
    extra=st.integers(min_value=0, max_value=50),
)
def test_eval2_monotone(evidence, policy, fuel1, extra):
    """Если eval2 завершается за fuel1 шагов, за fuel1+extra тоже → тот же результат."""
    prog = GGate(evidence, policy, agent_id=0)
    r1 = eval2(prog, 0, POLICY_ZERO, fuel1)
    r2 = eval2(prog, 0, POLICY_ZERO, fuel1 + extra)
    if r1 is not None:
        assert r1 == r2, f"Monotonicity violation: fuel={fuel1} → {r1}, fuel={fuel1+extra} → {r2}"


# ══════════════════════════════════════════════
# 8. Все скомпилированные записи валидны
# Lean: compile2_gate_sound
# ══════════════════════════════════════════════

@given(evidence=st_evidence_list(), policy=st_policy())
def test_compiled_records_valid(evidence, policy):
    """Каждая запись compile2 имеет record.valid == True."""
    prog = GGate(evidence, policy, agent_id=0)
    records, _ = compile2(prog, 0, POLICY_ZERO, 100)
    for rec in records:
        assert rec.valid, f"Invalid record: {rec}"


# ══════════════════════════════════════════════
# 9. gate_to_7tuple всегда well-formed
# Lean: gate_7tuple_wellformed
# ══════════════════════════════════════════════

@given(
    evidence=st_evidence_list(),
    policy=st_policy(),
    agent=st.integers(min_value=0, max_value=100),
    scope=st.integers(min_value=0, max_value=100),
)
def test_gate_7tuple_always_wellformed(evidence, policy, agent, scope):
    """gate_to_7tuple(...).well_formed == True."""
    e7 = gate_to_7tuple(evidence, policy, agent, scope, POLICY_ZERO)
    assert e7.well_formed, f"Event7 not well-formed: {e7}"
    assert e7.escalated is False


# ══════════════════════════════════════════════
# 10. gEmit не создаёт записей (no_spurious_facts)
# ══════════════════════════════════════════════

@given(code=st.integers(min_value=0, max_value=10000))
def test_emit_no_records(code):
    """gEmit(n) никогда не создаёт LedgerRecord."""
    prog = GEmit(code)
    records, _ = compile2(prog, 0, POLICY_ZERO, 100)
    assert len(records) == 0


# ══════════════════════════════════════════════
# 11. gRet не создаёт записей
# ══════════════════════════════════════════════

@given(n=st.integers(min_value=0, max_value=10000))
def test_ret_no_records(n):
    """gRet(gRaw(n)) никогда не создаёт LedgerRecord."""
    prog = GRet(GRaw(n))
    records, _ = compile2(prog, 0, POLICY_ZERO, 100)
    assert len(records) == 0


# ══════════════════════════════════════════════
# 12. ledger_mk всегда создаёт валидную запись
# ══════════════════════════════════════════════

@given(evidence=st_evidence_list(), policy=st_policy(), scope=st.integers(min_value=0, max_value=100))
def test_ledger_mk_always_valid(evidence, policy, scope):
    """ledger_mk(...).valid == True."""
    rec = ledger_mk(scope, evidence, policy, scope)
    assert rec.valid


# ══════════════════════════════════════════════
# 13. closure_gate монотонна по evidence
# Lean: closureGate_monotone (больше evidence → не хуже)
# ══════════════════════════════════════════════

@given(policy=st_policy(), extra=st.integers(min_value=0, max_value=5))
def test_closure_gate_monotone_evidence(policy, extra):
    """Если len(ev) >= min → PASS, то len(ev)+extra >= min → тоже PASS."""
    ev_base = [EvidenceRef(ref=f"e{i}") for i in range(policy.min_evidence)]
    ev_more = ev_base + [EvidenceRef(ref=f"extra_{i}") for i in range(extra)]
    v_base = closure_gate(ev_base, policy)
    v_more = closure_gate(ev_more, policy)
    assert v_base == Verdict.PASS
    assert v_more == Verdict.PASS


# ══════════════════════════════════════════════
# 14. gPar коммутативен по количеству записей
# ══════════════════════════════════════════════

@given(evidence=st_evidence_list(max_size=3), policy=st_policy())
def test_par_record_count_commutative(evidence, policy):
    """GPar(g1, g2) и GPar(g2, g1) производят одинаковое число записей."""
    g1 = GGate(evidence, policy, agent_id=0)
    g2 = GGate(evidence, policy, agent_id=1)
    recs1, _ = compile2(GPar(g1, g2), 0, POLICY_ZERO, 100)
    recs2, _ = compile2(GPar(g2, g1), 0, POLICY_ZERO, 100)
    assert len(recs1) == len(recs2)
