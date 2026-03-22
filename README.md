# GateLang Runtime v0.1.0

Верифицированный DSL для аудируемых систем.  
**A. A. Noh · UTE TLI SYSTEMS · DOI: 10.17605/OSF.IO/49UMB**

Lean 4 верификация: [github.com/alpindiay/lean4-ute-tli](https://github.com/alpindiay/lean4-ute-tli)  
1138 верифицированных утверждений · 0 sorry · Lean 4 v4.29.0-rc6

---

## Быстрый старт

```bash
# Запустить примеры
python runtime.py demo

# Интерактивный REPL
python runtime.py repl

# Запустить конкретный пример
python runtime.py run examples/basic.py
```

## Установка зависимостей

Зависимостей нет. Только Python 3.8+.

---

## Пример программы

```python
from gatelang import *

# Политика: нужно 2 доказательства
policy = PolicySnapshot(id=1, min_evidence=2, effective_at=0)

# Доказательства
evidence = [EvidenceRef("doc-A"), EvidenceRef("doc-B")]

# Программа
prog = GGate(evidence, policy, agent_id=42)

# Типизация (до выполнения)
ok, typ, err = verify_program(prog)
print(f"Тип: {typ}")  # TFact(Policy(...))

# Выполнение
result = run(prog, scope=100)
print(result.summary())
```

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

## Гарантии

Все гарантии машинно доказаны в Lean 4:

| Теорема | Гарантия |
|---|---|
| `bigstep2_deterministic` | Один вход → один выход |
| `gatelang_soundness_v2_master` | Типизированные программы → корректные факты |
| `no_spurious_facts` | GEmit не создаёт записей |
| `gatelang_is_7tuple_lang` | Каждый GGate → well-formed 7-tuple |
| `policy_algebra_master` | PolicySnapshot образует моноид |
| `no_infinite_descent` | Иерархия событий well-founded |

## 7-tuple E=(S,C,X,Γ,Ω,Λ,Π)

```python
from gatelang import gate_to_7tuple, EvidenceRef, PolicySnapshot, POLICY_ZERO

e7 = gate_to_7tuple(
    evidence=[EvidenceRef("sig")],
    policy=PolicySnapshot(id=1, min_evidence=1, effective_at=0),
    agent_id=42,
    scope=0,
    context_policy=POLICY_ZERO
)
print(e7.well_formed)  # True — теорема gate_7tuple_wellformed
```

## Структура репозитория

```
gatelang-runtime/
  gatelang/
    __init__.py    — публичный API
    types.py       — GVal, GExpr, PolicySnapshot, LedgerRecord, Event7
    semantics.py   — eval2, compile2, run, gstep2
    typechecker.py — typecheck, verify_program
    repl.py        — интерактивный REPL
  examples/
    basic.py       — gGate, gSeq, gEmit, gRet
    advanced.py    — gPar, gTry, gWith, gWhile
    seven_tuple.py — 7-tuple и soundness
  runtime.py       — CLI точка входа
  README.md
```

---

*GateLang Runtime — Python реализация семантики Lean 4 модулей  
Lang/GateLangV2.lean, Lang/GateLangSemanticsV2.lean, Lang/GateLangE7Tuple.lean*

## GateLang Runtime (Python)
**[github.com/alpindiay/gatelang-runtime-](https://github.com/alpindiay/gatelang-runtime-)** — Python implementation of GateLang v2. No dependencies, Python 3.8+.

## GateLang Runtime (Python)
**[github.com/alpindiay/gatelang-runtime-](https://github.com/alpindiay/gatelang-runtime-)** — Python implementation of GateLang v2. No dependencies, Python 3.8+.
