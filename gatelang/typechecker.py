"""
gatelang/typechecker.py
------------------------
Система типов GateLang v2.
Mirrors: Lang/GateLangTypesV2.lean
Author: A. A. Noh · UTE TLI SYSTEMS · DOI: 10.17605/OSF.IO/49UMB

Теоремы:
  progress_gate_v2  — типизированный gGate не застревает
  try_type_safety   — обе ветки gTry одного типа
  while_always_unit — gWhile всегда TUnit
  tfact_neq_tunit   — TFact ≠ TUnit
"""

from __future__ import annotations
from typing import Dict, Optional, Tuple, List
from .types import (
    GExpr, GRet, GEmit, GGate, GSeq, GGuard, GPar, GTry, GWith, GWhile, GLoop,
    GVal, GUnit, GFact, GAgent, GRaw, GPair, GLeft, GRight,
    GType, TUnit, TFact, TAgent, TRaw, TPair, TLeft, TRight, TGuarded, TWith,
    PolicySnapshot, POLICY_ZERO, policy_seq, type_of_val
)

# Контекст типизации
GCtx = Dict[int, GType]


class TypeCheckError(Exception):
    """Ошибка типизации."""
    pass


def typecheck(expr: GExpr,
              ctx: Optional[GCtx] = None,
              context_policy: Optional[PolicySnapshot] = None) -> GType:
    """
    Lean: inductive GTyping2 : GCtx2 → GExpr2 → GType2 → Prop

    Возвращает тип выражения или бросает TypeCheckError.
    """
    if ctx is None:
        ctx = {}
    if context_policy is None:
        context_policy = POLICY_ZERO

    return _tc(expr, ctx, context_policy)


def _tc(expr: GExpr, ctx: GCtx, pol: PolicySnapshot) -> GType:

    # T-Ret: gRet v → type of v
    if isinstance(expr, GRet):
        return type_of_val(expr.value)

    # T-Emit: gEmit n → TUnit
    if isinstance(expr, GEmit):
        return TUnit()

    # T-Gate-Pass / T-Gate-Fail
    if isinstance(expr, GGate):
        eff_policy = policy_seq(pol, expr.policy)
        if len(expr.evidence) >= eff_policy.min_evidence:
            return TFact(eff_policy)
        else:
            return TUnit()

    # T-Seq: gSeq e1 e2 → type of e2
    if isinstance(expr, GSeq):
        _tc(expr.e1, ctx, pol)  # проверяем e1
        return _tc(expr.e2, ctx, pol)

    # T-Guard
    if isinstance(expr, GGuard):
        eff_policy = policy_seq(pol, expr.policy)
        if len(expr.evidence) >= eff_policy.min_evidence:
            body_type = _tc(expr.body, ctx, pol)
            return TGuarded(eff_policy, body_type)
        return TUnit()

    # T-Par: gPar e1 e2 → TPair(τ1, τ2)
    # Теорема: par_type_safety
    if isinstance(expr, GPar):
        t1 = _tc(expr.e1, ctx, pol)
        t2 = _tc(expr.e2, ctx, pol)
        return TPair(t1, t2)

    # T-Try: обе ветки должны иметь одинаковый тип τ
    # Теорема: try_type_safety
    if isinstance(expr, GTry):
        t1 = _tc(expr.e1, ctx, pol)
        t2 = _tc(expr.e2, ctx, pol)
        if type(t1) != type(t2):
            raise TypeCheckError(
                f"gTry: ветки имеют разные типы: {t1} vs {t2}\n"
                f"Теорема try_type_safety требует одинаковый τ для обеих веток."
            )
        return t1

    # T-With: gWith pol body → TWith(pol, type of body)
    # Теорема: with_type_safe, with_policy_stricter
    if isinstance(expr, GWith):
        local_pol = policy_seq(pol, expr.policy)
        body_type = _tc(expr.body, ctx, local_pol)
        return TWith(expr.policy, body_type)

    # T-While: gWhile n body → TUnit
    # Теорема: while_always_unit
    if isinstance(expr, GWhile):
        _tc(expr.body, ctx, pol)  # проверяем тело
        return TUnit()

    # T-Loop: gLoop n body → TUnit
    if isinstance(expr, GLoop):
        _tc(expr.body, ctx, pol)
        return TUnit()

    raise TypeCheckError(f"Неизвестное выражение: {type(expr)}")


def typecheck_safe(expr: GExpr,
                   ctx: Optional[GCtx] = None,
                   context_policy: Optional[PolicySnapshot] = None
                   ) -> Tuple[Optional[GType], Optional[str]]:
    """
    Безопасная версия typecheck.
    Возвращает (тип, None) или (None, сообщение об ошибке).
    """
    try:
        t = typecheck(expr, ctx, context_policy)
        return t, None
    except TypeCheckError as e:
        return None, str(e)


def verify_program(expr: GExpr,
                   context_policy: Optional[PolicySnapshot] = None
                   ) -> Tuple[bool, Optional[GType], Optional[str]]:
    """
    Полная верификация программы.
    Возвращает (ok, тип, ошибка).

    Если ok=True: программа типизируется, теорема soundness применима.
    """
    t, err = typecheck_safe(expr, {}, context_policy)
    if err is not None:
        return False, None, err
    return True, t, None
