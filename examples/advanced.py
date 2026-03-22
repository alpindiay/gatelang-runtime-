"""
examples/advanced.py
---------------------
Продвинутые конструкции GateLang v2.
Главы 5–8 учебника: gPar, gTry, gWith, gWhile.
"""

from gatelang import (
    PolicySnapshot, EvidenceRef, POLICY_ZERO, policy_seq,
    GGate, GSeq, GEmit, GRet, GUnit, GRaw,
    GPar, GTry, GWith, GWhile, GLoop,
    run, verify_program, typecheck
)

print("═" * 60)
print("Пример 4: Параллельная верификация / gPar")
print("═" * 60)

policy = PolicySnapshot(id=1, min_evidence=1, effective_at=0)
ev1 = [EvidenceRef("alice-sign")]
ev2 = [EvidenceRef("bob-sign")]

# Два агента параллельно
prog_par = GPar(
    GGate(ev1, policy, agent_id=1),  # Alice
    GGate(ev2, policy, agent_id=2)   # Bob
)

ok, typ, err = verify_program(prog_par)
print(f"Тип: {typ}")
result = run(prog_par, scope=10)
print(result.summary())

print("\n── Три агента / Three agents ──")
ev3 = [EvidenceRef("carol-sign")]
prog_par3 = GPar(
    prog_par,
    GGate(ev3, policy, agent_id=3)
)
result3 = run(prog_par3, scope=10)
print(result3.summary())


print("\n═" * 60)
print("Пример 5: Обработка ошибок / gTry")
print("═" * 60)

strict_policy = PolicySnapshot(id=2, min_evidence=3, effective_at=0)
relaxed_policy = PolicySnapshot(id=3, min_evidence=1, effective_at=0)
ev_minimal = [EvidenceRef("minimal")]

# Пытаемся строгую политику, fallback на мягкую
prog_try = GTry(
    GGate(ev_minimal, strict_policy, agent_id=10),   # fail (нужно 3)
    GGate(ev_minimal, relaxed_policy, agent_id=10)   # pass (нужно 1)
)

ok, typ, err = verify_program(prog_try)
print(f"Тип: {typ}")
result = run(prog_try, scope=20)
print(result.summary())


print("\n═" * 60)
print("Пример 6: Локальная политика / gWith")
print("═" * 60)

base_policy = PolicySnapshot(id=4, min_evidence=1, effective_at=0)
strict_local = PolicySnapshot(id=5, min_evidence=2, effective_at=0)
ev_two = [EvidenceRef("d1"), EvidenceRef("d2")]

# gWith ужесточает политику
prog_with = GWith(
    strict_local,
    GGate(ev_two, base_policy, agent_id=99)
)

ok, typ, err = verify_program(prog_with)
print(f"Тип: {typ}")

# Эффективная политика = policySeq(POLICY_ZERO, strict_local) ужесточает base_policy
eff = policy_seq(POLICY_ZERO, strict_local)
print(f"Контекстная политика: {POLICY_ZERO}")
print(f"Локальная политика:   {strict_local}")
print(f"Эффективная политика: {eff} (строже)")
result = run(prog_with, scope=30)
print(result.summary())


print("\n═" * 60)
print("Пример 7: Цикл / gWhile")
print("═" * 60)

tick_policy = PolicySnapshot(id=6, min_evidence=1, effective_at=0)
ev_tick = [EvidenceRef("heartbeat")]

# 3 итерации верификации
prog_while = GWhile(3, GGate(ev_tick, tick_policy, agent_id=0))
ok, typ, err = verify_program(prog_while)
print(f"Тип: {typ}")  # всегда TUnit
result = run(prog_while, scope=40)
print(result.summary())
print(f"\nЗаписей создано: {len(result.records)} (по одной на итерацию)")


print("\n═" * 60)
print("Пример 8: Комбинированная программа / Combined")
print("═" * 60)

# Многоагентный аудит с параллелизмом и fallback
audit_policy = PolicySnapshot(id=7, min_evidence=2, effective_at=100)
ev_full = [EvidenceRef("sig-main"), EvidenceRef("sig-backup")]
ev_lite = [EvidenceRef("sig-main")]

prog_audit = GSeq(
    GEmit(1000),  # уведомление: начало аудита
    GPar(
        GTry(
            GGate(ev_full, audit_policy, agent_id=1),
            GGate(ev_lite, PolicySnapshot(id=8, min_evidence=1, effective_at=100), agent_id=1)
        ),
        GGate(ev_full, audit_policy, agent_id=2)
    )
)

ok, typ, err = verify_program(prog_audit)
print(f"Тип: {typ}")
result = run(prog_audit, scope=50)
print(result.summary())
