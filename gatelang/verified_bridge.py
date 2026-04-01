"""
gatelang/verified_bridge.py
----------------------------
Verified Bridge: Event7 ↔ OEvent (Ontology V2)

GOLDEN STANDARD — Gap #3: Cryptographic Connectivity
═══════════════════════════════════════════════════════════════
This module provides the Python-side verification that Event7
(7-tuple) faithfully corresponds to the OEvent structure in
Meta/OntologyV2.lean and Meta/VerifiedRuntime.lean.

Mirrors: Meta/VerifiedRuntime.lean
Author: A. A. Noh · UTE TLI SYSTEMS · DOI: 10.17605/OSF.IO/49UMB
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from .types import Event7, PolicySnapshot, EvidenceRef, Verdict, closure_gate


# ══════════════════════════════════════════════
# OEvent MODEL (mirrors Meta/OntologyV2.lean)
# ══════════════════════════════════════════════

@dataclass(frozen=True)
class OState:
    """Lean: structure OState where id : Nat"""
    id: int


@dataclass(frozen=True)
class OTransition:
    """Lean: structure OTransition where src : OState; dst : OState; diff : src ≠ dst"""
    src: OState
    dst: OState

    @property
    def valid(self) -> bool:
        return self.src.id != self.dst.id


@dataclass(frozen=True)
class OEvent:
    """Lean: structure OEvent where trans : OTransition; context : Nat"""
    trans: OTransition
    context: int


# ══════════════════════════════════════════════
# PROJECTION: Event7 → OEvent
# ══════════════════════════════════════════════

def event7_to_oevent(e: Event7) -> OEvent:
    """
    Lean: noncomputable def event7_to_oevent (e : RtEvent7) : OEvent
    Maps (S, C, X, Γ, Escalated, Ω, Λ, Π) → (transition, context)
    """
    src = OState(e.subject)
    dst = OState(e.subject + len(e.execution) + 1)
    trans = OTransition(src, dst)
    return OEvent(trans, e.context)


# ══════════════════════════════════════════════
# EMBEDDING: OEvent → Event7
# ══════════════════════════════════════════════

def oevent_to_event7(oe: OEvent) -> Event7:
    """
    Lean: def oevent_to_event7 (e : OEvent) : RtEvent7
    Lifts an ontological event to a minimal well-formed Event7.
    """
    from .types import LedgerRecord, POLICY_ZERO
    diff = abs(oe.trans.dst.id - oe.trans.src.id) - 1
    evidence = [EvidenceRef(f"bridge-ev-{i}") for i in range(max(0, diff))]
    policy = PolicySnapshot(id=0, min_evidence=0, effective_at=0)
    verdict = closure_gate(evidence, policy)
    record = LedgerRecord(
        scope=oe.context,
        verdict=verdict,
        policy=policy,
        evidence=evidence,
        closed_at=oe.context
    )
    return Event7(
        subject=oe.trans.src.id,
        context=oe.context,
        execution=evidence,
        conflict=False,
        escalated=False,
        outcome=verdict,
        ledger=record,
        policy=policy
    )


# ══════════════════════════════════════════════
# VERIFICATION THEOREMS (runtime checks)
# ══════════════════════════════════════════════

def verify_context_preservation(e7: Event7) -> bool:
    """
    Lean: theorem event7_context_preserved
    Projection preserves context: event7_to_oevent(e).context == e.context
    """
    oe = event7_to_oevent(e7)
    return oe.context == e7.context


def verify_embedding_wellformed(oe: OEvent) -> bool:
    """
    Lean: theorem oevent_to_event7_wellformed
    Embedding always produces a well-formed Event7.
    """
    e7 = oevent_to_event7(oe)
    return e7.well_formed


def verify_roundtrip_context(e7: Event7) -> bool:
    """
    Lean: theorem roundtrip_preserves_context
    Round-trip preserves context: oevent_to_event7(event7_to_oevent(e)).context == e.context
    """
    oe = event7_to_oevent(e7)
    e7_back = oevent_to_event7(oe)
    return e7_back.context == e7.context


def verify_projection_injective(e1: Event7, e2: Event7) -> bool:
    """
    Lean: theorem event7_projection_injective_on_context
    Distinct contexts → distinct OEvents.
    """
    if e1.context == e2.context:
        return True  # precondition not met
    oe1 = event7_to_oevent(e1)
    oe2 = event7_to_oevent(e2)
    return oe1 != oe2


def verify_bridge_master() -> dict:
    """
    Lean: theorem cryptographic_connectivity_master
    Run all verification checks and return results.
    """
    from .types import gate_to_7tuple, POLICY_ZERO
    
    # Build test Event7
    policy = PolicySnapshot(id=1, min_evidence=1, effective_at=0)
    evidence = [EvidenceRef("test-ev")]
    e7 = gate_to_7tuple(evidence, policy, agent_id=42, scope=100,
                        context_policy=POLICY_ZERO)
    
    # Build test OEvent
    oe = OEvent(OTransition(OState(0), OState(2)), context=200)
    
    # Build second Event7 for injectivity test
    e7_other = gate_to_7tuple(evidence, policy, agent_id=42, scope=200,
                               context_policy=POLICY_ZERO)
    
    results = {
        "context_preservation": verify_context_preservation(e7),
        "embedding_wellformed": verify_embedding_wellformed(oe),
        "roundtrip_context": verify_roundtrip_context(e7),
        "projection_injective": verify_projection_injective(e7, e7_other),
        "transition_valid": event7_to_oevent(e7).trans.valid,
    }
    results["all_passed"] = all(results.values())
    return results


if __name__ == "__main__":
    results = verify_bridge_master()
    print("═" * 60)
    print("GOLDEN STANDARD — Gap #3: Cryptographic Connectivity")
    print("Event7 ↔ OEvent Bridge Verification")
    print("═" * 60)
    for key, val in results.items():
        status = "✓ PASS" if val else "✗ FAIL"
        print(f"  {key}: {status}")
