# GateLang Runtime v0.1.0

Верифицированный DSL для аудируемых систем управления действиями.  
**A. A. Noh · UTE TLI SYSTEMS · DOI: 10.17605/OSF.IO/49UMB**

Lean 4 верификация: [github.com/alpindiay/lean4-ute-tli](https://github.com/alpindiay/lean4-ute-tli)  
**1173 верифицированных утверждений · 0 sorry · Lean 4 v4.29.0-rc6**

---

## Быстрый старт
```bash
# Запустить примеры
python runtime.py demo

# Интерактивный REPL
python runtime.py repl

# Тесты
python -m pytest tests/ -v
```

Зависимостей нет. Только Python 3.8+.

---

## Пример программы
```python
from gatelang import *

# Политика: нужно 2 доказательства
policy = PolicySnapshot(id=1, min_evidence=2, effective_at=0)
evidence = [EvidenceRef("doc-A"), EvidenceRef("doc-B")]

# Типизация до выполнения
prog = GGate(evidence, policy, agent_id=42)
ok, typ, err = verify_program(prog)
print(f"Тип: {typ}")  # TFact(Policy(...))

# Выполнение
result = run(prog, scope=100)
print(result.summary())
```

---

## GateLangInterpreter — интерпретатор с состоянием
```python
from gatelang import GateLangInterpreter, PolicySnapshot, EvidenceRef, GGate, GSeq, GEmit

interp = GateLangInterpreter(scope=1, fuel=10000)

pol = PolicySnapshot(id=1, min_evidence=2, effective_at=0)
ev  = [EvidenceRef("a"), EvidenceRef("b")]

# Выполнение с типизацией
t1 = interp.execute(GGate(ev, pol, agent_id=1))
t2 = interp.execute(GGate(ev, pol, agent_id=2))

# Персистентный журнал
print(f"Всего записей: {len(interp.get_ledger())}")  # 2
print(interp)  # InterpreterState(scope=1, records=2, steps=2)

# Смена политики
interp.set_policy(PolicySnapshot(id=2, min_evidence=3, effective_at=0))

# Сброс журнала (без сброса политики)
interp.reset()
```

---

## Конструкции языка

| Конструкция | Тип результата | Назначение |
|---|---|---|
| `GRet(v)` | тип v | Возврат значения |
| `GEmit(n)` | TUnit | Уведомление (без записи) |
| `GGate(ev, pol, ag)` | TFact(pol) / TUnit | Верификация с доказательствами |
| `GSeq(e1, e2)` | тип e2 | Последовательность |
| `GPar(e1, e2)` | TPair(τ1, τ2) | Параллельное выполнение |
| `GTry(e1, e2)` | τ (одинаковый) | Обработка ошибок |
| `GWith(pol, e)` | TWith(pol, τ) | Локальная политика |
| `GWhile(n, e)` | TUnit | Цикл n итераций |
| `GLoop(n, e)` | TUnit | Повторение n раз |
| `GGuard(ev, pol, e)` | TGuarded(pol, τ) | Условное выполнение |

---

## Система типов
```python
from gatelang.typechecker import verify_program, typecheck
from gatelang.types import TFact, TUnit, TPair

# Прямая типизация
typ = typecheck(GGate(ev, pol, agent_id=1))
print(typ)  # TFact(Policy(id=1, min=2, eff=0))

# Безопасная типизация
ok, typ, err = verify_program(GSeq(GGate(ev, pol, 1), GRet(GRaw(42))))
# ok=True, typ=TRaw

# gTry: обе ветки должны иметь одинаковый тип
try:
    typecheck(GTry(GGate(ev, pol, 1), GRet(GRaw(0))))
except TypeCheckError as e:
    print(e)  # ветки имеют разные типы: TFact vs TRaw
```

---

## Алгебра политик
```python
from gatelang.types import policy_seq, policy_par, PolicySnapshot

p1 = PolicySnapshot(id=1, min_evidence=2, effective_at=0)
p2 = PolicySnapshot(id=2, min_evidence=3, effective_at=0)

# policySeq: строже обоих (Lean: policySeq_stricter)
ps = policy_seq(p1, p2)
print(ps.min_evidence)  # 3 = max(2, 3)

# policyPar: мягче обоих (Lean: policyPar_weaker)
pp = policy_par(p1, p2)
print(pp.min_evidence)  # 2 = min(2, 3)

# gWith применяет строгую политику локально
prog = GWith(p2, GGate(ev, p1, agent_id=1))
# Эффективная политика = policy_seq(p2, p1), min=3
```

---

## 7-tuple E=(S,C,X,Γ,Ω,Λ,Π)

Каждый `gGate` pass производит well-formed 7-tuple (теорема `gatelang_is_7tuple_lang`):
```python
from gatelang.types import gate_to_7tuple, POLICY_ZERO

e7 = gate_to_7tuple(
    evidence=[EvidenceRef("sig")],
    policy=PolicySnapshot(id=1, min_evidence=1, effective_at=0),
    agent_id=42,
    scope=0,
    context_policy=POLICY_ZERO
)
print(e7.well_formed)  # True — теорема gate_7tuple_wellformed
print(e7.escalated)    # False — теорема bigstep2_escalated_false
```

Поля 7-tuple:

| Поле | Обозначение | Значение |
|---|---|---|
| `subject` | S | Агент-исполнитель |
| `context` | C | Scope идентификатор |
| `execution` | X | Список доказательств |
| `conflict` | Γ | Флаг конфликта |
| `escalated` | — | Всегда False |
| `outcome` | Ω | Вердикт (pass / fail) |
| `ledger` | Λ | LedgerRecord |
| `policy` | Π | PolicySnapshot |

---

## Гарантии

Все гарантии машинно доказаны в Lean 4 (0 sorry):

| Теорема | Гарантия |
|---|---|
| `bigstep2_deterministic` | Один вход → один выход |
| `eval2_monotone` | Больше топлива → тот же результат |
| `gatelang_soundness_v2_master` | Типизированные программы → корректные факты |
| `no_spurious_facts` | GEmit не создаёт LedgerRecord |
| `gatelang_is_7tuple_lang` | Каждый GGate → well-formed 7-tuple |
| `policy_algebra_master` | PolicySnapshot образует моноид |
| `cross_framework_bridge_master` | GateLang ↔ TLI формально связаны |
| `ledger_deterministic` | Одни входы → один вердикт |

---

## Тестирование
```bash
# Запустить все тесты
python -m pytest tests/ -v

# Результат: 20 passed in 0.02s
```

Тесты в `tests/test_semantics.py` зеркалят теоремы Lean 4:
- `test_gate_pass` ← `bigstep2_deterministic`
- `test_emit_no_record` ← `no_spurious_facts`
- `test_eval2_monotone` ← `eval2_monotone`
- `test_7tuple_wellformed` ← `gate_7tuple_wellformed`

---


## REST API
```bash
# Установить Flask
pip3 install flask

# Запустить сервер
python3 -c "from gatelang.server import start_server; start_server()"
# → http://127.0.0.1:8080
```

| Endpoint | Метод | Описание |
|---|---|---|
| `/health` | GET | Health check |
| `/info` | GET | Runtime info (1260 теорем, 0 sorry) |
| `/run` | POST | Выполнить программу → LedgerRecord + 7-tuple |
| `/typecheck` | POST | Проверить типы без выполнения |
| `/compile` | POST | Скомпилировать → список LedgerRecord |
| `/batch` | POST | Выполнить несколько программ сразу |

Пример:
```bash
curl -X POST http://127.0.0.1:8080/run \
  -H "Content-Type: application/json" \
  -d '{"expr": {"type": "gGate", "evidence": [{"ref": "doc-1"}, {"ref": "doc-2"}], "policy": {"id": 1, "min_evidence": 2, "effective_at": 0}, "agent_id": 42}, "scope": 100}'
```

## Структура репозитория
```
gatelang-runtime/
  gatelang/
    __init__.py      — публичный API
    types.py         — GVal, GExpr, PolicySnapshot, LedgerRecord, Event7
    semantics.py     — eval2, compile2, run, gstep2
    typechecker.py   — typecheck, verify_program
    interpreter.py   — GateLangInterpreter (stateful)
    repl.py          — интерактивный REPL
  examples/
    basic.py         — gGate, gSeq, gEmit, gRet
    advanced.py      — gPar, gTry, gWith, gWhile
    seven_tuple.py   — 7-tuple и soundness
  tests/
    test_semantics.py — 20 тестов, зеркало Lean 4 теорем
  runtime.py         — CLI точка входа
  README.md
```

---

*GateLang Runtime — Python реализация семантики Lean 4 модулей  
`Lang/GateLangV2.lean`, `Lang/GateLangSemanticsV2.lean`, `Lang/GateLangE7Tuple.lean`*
