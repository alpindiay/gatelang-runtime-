"""
GateLang Runtime v0.1.0
-----------------------
Верифицированный DSL для аудируемых систем.
Author: A. A. Noh · UTE TLI SYSTEMS · DOI: 10.17605/OSF.IO/49UMB
Lean 4: github.com/alpindiay/lean4-ute-tli
"""

from .types import (
    # Политики
    PolicySnapshot, POLICY_ZERO, policy_seq, policy_par,
    # Доказательства
    EvidenceRef,
    # Вердикт
    Verdict,
    # Журнальная запись
    LedgerRecord, ledger_mk, closure_gate,
    # Значения
    GVal, GUnit, GFact, GAgent, GRaw, GPair, GLeft, GRight,
    # Выражения
    GExpr, GRet, GEmit, GGate, GSeq, GGuard, GPar, GTry, GWith, GWhile, GLoop,
    # Типы
    GType, TUnit, TFact, TAgent, TRaw, TPair, TWith, TGuarded,
    type_of_val,
    # 7-tuple
    Event7, gate_to_7tuple,
)

from .semantics import (
    eval2, compile2, run, gstep2,
    ExecutionTrace,
    GResult, GDone, GCont, GStuck, GError,
)

from .typechecker import (
    typecheck, typecheck_safe, verify_program,
    TypeCheckError,
)

__version__ = "0.1.0"
__all__ = [
    # Политики
    "PolicySnapshot", "POLICY_ZERO", "policy_seq", "policy_par",
    # Доказательства
    "EvidenceRef",
    # Вердикт
    "Verdict",
    # Журнал
    "LedgerRecord", "ledger_mk", "closure_gate",
    # Значения
    "GUnit", "GFact", "GAgent", "GRaw", "GPair", "GLeft", "GRight",
    # Выражения
    "GRet", "GEmit", "GGate", "GSeq", "GGuard", "GPar", "GTry", "GWith", "GWhile", "GLoop",
    # Типы
    "TUnit", "TFact", "TAgent", "TRaw", "TPair", "TWith",
    # 7-tuple
    "Event7", "gate_to_7tuple",
    # Runtime
    "eval2", "compile2", "run",
    "GDone", "GStuck", "GError",
    # Typechecker
    "typecheck", "typecheck_safe", "verify_program", "TypeCheckError",
]
