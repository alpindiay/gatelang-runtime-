"""
gatelang/repl.py
----------------
Интерактивный REPL для GateLang.
Author: A. A. Noh · UTE TLI SYSTEMS
"""

import sys
import code
import readline
import rlcompleter

BANNER = """
╔══════════════════════════════════════════════════════╗
║          GateLang Runtime v0.1.0 — REPL              ║
║  Верифицированный DSL для аудируемых систем           ║
║  Author: А. А. Но · DOI: 10.17605/OSF.IO/49UMB       ║
╚══════════════════════════════════════════════════════╝

Быстрый старт / Quick start:
  from gatelang import *

  # Политика / Policy
  p = PolicySnapshot(id=1, min_evidence=2, effective_at=0)

  # Доказательства / Evidence
  ev = [EvidenceRef("doc-1"), EvidenceRef("doc-2")]

  # Программа / Program
  prog = GGate(ev, p, agent_id=42)

  # Запуск / Run
  result = run(prog, scope=0)
  print(result.summary())

  # Типизация / Typecheck
  ok, typ, err = verify_program(prog)

Введите help(run), help(GGate) и т.д. для справки.
Type exit() or Ctrl+D to quit.
"""

EXIT_MSG = "\nДо свидания / Goodbye."


def start_repl():
    """Запустить интерактивный REPL."""
    # Автодополнение
    readline.set_completer(rlcompleter.Completer().complete)
    readline.parse_and_bind("tab: complete")

    # Импорт всего в namespace
    local_ns = {}
    exec("from gatelang import *", local_ns)

    print(BANNER)
    try:
        code.interact(local=local_ns, banner="", exitmsg=EXIT_MSG)
    except SystemExit:
        print(EXIT_MSG)


if __name__ == "__main__":
    start_repl()
