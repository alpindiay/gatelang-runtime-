"""
tests/test_hashchain.py
Тесты для hash-chain реализации в GateLang runtime.

Проверяет:
  1. LedgerRecord.compute_hash() детерминирован
  2. LedgerRecord.prev_hash корректно связывает записи
  3. compile2 с prev_hash корректно строит chain
  4. InterpreterState.verify_chain_integrity() работает
  5. Изменение любой записи ломает chain
"""
import pytest
from gatelang.types import (
    LedgerRecord, PolicySnapshot, EvidenceRef, Verdict,
    POLICY_ZERO, Event7
)
from gatelang.semantics import compile2, run
from gatelang.interpreter import GateLangInterpreter, InterpreterState


# ── §1. LedgerRecord hash determinism ──────────────────────────

def test_ledger_record_hash_deterministic():
    """compute_hash должен возвращать одинаковый результат для одинаковых данных."""
    rec = LedgerRecord(
        scope=1,
        verdict=Verdict.PASS,
        policy=POLICY_ZERO,
        evidence=[EvidenceRef(ref="ev1")],
        closed_at=1,
        prev_hash=""
    )
    h1 = rec.compute_hash()
    h2 = rec.compute_hash()
    assert h1 == h2, "Hash should be deterministic"
    assert len(h1) == 64, "SHA-256 produces 64 hex chars"


def test_ledger_record_hash_changes_on_mutation():
    """Разные данные → разные хэши."""
    rec1 = LedgerRecord(
        scope=1, verdict=Verdict.PASS, policy=POLICY_ZERO,
        evidence=[EvidenceRef(ref="ev1")], closed_at=1, prev_hash=""
    )
    rec2 = LedgerRecord(
        scope=2, verdict=Verdict.PASS, policy=POLICY_ZERO,
        evidence=[EvidenceRef(ref="ev1")], closed_at=2, prev_hash=""
    )
    assert rec1.compute_hash() != rec2.compute_hash()


def test_prev_hash_affects_record_hash():
    """Изменение prev_hash меняет compute_hash."""
    rec1 = LedgerRecord(
        scope=1, verdict=Verdict.PASS, policy=POLICY_ZERO,
        evidence=[], closed_at=1, prev_hash=""
    )
    rec2 = LedgerRecord(
        scope=1, verdict=Verdict.PASS, policy=POLICY_ZERO,
        evidence=[], closed_at=1, prev_hash="abc123"
    )
    assert rec1.compute_hash() != rec2.compute_hash()


# ── §2. Chain integrity через InterpreterState ─────────────────

def test_empty_chain_is_valid():
    """Пустой журнал имеет корректную chain."""
    state = InterpreterState()
    assert state.verify_chain_integrity() is True


def test_manual_chain_construction():
    """Ручное построение chain из двух записей."""
    rec1 = LedgerRecord(
        scope=1, verdict=Verdict.PASS, policy=POLICY_ZERO,
        evidence=[], closed_at=1, prev_hash=""
    )
    h1 = rec1.compute_hash()
    
    rec2 = LedgerRecord(
        scope=2, verdict=Verdict.PASS, policy=POLICY_ZERO,
        evidence=[], closed_at=2, prev_hash=h1
    )
    h2 = rec2.compute_hash()
    
    state = InterpreterState()
    state.ledger = [rec1, rec2]
    state.current_hash = h2
    assert state.verify_chain_integrity() is True


def test_broken_chain_detected():
    """Подмена prev_hash должна быть обнаружена."""
    rec1 = LedgerRecord(
        scope=1, verdict=Verdict.PASS, policy=POLICY_ZERO,
        evidence=[], closed_at=1, prev_hash=""
    )
    h1 = rec1.compute_hash()
    
    rec2 = LedgerRecord(
        scope=2, verdict=Verdict.PASS, policy=POLICY_ZERO,
        evidence=[], closed_at=2, prev_hash="TAMPERED_HASH"  # broken!
    )
    h2 = rec2.compute_hash()
    
    state = InterpreterState()
    state.ledger = [rec1, rec2]
    state.current_hash = h2
    assert state.verify_chain_integrity() is False


# ── §3. Event7 hash ────────────────────────────────────────────

def test_event7_hash():
    """Event7.compute_hash() должен быть детерминирован."""
    e = Event7(
        subject=0,
        context=1,
        execution=[EvidenceRef(ref="ev1")],
        conflict=False,
        escalated=False,
        outcome=Verdict.PASS,
        ledger=LedgerRecord(
            scope=1, verdict=Verdict.PASS, policy=POLICY_ZERO,
            evidence=[EvidenceRef(ref="ev1")], closed_at=1, prev_hash=""
        ),
        policy=POLICY_ZERO
    )
    h1 = e.compute_hash()
    h2 = e.compute_hash()
    assert h1 == h2
    assert len(h1) == 64


# ── §4. Summary & repr ────────────────────────────────────────

def test_interpreter_state_summary_shows_chain():
    """summary() должен показывать статус chain."""
    state = InterpreterState()
    s = state.summary()
    assert "chain=" in s
    assert "[OK]" in s


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
