"""
tests/test_lean_compliance.py
------------------------------
Reference-тесты: Python-реализация ↔ Lean-спецификация.

Каждый кейс соответствует теореме (или определению) из Lean 4 формализации:
  Lang/GateLangV2.lean
  Lang/GateLangSemanticsV2.lean
  Lang/GateLangE7Tuple.lean

Author: A. A. Noh · UTE TLI SYSTEMS · DOI: 10.17605/OSF.IO/49UMB
"""
import pytest
from gatelang.types import (
    GVal, GUnit, GFact, GAgent, GRaw, GPair, GLeft, GRight,
    GExpr, GRet, GEmit, GGate, GSeq, GGuard, GPar, GTry, GWith, GWhile, GLoop,
    PolicySnapshot, EvidenceRef, Verdict, POLICY_ZERO,
    closure_gate, policy_seq, policy_par, ledger_mk, gate_to_7tuple,
    type_of_val, TUnit, TFact, TAgent, TRaw, TPair,
)
from gatelang.semantics import eval2, gstep2, compile2, run, GDone, GCont, GStuck


# ══════════════════════════════════════════════
# Общие фикстуры
# ══════════════════════════════════════════════

POL0 = POLICY_ZERO
POL1 = PolicySnapshot(id=1, min_evidence=1, effective_at=0)
POL2 = PolicySnapshot(id=2, min_evidence=2, effective_at=0)
POL3 = PolicySnapshot(id=3, min_evidence=3, effective_at=0)
EV0: list = []
EV1 = [EvidenceRef("e1")]
EV2 = [EvidenceRef("e1"), EvidenceRef("e2")]
EV3 = [EvidenceRef("e1"), EvidenceRef("e2"), EvidenceRef("e3")]


# ══════════════════════════════════════════════
# Reference cases: (program, expected_result_type, description, lean_theorem)
# expected_result_type: класс GVal или None (для stuck/timeout)
# ══════════════════════════════════════════════

LEAN_EVAL_CASES = [
    # ── gRet ──
    (GRet(GUnit()), GUnit, "gRet gUnit → gUnit",
     "GateLang.Semantics.gstep2_ret"),

    (GRet(GRaw(42)), GRaw, "gRet gRaw(42) → gRaw",
     "GateLang.Semantics.gstep2_ret_raw"),

    (GRet(GAgent(7)), GAgent, "gRet gAgent(7) → gAgent",
     "GateLang.Semantics.gstep2_ret_agent"),

    # ── gEmit ──
    (GEmit(0), GUnit, "gEmit 0 → gUnit (no records)",
     "GateLang.Semantics.no_spurious_facts"),

    (GEmit(999), GUnit, "gEmit 999 → gUnit",
     "GateLang.Semantics.emit_always_unit"),

    # ── gGate: PASS ──
    (GGate(EV2, POL2, agent_id=1), GFact, "gGate с достаточным evidence → GFact",
     "GateLang.Semantics.progress_gate_v2"),

    (GGate(EV3, POL2, agent_id=1), GFact, "gGate с избыточным evidence → GFact",
     "GateLang.Semantics.gate_surplus_evidence"),

    (GGate(EV1, POL1, agent_id=5), GFact, "gGate min=1, ev=1 → GFact",
     "GateLang.Semantics.gate_minimal_pass"),

    # ── gGate: FAIL ──
    (GGate(EV1, POL2, agent_id=1), GUnit, "gGate с недостаточным evidence → GUnit",
     "GateLang.Semantics.gate_insufficient_evidence"),

    (GGate(EV0, POL1, agent_id=1), GUnit, "gGate с пустым evidence, min=1 → GUnit",
     "GateLang.Semantics.gate_empty_evidence_fail"),

    # ── gSeq ──
    (GSeq(GRet(GRaw(1)), GRet(GRaw(2))), GRaw, "gSeq: возвращает второй",
     "GateLang.Semantics.seq_returns_second"),

    (GSeq(GEmit(1), GRet(GRaw(99))), GRaw, "gSeq emit+ret → ret value",
     "GateLang.Semantics.seq_emit_then_ret"),

    # ── gPar ──
    (GPar(GRet(GRaw(10)), GRet(GRaw(20))), GPair,
     "gPar: возвращает пару", "GateLang.Semantics.par_ret_confluence"),

    # ── gWith ──
    (GWith(POL3, GGate(EV2, POL2, 1)), GUnit,
     "gWith stricter policy → gate fails",
     "GateLang.Semantics.with_policy_stricter"),

    # ── gWhile 0 ──
    (GWhile(0, GGate(EV2, POL2, 1)), GUnit,
     "gWhile 0 → gUnit immediately",
     "GateLang.Semantics.bigstep2_while_zero"),

    # ── gLoop 0 ──
    (GLoop(0, GGate(EV2, POL2, 1)), GUnit,
     "gLoop 0 → gUnit immediately",
     "GateLang.Semantics.loop_zero_terminates"),

    # ── gTry success path ──
    (GTry(GRet(GRaw(1)), GRet(GRaw(2))), GRaw,
     "gTry: success → first branch",
     "GateLang.Semantics.try_type_safety"),

    # ── gGuard pass ──
    (GGuard(EV2, POL2, GRet(GRaw(7))), GRaw,
     "gGuard with sufficient evidence → executes body",
     "GateLang.Semantics.guard_sufficient"),

    # ── gGuard fail ──
    (GGuard(EV1, POL2, GRet(GRaw(7))), GUnit,
     "gGuard with insufficient evidence → gUnit",
     "GateLang.Semantics.guard_insufficient"),
]


@pytest.mark.parametrize(
    "program,expected_type,description,theorem",
    LEAN_EVAL_CASES,
    ids=[c[3] for c in LEAN_EVAL_CASES],
)
def test_lean_eval_compliance(program, expected_type, description, theorem):
    """Проверка: eval2 даёт ожидаемый тип результата (Lean reference)."""
    result = eval2(program, scope=0, context_policy=POLICY_ZERO, fuel=1000)
    assert result is not None, f"[{theorem}] eval2 returned None (stuck) for: {description}"
    assert isinstance(result, expected_type), (
        f"[{theorem}] Expected {expected_type.__name__}, got {type(result).__name__} "
        f"for: {description}"
    )


# ══════════════════════════════════════════════
# Closure-gate reference: (evidence, policy, expected_verdict, theorem)
# ══════════════════════════════════════════════

LEAN_CLOSURE_CASES = [
    (EV0, POL0, Verdict.PASS, "closureGate_empty_zero"),
    (EV2, POL2, Verdict.PASS, "closureGate_exact_match"),
    (EV3, POL2, Verdict.PASS, "closureGate_surplus"),
    (EV1, POL2, Verdict.CLOSED_WITH_MISSING_EVIDENCE, "closureGate_insufficient"),
    (EV0, POL1, Verdict.CLOSED_WITH_MISSING_EVIDENCE, "closureGate_empty_nonzero"),
]


@pytest.mark.parametrize(
    "evidence,policy,expected,theorem",
    LEAN_CLOSURE_CASES,
    ids=[c[3] for c in LEAN_CLOSURE_CASES],
)
def test_lean_closure_gate(evidence, policy, expected, theorem):
    """Lean: closureGate deterministic."""
    assert closure_gate(evidence, policy) == expected, f"Failed {theorem}"


# ══════════════════════════════════════════════
# Policy-seq reference: (p1, p2, expected_min, theorem)
# ══════════════════════════════════════════════

LEAN_POLICY_SEQ_CASES = [
    (POL0, POL0, 0, "policySeq_zero_zero"),
    (POL1, POL2, 2, "policySeq_stricter"),
    (POL2, POL1, 2, "policySeq_commutative_min"),
    (POL3, POL1, 3, "policySeq_max_dominates"),
]


@pytest.mark.parametrize(
    "p1,p2,expected_min,theorem",
    LEAN_POLICY_SEQ_CASES,
    ids=[c[3] for c in LEAN_POLICY_SEQ_CASES],
)
def test_lean_policy_seq(p1, p2, expected_min, theorem):
    """Lean: policySeq_stricter — min_evidence = max(p1.min, p2.min)."""
    result = policy_seq(p1, p2)
    assert result.min_evidence == expected_min, f"Failed {theorem}"


# ══════════════════════════════════════════════
# Event7 well-formedness reference
# ══════════════════════════════════════════════

LEAN_7TUPLE_CASES = [
    (EV2, POL2, 1, 0, POL0, True, "gate_7tuple_wellformed_pass"),
    (EV1, POL1, 5, 10, POL0, True, "gate_7tuple_wellformed_min"),
    (EV3, POL2, 3, 5, POL0, True, "gate_7tuple_wellformed_surplus"),
]


@pytest.mark.parametrize(
    "evidence,policy,agent,scope,ctx,expected_wf,theorem",
    LEAN_7TUPLE_CASES,
    ids=[c[6] for c in LEAN_7TUPLE_CASES],
)
def test_lean_7tuple_wellformed(evidence, policy, agent, scope, ctx, expected_wf, theorem):
    """Lean: gate_7tuple_wellformed — gate_to_7tuple always well-formed."""
    e7 = gate_to_7tuple(evidence, policy, agent, scope, ctx)
    assert e7.well_formed == expected_wf, f"Failed {theorem}"
    assert e7.escalated is False, f"Escalated must be False per Lean spec in {theorem}"


# ══════════════════════════════════════════════
# Compile2 record-count reference
# ══════════════════════════════════════════════

LEAN_COMPILE_CASES = [
    (GRet(GRaw(1)), 0, "compile2_ret_no_records"),
    (GEmit(1), 0, "compile2_emit_no_records"),
    (GGate(EV2, POL2, 1), 1, "compile2_gate_pass_one_record"),
    (GGate(EV1, POL2, 1), 0, "compile2_gate_fail_no_record"),
    (GSeq(GGate(EV2, POL2, 1), GGate(EV2, POL2, 2)), 2, "compile2_seq_two_gates"),
    (GWhile(3, GGate(EV2, POL2, 1)), 3, "compile2_while_n_records"),
]


@pytest.mark.parametrize(
    "program,expected_count,theorem",
    LEAN_COMPILE_CASES,
    ids=[c[2] for c in LEAN_COMPILE_CASES],
)
def test_lean_compile2_records(program, expected_count, theorem):
    """Lean: compile2_gate_sound."""
    records, _ = compile2(program, scope=0, context_policy=POL0, fuel=1000)
    assert len(records) == expected_count, (
        f"[{theorem}] Expected {expected_count} records, got {len(records)}"
    )


# ══════════════════════════════════════════════
# Type-of-val reference
# ══════════════════════════════════════════════

def test_lean_type_of_unit():
    """Lean: gtypeOf2 gUnit = TUnit."""
    assert isinstance(type_of_val(GUnit()), TUnit)


def test_lean_type_of_raw():
    """Lean: gtypeOf2 (gRaw n) = TRaw."""
    assert isinstance(type_of_val(GRaw(42)), TRaw)


def test_lean_type_of_agent():
    """Lean: gtypeOf2 (gAgent id) = TAgent."""
    assert isinstance(type_of_val(GAgent(1)), TAgent)


def test_lean_type_of_pair():
    """Lean: gtypeOf2 (gPair v1 v2) = TPair (gtypeOf2 v1) (gtypeOf2 v2)."""
    t = type_of_val(GPair(GRaw(1), GUnit()))
    assert isinstance(t, TPair)
