"""
examples/basic.py
-----------------
Базовые примеры GateLang.
Глава 3 учебника: gGate, gSeq, gEmit, gRet.
"""

from gatelang import (
    PolicySnapshot, EvidenceRef, POLICY_ZERO,
    GGate, GSeq, GEmit, GRet, GUnit,
    run, verify_program
)

print("═" * 60)
print("Пример 1: Базовая верификация / Basic verification")
print("═" * 60)

# Политика: нужно 2 доказательства
policy = PolicySnapshot(id=1, min_evidence=2, effective_at=0)

# Пример A: достаточно доказательств → gFact
ev_ok = [EvidenceRef("doc-A"), EvidenceRef("doc-B")]
prog_pass = GGate(ev_ok, policy, agent_id=42)

print("\n── Программа A: gate pass ──")
ok, typ, err = verify_program(prog_pass)
print(f"Типизация: {'✓ OK' if ok else '✗ FAIL'}, тип = {typ}")
result = run(prog_pass, scope=100)
print(result.summary())

# Пример B: недостаточно доказательств → gUnit
ev_fail = [EvidenceRef("doc-A")]
prog_fail = GGate(ev_fail, policy, agent_id=42)

print("\n── Программа B: gate fail ──")
result = run(prog_fail, scope=100)
print(result.summary())

print("\n═" * 60)
print("Пример 2: Последовательность / Sequential (gSeq)")
print("═" * 60)

# gSeq: уведомление + верификация
prog_seq = GSeq(
    GEmit(7),                        # уведомление с кодом 7
    GGate(ev_ok, policy, agent_id=1)  # верификация
)

print("\n── Программа: gEmit → gGate ──")
ok, typ, err = verify_program(prog_seq)
print(f"Типизация: {'✓ OK' if ok else '✗ FAIL'}, тип = {typ}")
result = run(prog_seq, scope=200)
print(result.summary())

print("\n═" * 60)
print("Пример 3: gRet — возврат значения")
print("═" * 60)

prog_ret = GRet(GUnit())
result = run(prog_ret)
print(f"Результат: {result.result}")
print(f"Записей: {len(result.records)}")
