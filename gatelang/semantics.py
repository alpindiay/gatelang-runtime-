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
from typing import List, Optional, Tuple
from dataclasses import dataclass
from .types import (
    GVal, GUnit, GFact, GAgent, GRaw, GPair, GLeft, GRight,
    GExpr, GRet, GEmit, GGate, GSeq, GGuard, GPar, GTry, GWith, GWhile, GLoop,
    PolicySnapshot, LedgerRecord, EvidenceRef, Verdict,
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

    # gSeq e1 e2 → выполнить e1, затем e2
    if isinstance(expr, GSeq):
        r1 = gstep2(expr.e1, scope, context_policy)
        if isinstance(r1, GDone):
            return gstep2(expr.e2, scope, context_policy)
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
    # gWhile (n+1) body → выполнить body, затем gWhile n body
    # Теорема: bigstep2_while_zero, bigstep2_while_ret_n
    if isinstance(expr, GWhile):
        if expr.fuel == 0:
            return GDone(GUnit())
        r = gstep2(expr.body, scope, context_policy)
        if isinstance(r, GDone):
            return gstep2(GWhile(expr.fuel - 1, expr.body), scope, context_policy)
        elif isinstance(r, GError):
            return r
        return GStuck()

    # gLoop — аналог gWhile
    if isinstance(expr, GLoop):
        if expr.fuel == 0:
            return GDone(GUnit())
        r = gstep2(expr.body, scope, context_policy)
        if isinstance(r, GDone):
            return gstep2(GLoop(expr.fuel - 1, expr.body), scope, context_policy)
        elif isinstance(r, GError):
            return r
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
    """
    if fuel == 0:
        return None
    result = gstep2(expr, scope, context_policy)
    if isinstance(result, GDone):
        return result.value
    return None


# ══════════════════════════════════════════════
# КОМПИЛЯТОР В LEDGER / compile2
# ══════════════════════════════════════════════

def compile2(expr: GExpr, scope: int, context_policy: PolicySnapshot,
             fuel: int) -> List[LedgerRecord]:
    """
    Lean: def compile2 (e : GExpr2) (t : GScopeId) (pol : PolicySnapshot)
                       (fuel : Nat) : List LedgerRecord

    Компилирует программу в список журнальных записей.

    Теоремы:
      no_spurious_facts  — compile2 (gEmit n) = []
      compile2_gate_sound — все записи корректны (FactSound)
    """
    if fuel == 0:
        return []
    return _compile_rec(expr, scope, context_policy, fuel)


def _compile_rec(expr: GExpr, scope: int, pol: PolicySnapshot,
                 fuel: int) -> List[LedgerRecord]:
    """Рекурсивный компилятор."""

    # gRet → []
    if isinstance(expr, GRet):
        return []

    # gEmit → [] (теорема: no_spurious_facts)
    if isinstance(expr, GEmit):
        return []

    # gGate pass → [LedgerRecord]
    # gGate fail → []
    if isinstance(expr, GGate):
        eff_policy = policy_seq(pol, expr.policy)
        verdict = closure_gate(expr.evidence, eff_policy)
        if verdict == Verdict.PASS:
            record = ledger_mk(scope, expr.evidence, eff_policy, scope)
            return [record]
        return []

    # gSeq → конкатенация
    if isinstance(expr, GSeq):
        return (_compile_rec(expr.e1, scope, pol, fuel) +
                _compile_rec(expr.e2, scope, pol, fuel))

    # gGuard → записи тела если guard прошёл
    if isinstance(expr, GGuard):
        eff_policy = policy_seq(pol, expr.policy)
        if len(expr.evidence) >= eff_policy.min_evidence:
            return _compile_rec(expr.body, scope, pol, fuel)
        return []

    # gPar → записи обеих веток
    if isinstance(expr, GPar):
        return (_compile_rec(expr.e1, scope, pol, fuel) +
                _compile_rec(expr.e2, scope, pol, fuel))

    # gTry → записи e1 (если нет ошибки) или e2
    if isinstance(expr, GTry):
        try:
            return _compile_rec(expr.e1, scope, pol, fuel)
        except Exception:
            return _compile_rec(expr.e2, scope, pol, fuel)

    # gWith → тело под строгой политикой
    if isinstance(expr, GWith):
        local_pol = policy_seq(pol, expr.policy)
        return _compile_rec(expr.body, scope, local_pol, fuel)

    # gWhile → fuel итераций
    if isinstance(expr, GWhile):
        records = []
        for _ in range(expr.fuel):
            records.extend(_compile_rec(expr.body, scope, pol, fuel))
        return records

    # gLoop — аналог gWhile
    if isinstance(expr, GLoop):
        records = []
        for _ in range(expr.fuel):
            records.extend(_compile_rec(expr.body, scope, pol, fuel))
        return records

    return []


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
        fuel: int = 1000) -> ExecutionTrace:
    """
    Основная точка входа. Запустить программу и вернуть полный след.
    """
    if context_policy is None:
        context_policy = POLICY_ZERO

    result = eval2(expr, scope, context_policy, fuel)
    records = compile2(expr, scope, context_policy, fuel)
    event7s = _extract_event7s(records, expr, context_policy)
    emits = _collect_emits(expr)

    return ExecutionTrace(
        expr=expr,
        scope=scope,
        context_policy=context_policy,
        result=result,
        records=records,
        event7s=event7s,
        emit_codes=emits
    )
