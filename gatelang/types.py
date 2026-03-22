"""
gatelang/types.py
-----------------
Типы данных GateLang v2, точно отражающие Lean 4 определения.
Mirrors: Lang/GateLangV2.lean · Lang/GateLangE7Tuple.lean
Author: A. A. Noh · UTE TLI SYSTEMS · DOI: 10.17605/OSF.IO/49UMB
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Union
from enum import Enum


# ══════════════════════════════════════════════
# БАЗОВЫЕ ТИПЫ / BASE TYPES
# ══════════════════════════════════════════════

class Verdict(Enum):
    """Lean: inductive Verdict"""
    PASS = "pass"
    CLOSED_WITH_MISSING_EVIDENCE = "closedWithMissingEvidence"


@dataclass(frozen=True)
class EvidenceRef:
    """Lean: structure EvidenceRef"""
    ref: str

    def __str__(self):
        return f"EvidenceRef({self.ref!r})"


@dataclass(frozen=True)
class PolicySnapshot:
    """
    Lean: structure PolicySnapshot where
      id            : PolicyId
      minEvidence   : Nat
      effectiveAt   : Nat

    Политика зафиксированная на момент выполнения.
    """
    id: int
    min_evidence: int
    effective_at: int = 0

    def __str__(self):
        return f"Policy(id={self.id}, min={self.min_evidence}, eff={self.effective_at})"


@dataclass(frozen=True)
class LedgerRecord:
    """
    Lean: structure LedgerRecord where
      scope    : ScopeId
      verdict  : Verdict
      policy   : PolicySnapshot
      evidence : List EvidenceRef
      closedAt : Nat

    Неизменяемая журнальная запись.
    Инвариант: verdict = closureGate(evidence, policy).
    """
    scope: int
    verdict: Verdict
    policy: PolicySnapshot
    evidence: List[EvidenceRef]
    closed_at: int

    @property
    def valid(self) -> bool:
        """Lean: valid : verdict = closureGate evidence policy"""
        expected = closure_gate(self.evidence, self.policy)
        return self.verdict == expected

    def __str__(self):
        ev_str = f"[{', '.join(e.ref for e in self.evidence)}]"
        return (f"LedgerRecord("
                f"scope={self.scope}, "
                f"verdict={self.verdict.value}, "
                f"policy={self.policy}, "
                f"evidence={ev_str}, "
                f"closed_at={self.closed_at})")


# ══════════════════════════════════════════════
# ФУНКЦИИ ПОЛИТИКИ / POLICY FUNCTIONS
# ══════════════════════════════════════════════

# Lean: policyZero : PolicySnapshot
POLICY_ZERO = PolicySnapshot(id=0, min_evidence=0, effective_at=0)


def policy_seq(p1: PolicySnapshot, p2: PolicySnapshot) -> PolicySnapshot:
    """
    Lean: def policySeq (p1 p2 : PolicySnapshot) : PolicySnapshot
    Теорема: policySeq_stricter — результат строже обоих аргументов.
    minEvidence = max(p1.minEvidence, p2.minEvidence)
    """
    return PolicySnapshot(
        id=p1.id + p2.id,
        min_evidence=max(p1.min_evidence, p2.min_evidence),
        effective_at=max(p1.effective_at, p2.effective_at)
    )


def policy_par(p1: PolicySnapshot, p2: PolicySnapshot) -> PolicySnapshot:
    """
    Lean: def policyPar (p1 p2 : PolicySnapshot) : PolicySnapshot
    Теорема: policyPar_weaker — результат мягче обоих аргументов.
    minEvidence = min(p1.minEvidence, p2.minEvidence)
    """
    return PolicySnapshot(
        id=p1.id + p2.id,
        min_evidence=min(p1.min_evidence, p2.min_evidence),
        effective_at=min(p1.effective_at, p2.effective_at)
    )


def closure_gate(evidence: List[EvidenceRef], policy: PolicySnapshot) -> Verdict:
    """
    Lean: def closureGate (ev : List EvidenceRef) (p : PolicySnapshot) : Verdict
    Теорема: bigstep2_deterministic — детерминированная чистая функция.
    """
    if len(evidence) >= policy.min_evidence:
        return Verdict.PASS
    return Verdict.CLOSED_WITH_MISSING_EVIDENCE


def ledger_mk(scope: int, evidence: List[EvidenceRef],
              policy: PolicySnapshot, closed_at: int) -> LedgerRecord:
    """
    Lean: def LedgerRecord.mk' (scope ev policy closedAt)
    Создаёт запись с корректным вердиктом.
    """
    verdict = closure_gate(evidence, policy)
    return LedgerRecord(
        scope=scope,
        verdict=verdict,
        policy=policy,
        evidence=list(evidence),
        closed_at=closed_at
    )


# ══════════════════════════════════════════════
# ЗНАЧЕНИЯ / VALUES (GVal2)
# ══════════════════════════════════════════════

class GVal:
    """Lean: inductive GVal2"""
    pass


@dataclass(frozen=True)
class GUnit(GVal):
    """Lean: gUnit"""
    def __str__(self): return "gUnit"


@dataclass(frozen=True)
class GFact(GVal):
    """Lean: gFact (r : LedgerRecord)"""
    record: LedgerRecord
    def __str__(self): return f"gFact({self.record})"


@dataclass(frozen=True)
class GAgent(GVal):
    """Lean: gAgent (id : GAgentId)"""
    agent_id: int
    def __str__(self): return f"gAgent({self.agent_id})"


@dataclass(frozen=True)
class GRaw(GVal):
    """Lean: gRaw (n : Nat)"""
    value: int
    def __str__(self): return f"gRaw({self.value})"


@dataclass(frozen=True)
class GPair(GVal):
    """Lean: gPair (v1 v2 : GVal2)"""
    left: GVal
    right: GVal
    def __str__(self): return f"gPair({self.left}, {self.right})"


@dataclass(frozen=True)
class GLeft(GVal):
    """Lean: gLeft (v : GVal2)"""
    value: GVal
    def __str__(self): return f"gLeft({self.value})"


@dataclass(frozen=True)
class GRight(GVal):
    """Lean: gRight (v : GVal2)"""
    value: GVal
    def __str__(self): return f"gRight({self.value})"


# ══════════════════════════════════════════════
# ВЫРАЖЕНИЯ / EXPRESSIONS (GExpr2)
# ══════════════════════════════════════════════

class GExpr:
    """Lean: inductive GExpr2"""
    pass


@dataclass
class GRet(GExpr):
    """Lean: gRet (v : GVal2)"""
    value: GVal
    def __str__(self): return f"gRet({self.value})"


@dataclass
class GEmit(GExpr):
    """Lean: gEmit (n : Nat)"""
    code: int
    def __str__(self): return f"gEmit({self.code})"


@dataclass
class GGate(GExpr):
    """Lean: gGate (ev : List EvidenceRef) (p : PolicySnapshot) (ag : GAgentId)"""
    evidence: List[EvidenceRef]
    policy: PolicySnapshot
    agent_id: int

    def __str__(self):
        ev_str = f"[{', '.join(e.ref for e in self.evidence)}]"
        return f"gGate({ev_str}, {self.policy}, agent={self.agent_id})"


@dataclass
class GSeq(GExpr):
    """Lean: gSeq (e1 e2 : GExpr2)"""
    e1: GExpr
    e2: GExpr
    def __str__(self): return f"gSeq({self.e1}, {self.e2})"


@dataclass
class GGuard(GExpr):
    """Lean: gGuard (ev : List EvidenceRef) (p : PolicySnapshot) (body : GExpr2)"""
    evidence: List[EvidenceRef]
    policy: PolicySnapshot
    body: GExpr
    def __str__(self): return f"gGuard({self.policy}, {self.body})"


@dataclass
class GPar(GExpr):
    """Lean: gPar (e1 e2 : GExpr2)"""
    e1: GExpr
    e2: GExpr
    def __str__(self): return f"gPar({self.e1}, {self.e2})"


@dataclass
class GTry(GExpr):
    """Lean: gTry (e1 e2 : GExpr2)"""
    e1: GExpr
    e2: GExpr
    def __str__(self): return f"gTry({self.e1}, {self.e2})"


@dataclass
class GWith(GExpr):
    """Lean: gWith (pol : PolicySnapshot) (body : GExpr2)"""
    policy: PolicySnapshot
    body: GExpr
    def __str__(self): return f"gWith({self.policy}, {self.body})"


@dataclass
class GWhile(GExpr):
    """Lean: gWhile (fuel : Nat) (body : GExpr2)"""
    fuel: int
    body: GExpr
    def __str__(self): return f"gWhile(fuel={self.fuel}, {self.body})"


@dataclass
class GLoop(GExpr):
    """Lean: gLoop (fuel : Nat) (body : GExpr2)"""
    fuel: int
    body: GExpr
    def __str__(self): return f"gLoop(fuel={self.fuel}, {self.body})"


# ══════════════════════════════════════════════
# 7-TUPLE / EVENT7
# ══════════════════════════════════════════════

@dataclass
class Event7:
    """
    Lean: structure Event7 where
      subject   : GAgentId   -- S
      context   : GScopeId   -- C
      execution : List EvidenceRef  -- X
      conflict  : Bool        -- Γ
      escalated : Bool        -- Escalated=0
      outcome   : Verdict     -- Ω
      ledger    : LedgerRecord -- Λ
      policy    : PolicySnapshot -- Π

    Теорема: gatelang_is_7tuple_lang
    """
    subject: int           # S
    context: int           # C
    execution: List[EvidenceRef]  # X
    conflict: bool         # Γ
    escalated: bool        # Escalated=0 (всегда False)
    outcome: Verdict       # Ω
    ledger: LedgerRecord   # Λ
    policy: PolicySnapshot # Π

    @property
    def well_formed(self) -> bool:
        """
        Lean: def Event7.WellFormed (e : Event7) : Prop :=
          e.outcome = closureGate e.execution e.policy ∧
          e.escalated = false ∧
          e.ledger.policy = e.policy ∧
          e.ledger.verdict = e.outcome
        """
        return (
            self.outcome == closure_gate(self.execution, self.policy)
            and not self.escalated
            and self.ledger.policy == self.policy
            and self.ledger.verdict == self.outcome
        )

    def __str__(self):
        return (f"Event7(\n"
                f"  S={self.subject}, C={self.context},\n"
                f"  X=[{', '.join(e.ref for e in self.execution)}],\n"
                f"  Γ={self.conflict}, Escalated={self.escalated},\n"
                f"  Ω={self.outcome.value},\n"
                f"  Π={self.policy},\n"
                f"  well_formed={self.well_formed}\n"
                f")")


def gate_to_7tuple(evidence: List[EvidenceRef], policy: PolicySnapshot,
                   agent_id: int, scope: int,
                   context_policy: PolicySnapshot) -> Event7:
    """
    Lean: def gate_to_7tuple ev p ag t pol : Event7
    Теорема: gate_7tuple_wellformed — всегда well-formed.
    """
    eff_policy = policy_seq(context_policy, policy)
    verdict = closure_gate(evidence, eff_policy)
    record = ledger_mk(scope, evidence, eff_policy, scope)
    return Event7(
        subject=agent_id,
        context=scope,
        execution=list(evidence),
        conflict=False,
        escalated=False,
        outcome=verdict,
        ledger=record,
        policy=eff_policy
    )


# ══════════════════════════════════════════════
# ТИПЫ ВЫРАЖЕНИЙ / EXPRESSION TYPES (GType2)
# ══════════════════════════════════════════════

class GType:
    """Lean: inductive GType2"""
    pass


@dataclass(frozen=True)
class TUnit(GType):
    def __str__(self): return "TUnit"


@dataclass(frozen=True)
class TFact(GType):
    policy: PolicySnapshot
    def __str__(self): return f"TFact({self.policy})"


@dataclass(frozen=True)
class TAgent(GType):
    def __str__(self): return "TAgent"


@dataclass(frozen=True)
class TRaw(GType):
    def __str__(self): return "TRaw"


@dataclass(frozen=True)
class TPair(GType):
    left: GType
    right: GType
    def __str__(self): return f"TPair({self.left}, {self.right})"


@dataclass(frozen=True)
class TLeft(GType):
    inner: GType
    def __str__(self): return f"TLeft({self.inner})"


@dataclass(frozen=True)
class TRight(GType):
    inner: GType
    def __str__(self): return f"TRight({self.inner})"


@dataclass(frozen=True)
class TGuarded(GType):
    policy: PolicySnapshot
    inner: GType
    def __str__(self): return f"TGuarded({self.policy}, {self.inner})"


@dataclass(frozen=True)
class TWith(GType):
    policy: PolicySnapshot
    inner: GType
    def __str__(self): return f"TWith({self.policy}, {self.inner})"


def type_of_val(v: GVal) -> GType:
    """Lean: def gtypeOf2 : GVal2 → GType2"""
    if isinstance(v, GUnit):
        return TUnit()
    elif isinstance(v, GFact):
        return TFact(v.record.policy)
    elif isinstance(v, GAgent):
        return TAgent()
    elif isinstance(v, GRaw):
        return TRaw()
    elif isinstance(v, GPair):
        return TPair(type_of_val(v.left), type_of_val(v.right))
    elif isinstance(v, GLeft):
        return TLeft(type_of_val(v.value))
    elif isinstance(v, GRight):
        return TRight(type_of_val(v.value))
    raise TypeError(f"Unknown GVal: {type(v)}")
