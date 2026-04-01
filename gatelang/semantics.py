"""
gatelang/semantics.py
----------------------
Операционная семантика GateLang v2.
Mirrors: Lang/GateLangV2.lean · Lang/GateLangSemanticsV2.lean
Author: A. A. Noh · UTE TLI SYSTEMS · DOI: 10.17605/OSF.IO/49UMB

Ключевые теоремы:
  bigstep2_deterministic  — детерминизм
  eval2_monotone          — монотонность по fuel
  no_spurious_facts       — emit не создаёт записей
  compile2_gate_sound     — все записи корректны
"""

from __future__ import annotations
from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass
from .types import (
    GVal, GUnit, GFact, GAgent, GRaw, GPair, GLeft, GRight,
    GExpr, GRet, GEmit, GGate, GSeq, GGuard, GPar, GTry, GWith, GWhile, GLoop,
    PolicySnapshot, LedgerRecord, EvidenceRef, Verdict, EscalationReason,
    POLICY_ZERO, policy_seq, closure_gate, ledger_mk,
    gate_to_7tuple, Event7
)


# ══════════════════════════════════════════════
# РЕЗУЛЬТАТЫ ВЫЧИСЛЕНИЯ / GResult2
# ══════════════════════════════════════════════

class GResult:
    """Lean: inductive GResult2"""
    pass


@dataclass
class GDone(GResult):
    """Lean: gDone (v : GVal2) — вычисление завершено"""
    value: GVal
    def __str__(self): return f"gDone({self.value})"


@dataclass
class GCont(GResult):
    """Lean: gCont (e : GExpr2) — продолжение"""
    expr: GExpr
    def __str__(self): return f"gCont({self.expr})"


@dataclass
class GStuck(GResult):
    """Lean: gStuck — застревание (не должно возникать для типизированных программ)"""
    def __str__(self): return "gStuck"


@dataclass
class GError(GResult):
    """Lean: gError (s : String) — ошибка"""
    message: str
    def __str__(self): return f"gError({self.message!r})"


# ══════════════════════════════════════════════
# МАЛОШАГОВАЯ СЕМАНТИКА / SMALL-STEP
# ══════════════════════════════════════════════

def gstep2(expr: GExpr, scope: int, context_policy: PolicySnapshot) -> GResult:
    """
    Lean: def gstep2 (e : GExpr2) (t : GScopeId) (pol : PolicySnapshot) : GResult2
    Теорема: progress_gate_v2 — gstep2 (gGate ..) ≠ gStuck
    """

    # gRet v → gDone v
    if isinstance(expr, GRet):
        return GDone(expr.value)

    # gEmit n → gDone gUnit
    # Теорема: no_spurious_facts — emit не создаёт LedgerRecord
    if isinstance(expr, GEmit):
        return GDone(GUnit())

    # gGate ev p ag → gDone (gFact r) или gDone gUnit
    if isinstance(expr, GGate):
        eff_policy = policy_seq(context_policy, expr.policy)
        verdict = closure_gate(expr.evidence, eff_policy)
        if verdict == Verdict.PASS:
            record = ledger_mk(scope, expr.evidence, eff_policy, scope)
            return GDone(GFact(record))
        else:
            return GDone(GUnit())

    # gSeq e1 e2: один шаг e1, затем GCont(e2)
    # Lean: gstep2 (gSeq e1 e2) = если gDone → GCont e2
    if isinstance(expr, GSeq):
        r1 = gstep2(expr.e1, scope, context_policy)
        if isinstance(r1, GDone):
            return GCont(expr.e2)
        elif isinstance(r1, GCont):
            return GCont(GSeq(r1.expr, expr.e2))
        elif isinstance(r1, GError):
            return r1
        return GStuck()

    # gGuard ev p body — guard с предусловием
    if isinstance(expr, GGuard):
        eff_policy = policy_seq(context_policy, expr.policy)
        if len(expr.evidence) >= eff_policy.min_evidence:
            return gstep2(expr.body, scope, context_policy)
        return GDone(GUnit())

    # gPar e1 e2 → выполнить оба, результат gPair
    # Теорема: par_ret_confluence
    if isinstance(expr, GPar):
        r1 = gstep2(expr.e1, scope, context_policy)
        r2 = gstep2(expr.e2, scope, context_policy)
        if isinstance(r1, GDone) and isinstance(r2, GDone):
            return GDone(GPair(r1.value, r2.value))
        elif isinstance(r1, GError):
            return r1
        elif isinstance(r2, GError):
            return r2
        return GStuck()

    # gTry e1 e2 — попытка e1, при ошибке e2
    # Теорема: try_type_safety
    if isinstance(expr, GTry):
        r1 = gstep2(expr.e1, scope, context_policy)
        if isinstance(r1, GError):
            return gstep2(expr.e2, scope, context_policy)
        return r1

    # gWith pol body — локальная политика
    # Теорема: with_policy_stricter
    if isinstance(expr, GWith):
        local_policy = policy_seq(context_policy, expr.policy)
        return gstep2(expr.body, scope, local_policy)

    # gWhile 0 body → gDone gUnit
    # gWhile (n+1) body → один шаг body, затем GCont(gWhile n body)
    if isinstance(expr, GWhile):
        if expr.fuel == 0:
            return GDone(GUnit())
        r = gstep2(expr.body, scope, context_policy)
        if isinstance(r, GDone):
            return GCont(GWhile(expr.fuel - 1, expr.body))
        elif isinstance(r, GError):
            return GDone(GUnit())
        return GStuck()

    # gLoop — аналог gWhile
    if isinstance(expr, GLoop):
        if expr.fuel == 0:
            return GDone(GUnit())
        r = gstep2(expr.body, scope, context_policy)
        if isinstance(r, GDone):
            return GCont(GLoop(expr.fuel - 1, expr.body))
        elif isinstance(r, GError):
            return GStuck()
        return GStuck()

    return GStuck()


# ══════════════════════════════════════════════
# ИНТЕРПРЕТАТОР С FUEL / eval2
# ══════════════════════════════════════════════

def eval2(expr: GExpr, scope: int, context_policy: PolicySnapshot,
          fuel: int) -> Optional[GVal]:
    """
    Lean: def eval2 (e : GExpr2) (t : GScopeId) (pol : PolicySnapshot)
                    (fuel : Nat) : Option GVal2

    Теорема: eval2_monotone — если завершается за n шагов,
    то завершается за m≥n шагов с тем же результатом.

    ВАЖНО: цикл по GCont — зеркалит Lean eval2 точно.
    """
    current = expr
    remaining = fuel
    while remaining > 0:
        result = gstep2(current, scope, context_policy)
        if isinstance(result, GDone):
            return result.value
        elif isinstance(result, GCont):
            current = result.expr
            remaining -= 1
        else:
            return None
    return None


# ══════════════════════════════════════════════
# КОМПИЛЯТОР В LEDGER / compile2
# ══════════════════════════════════════════════

def compile2(expr: GExpr, scope: int, context_policy: PolicySnapshot,
             fuel: int, prev_hash: str = "") -> Tuple[List[LedgerRecord], str]:
    """
    Lean: def compile2 (e : GExpr2) (t : GScopeId) (pol : PolicySnapshot)
                       (fuel : Nat) : List LedgerRecord

    Компилирует программу в список журнальных записей с поддержкой Hash-Chain.
    """
    if fuel == 0:
        return [], prev_hash
    return _compile_rec(expr, scope, context_policy, fuel, prev_hash)


def _compile_rec(expr: GExpr, scope: int, pol: PolicySnapshot,
                 fuel: int, current_hash: str = "") -> Tuple[List[LedgerRecord], str]:
    """Рекурсивный компилятор с пробросом хэша."""

    if isinstance(expr, GRet) or isinstance(expr, GEmit):
        return [], current_hash

    if isinstance(expr, GGate):
        eff_policy = policy_seq(pol, expr.policy)

        # Claim 10: Time-lock check for GGate
        if getattr(expr, 'expires_at', None) is not None:
            import time as _time
            if _time.time() > expr.expires_at:
                from .types import GFact
                record = LedgerRecord(
                    scope=scope,
                    verdict=Verdict.CLOSED_WITH_MISSING_EVIDENCE,
                    policy=eff_policy,
                    evidence=list(expr.evidence),
                    closed_at=scope,
                    prev_hash=current_hash
                )
                # Mark as escalated in metadata if possible
                new_hash = record.compute_hash()
                return [record], new_hash
        verdict = closure_gate(expr.evidence, eff_policy)
        if verdict == Verdict.PASS:
            from .types import LedgerRecord
            record = LedgerRecord(
                scope=scope,
                verdict=verdict,
                policy=eff_policy,
                evidence=list(expr.evidence),
                closed_at=scope,
                prev_hash=current_hash
            )
            new_hash = record.compute_hash()
            return [record], new_hash
        return [], current_hash

    if isinstance(expr, GSeq):
        recs1, hash1 = _compile_rec(expr.e1, scope, pol, fuel, current_hash)
        recs2, hash2 = _compile_rec(expr.e2, scope, pol, fuel, hash1)
        return recs1 + recs2, hash2

    if isinstance(expr, GGuard):
        eff_policy = policy_seq(pol, expr.policy)
        if len(expr.evidence) >= eff_policy.min_evidence:
            return _compile_rec(expr.body, scope, pol, fuel, current_hash)
        return [], current_hash

    if isinstance(expr, GPar):
        recs1, hash1 = _compile_rec(expr.e1, scope, pol, fuel, current_hash)
        recs2, hash2 = _compile_rec(expr.e2, scope, pol, fuel, hash1)
        return recs1 + recs2, hash2

    if isinstance(expr, GTry):
        r1 = gstep2(expr.e1, scope, pol)
        if isinstance(r1, GError):
            return _compile_rec(expr.e2, scope, pol, fuel, current_hash)
        return _compile_rec(expr.e1, scope, pol, fuel, current_hash)

    if isinstance(expr, GWith):
        local_pol = policy_seq(pol, expr.policy)
        return _compile_rec(expr.body, scope, local_pol, fuel, current_hash)

    if isinstance(expr, (GWhile, GLoop)):
        records = []
        h = current_hash
        for _ in range(expr.fuel):
            recs, h = _compile_rec(expr.body, scope, pol, fuel, h)
            records.extend(recs)
        return records, h

    return [], current_hash


# ══════════════════════════════════════════════
# ТРАССИРОВКА / TRACE
# ══════════════════════════════════════════════

@dataclass
class ExecutionTrace:
    """Полный след выполнения программы."""
    expr: GExpr
    scope: int
    context_policy: PolicySnapshot
    result: Optional[GVal]
    records: List[LedgerRecord]
    event7s: List[Event7]
    emit_codes: List[int]
    final_hash: str = ""

    @property
    def success(self) -> bool:
        return self.result is not None

    def summary(self) -> str:
        lines = [
            f"═══ GateLang Execution Trace ═══",
            f"Scope:    {self.scope}",
            f"Policy:   {self.context_policy}",
            f"Result:   {self.result}",
            f"Records:  {len(self.records)}",
            f"Events:   {len(self.event7s)}",
            f"Emits:    {self.emit_codes}",
            "",
        ]
        if self.records:
            lines.append("── LedgerRecords ──")
            for i, r in enumerate(self.records):
                lines.append(f"  [{i}] {r}")
        if self.event7s:
            lines.append("")
            lines.append("── 7-Tuples ──")
            for i, e in enumerate(self.event7s):
                lines.append(f"  [{i}] {e}")
        return "\n".join(lines)


def _time_lock_escalation_trace(expr: GExpr, scope: int, context_policy: PolicySnapshot, prev_hash: str) -> ExecutionTrace:
    """
    Claim 10: If an Event7 is time-expired, we do not execute semantics; we record an escalation ledger record.
    This keeps hash-chain continuity and makes the hold auditable.
    """
    # Create a minimal escalation ledger record
    rec = LedgerRecord(
        scope=scope,
        verdict=Verdict.CLOSED_WITH_MISSING_EVIDENCE,
        policy=context_policy,
        evidence=[],
        closed_at=scope,
        prev_hash=prev_hash,
    )
    new_hash = rec.compute_hash()
    e7 = Event7(
        subject=0,
        context=scope,
        execution=[],
        conflict=False,
        escalated=True,
        outcome=Verdict.CLOSED_WITH_MISSING_EVIDENCE,
        ledger=rec,
        policy=context_policy,
    )
    try:
        e7.escalation_reason = EscalationReason.TIME_EXPIRED
    except Exception:
        pass
    e7.hash = e7.compute_hash()
    return ExecutionTrace(
        expr=expr,
        scope=scope,
        context_policy=context_policy,
        result=GUnit(),
        records=[rec],
        event7s=[e7],
        emit_codes=[],
        final_hash=new_hash,
    )


def _collect_emits(expr: GExpr) -> List[int]:
    """Собрать все gEmit коды."""
    codes = []
    if isinstance(expr, GEmit):
        codes.append(expr.code)
    elif isinstance(expr, GSeq):
        codes.extend(_collect_emits(expr.e1))
        codes.extend(_collect_emits(expr.e2))
    elif isinstance(expr, GPar):
        codes.extend(_collect_emits(expr.e1))
        codes.extend(_collect_emits(expr.e2))
    elif isinstance(expr, GTry):
        codes.extend(_collect_emits(expr.e1))
    elif isinstance(expr, GWith):
        codes.extend(_collect_emits(expr.body))
    elif isinstance(expr, GWhile):
        codes.extend(_collect_emits(expr.body) * expr.fuel)
    elif isinstance(expr, GLoop):
        codes.extend(_collect_emits(expr.body) * expr.fuel)
    return codes


def _extract_event7s(records: List[LedgerRecord], expr: GExpr,
                     context_policy: PolicySnapshot) -> List[Event7]:
    """Извлечь 7-tuple для каждого gGate вызова."""
    events = []
    _collect_gate_events(expr, context_policy, events)
    return events


def _collect_gate_events(expr: GExpr, pol: PolicySnapshot,
                         acc: List[Event7]) -> None:
    if isinstance(expr, GGate):
        e7 = gate_to_7tuple(expr.evidence, expr.policy,
                            expr.agent_id, 0, pol)
        acc.append(e7)
    elif isinstance(expr, GSeq):
        _collect_gate_events(expr.e1, pol, acc)
        _collect_gate_events(expr.e2, pol, acc)
    elif isinstance(expr, GPar):
        _collect_gate_events(expr.e1, pol, acc)
        _collect_gate_events(expr.e2, pol, acc)
    elif isinstance(expr, GTry):
        _collect_gate_events(expr.e1, pol, acc)
    elif isinstance(expr, GWith):
        _collect_gate_events(expr.body, policy_seq(pol, expr.policy), acc)
    elif isinstance(expr, GGuard):
        _collect_gate_events(expr.body, pol, acc)
    elif isinstance(expr, (GWhile, GLoop)):
        _collect_gate_events(expr.body, pol, acc)


def run(expr: GExpr, scope: int = 0,
        context_policy: Optional[PolicySnapshot] = None,
        fuel: int = 1000,
        prev_hash: str = "", event: Optional[Event7] = None) -> ExecutionTrace:
    """
    Основная точка входа. Запустить программу и вернуть полный след.
    """
    if context_policy is None:
        context_policy = POLICY_ZERO

        # Auto-detect expires_at from GGate if not provided in event
    if event is None and isinstance(expr, GGate) and getattr(expr, 'expires_at', None) is not None:
        # Create a dummy event for the existing time-lock check below
        event = Event7(0, scope, [], False, False, Verdict.PASS, None, context_policy, expires_at=expr.expires_at)
    # Claim 10: time-lock enforcement (semantic layer)
    if event is not None and hasattr(event, "is_expired"):
        try:
            import time as _time
            if event.is_expired(_time.time()):
                return _time_lock_escalation_trace(expr, scope, context_policy, prev_hash)
        except Exception:
            pass

    result = eval2(expr, scope, context_policy, fuel)
    records, final_hash = compile2(expr, scope, context_policy, fuel, prev_hash)

    # Генерируем Event7 из выражений (сохраняя agent_id)
    event7s = _extract_event7s(records, expr, context_policy)
    for e7 in event7s:
        e7.hash = e7.compute_hash()

    emits = _collect_emits(expr)

    return ExecutionTrace(
        expr=expr,
        scope=scope,
        context_policy=context_policy,
        result=result,
        records=records,
        event7s=event7s,
        emit_codes=emits,
        final_hash=final_hash
    )
