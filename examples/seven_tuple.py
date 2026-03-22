"""
examples/seven_tuple.py
------------------------
Демонстрация 7-tuple и soundness.
Глава 9–10 учебника.
Теорема: gatelang_is_7tuple_lang
"""

from gatelang import (
    PolicySnapshot, EvidenceRef, POLICY_ZERO, policy_seq,
    GGate, GPar, GSeq, GEmit,
    run, verify_program, compile2,
    gate_to_7tuple, Event7, Verdict
)

print("═" * 60)
print("Пример 9: 7-tuple E=(S,C,X,Γ,Ω,Λ,Π)")
print("═" * 60)

policy = PolicySnapshot(id=42, min_evidence=2, effective_at=1000)
evidence = [EvidenceRef("contract-hash"), EvidenceRef("signature")]

# Получить 7-tuple напрямую
e7 = gate_to_7tuple(
    evidence=evidence,
    policy=policy,
    agent_id=7,
    scope=999,
    context_policy=POLICY_ZERO
)

print("\n── 7-tuple структура ──")
print(f"S (Subject/Агент):   {e7.subject}")
print(f"C (Context/Контекст):{e7.context}")
print(f"X (Evidence):        {[r.ref for r in e7.execution]}")
print(f"Γ (Conflict):        {e7.conflict}")
print(f"  Escalated:         {e7.escalated}  ← всегда False (теорема tuple_not_escalated)")
print(f"Ω (Outcome):         {e7.outcome.value}")
print(f"Π (Policy):          {e7.policy}")
print(f"Λ (Ledger):          {e7.ledger}")
print(f"\nWell-formed: {e7.well_formed}  ← теорема gate_7tuple_wellformed")


print("\n═" * 60)
print("Пример 10: Soundness — типизация гарантирует корректность")
print("═" * 60)

policy_ok = PolicySnapshot(id=1, min_evidence=1, effective_at=0)
ev = [EvidenceRef("proof-doc")]

prog = GGate(ev, policy_ok, agent_id=42)

# Типизация
ok, typ, err = verify_program(prog)
print(f"\n1. Типизация: {'✓ PASS' if ok else '✗ FAIL'}")
print(f"   Тип: {typ}")

# Выполнение
result = run(prog, scope=0)
print(f"\n2. Выполнение: результат = {result.result}")

# Soundness: все записи корректны
print(f"\n3. Soundness проверка:")
for i, r in enumerate(result.records):
    valid = r.valid  # r.verdict == closureGate(r.evidence, r.policy)
    print(f"   Запись [{i}]: verdict={r.verdict.value}, valid={valid}")
    print(f"   ← теорема gatelang_soundness_v2_master")

# emit не создаёт записей
from gatelang import GEmit
prog_emit = GEmit(42)
records_emit = compile2(prog_emit, 0, POLICY_ZERO, 10)
print(f"\n4. no_spurious_facts: compile2(gEmit 42) = {records_emit}")
print(f"   ← теорема no_spurious_facts: compile2 (gEmit n) t pol 1 = []")


print("\n═" * 60)
print("Пример 11: Policy Algebra моноид")
print("═" * 60)

p1 = PolicySnapshot(id=1, min_evidence=2, effective_at=0)
p2 = PolicySnapshot(id=2, min_evidence=5, effective_at=0)
p_zero = POLICY_ZERO

# policySeq строже обоих
p_seq = policy_seq(p1, p2)
print(f"\npolicySeq({p1}, {p2})")
print(f"  = {p_seq}")
print(f"  minEvidence = max(2,5) = {p_seq.min_evidence}  ← теорема policySeq_stricter")

# policyZero — нейтральный элемент
p_neutral = policy_seq(p_zero, p1)
print(f"\npolicySeq(policyZero, {p1})")
print(f"  = {p_neutral}")
print(f"  minEvidence = {p_neutral.min_evidence} = {p1.min_evidence}  ← левый нейтраль")

# Ассоциативность
p3 = PolicySnapshot(id=3, min_evidence=3, effective_at=0)
left_assoc = policy_seq(policy_seq(p1, p2), p3)
right_assoc = policy_seq(p1, policy_seq(p2, p3))
print(f"\nАссоциативность: policy_algebra_master")
print(f"  (p1 ⋅ p2) ⋅ p3: minEv = {left_assoc.min_evidence}")
print(f"  p1 ⋅ (p2 ⋅ p3): minEv = {right_assoc.min_evidence}")
print(f"  Равны: {left_assoc.min_evidence == right_assoc.min_evidence}")
