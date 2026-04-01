"""
gatelang/interpreter.py
GateLangInterpreter — интерпретатор с состоянием между вызовами.
Зеркалит eval2 из Lean 4, но с персистентным журналом.
"""
from __future__ import annotations
from typing import List, Optional, Dict
from dataclasses import dataclass, field
from .types import (
    GVal, GUnit, GFact, LedgerRecord, PolicySnapshot, EvidenceRef,
    POLICY_ZERO
)
from .semantics import eval2, compile2, run, ExecutionTrace
from .typechecker import verify_program, GType


@dataclass
class InterpreterState:
    """Персистентное состояние интерпретатора.

    Hash-Chain Invariant:
      Каждая новая LedgerRecord содержит prev_hash — SHA-256 хэш
      предыдущей записи. Это обеспечивает целостность и неизменяемость
      журнала (tamper-evidence для суда/регулятора).
    """
    scope: int = 0
    context_policy: PolicySnapshot = field(default_factory=lambda: POLICY_ZERO)
    ledger: List[LedgerRecord] = field(default_factory=list)
    history: List[ExecutionTrace] = field(default_factory=list)
    fuel: int = 10000
    current_hash: str = ""  # Текущий хвост hash-chain

    @property
    def total_records(self) -> int:
        return len(self.ledger)

    @property
    def chain_head(self) -> str:
        """Хэш последней записи в chain (или "" если пусто)."""
        return self.current_hash

    def verify_chain_integrity(self) -> bool:
        """Проверить целостность всей hash-chain.

        Returns:
            True если цепочка prev_hash корректна от начала до конца.
        """
        expected_hash = ""
        for record in self.ledger:
            if record.prev_hash != expected_hash:
                return False
            expected_hash = record.compute_hash()
        return expected_hash == self.current_hash or (not self.ledger and self.current_hash == "")

    def summary(self) -> str:
        chain_status = "OK" if self.verify_chain_integrity() else "BROKEN"
        hash_preview = self.current_hash[:8] + "..." if self.current_hash else "∅"
        return (f"InterpreterState("
                f"scope={self.scope}, "
                f"policy={self.context_policy}, "
                f"records={self.total_records}, "
                f"steps={len(self.history)}, "
                f"chain={hash_preview}[{chain_status}])")


class GateLangInterpreter:
    """
    Интерпретатор GateLang с персистентным состоянием.

    Зеркалит eval2 из Lean 4:
      eval2 e t pol fuel : Option GVal2

    Добавляет:
      - персистентный журнал (ledger)
      - историю выполнений
      - типизацию перед выполнением
    """

    def __init__(self, scope: int = 0,
                 policy: Optional[PolicySnapshot] = None,
                 fuel: int = 10000):
        self.state = InterpreterState(
            scope=scope,
            context_policy=policy or POLICY_ZERO,
            fuel=fuel
        )

    def typecheck(self, expr) -> tuple:
        """Типизировать выражение до выполнения."""
        return verify_program(expr, self.state.context_policy)

    def execute(self, expr, typecheck: bool = True) -> ExecutionTrace:
        """
        Выполнить выражение. Обновить состояние.

        Args:
            expr: GExpr2
            typecheck: проверять типы перед выполнением

        Returns:
            ExecutionTrace
        """
        if typecheck:
            ok, typ, err = self.typecheck(expr)
            if not ok:
                raise TypeError(f"Ошибка типизации: {err}")

        trace = run(expr,
                    scope=self.state.scope,
                    context_policy=self.state.context_policy,
                    fuel=self.state.fuel,
                    prev_hash=self.state.current_hash)

        # Обновляем состояние + hash-chain
        self.state.ledger.extend(trace.records)
        self.state.history.append(trace)
        if trace.final_hash:
            self.state.current_hash = trace.final_hash

        return trace

    def run_many(self, exprs: list) -> List[ExecutionTrace]:
        """Выполнить список выражений последовательно."""
        return [self.execute(e) for e in exprs]

    def set_policy(self, policy: PolicySnapshot) -> None:
        """Установить контекстную политику."""
        self.state.context_policy = policy

    def set_scope(self, scope: int) -> None:
        """Установить scope."""
        self.state.scope = scope

    def get_ledger(self) -> List[LedgerRecord]:
        """Получить полный журнал."""
        return list(self.state.ledger)

    def get_history(self) -> List[ExecutionTrace]:
        """Получить историю выполнений."""
        return list(self.state.history)

    def reset(self) -> None:
        """Сбросить состояние (кроме scope и policy)."""
        self.state.ledger.clear()
        self.state.history.clear()

    def __repr__(self) -> str:
        return self.state.summary()
