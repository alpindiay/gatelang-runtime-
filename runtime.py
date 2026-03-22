#!/usr/bin/env python3
"""
runtime.py
----------
CLI для GateLang Runtime.
Author: A. A. Noh · UTE TLI SYSTEMS · DOI: 10.17605/OSF.IO/49UMB

Использование / Usage:
  python runtime.py repl              # интерактивный REPL
  python runtime.py run examples/basic.py
  python runtime.py check examples/basic.py
  python runtime.py demo              # демонстрация всех примеров
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def cmd_repl():
    from gatelang.repl import start_repl
    start_repl()


def cmd_run(path: str):
    """Запустить файл с GateLang программами."""
    print(f"Запуск / Running: {path}")
    print()
    with open(path) as f:
        code = f.read()
    exec(compile(code, path, 'exec'), {'__name__': '__main__'})


def cmd_demo():
    """Запустить все примеры."""
    examples_dir = os.path.join(os.path.dirname(__file__), 'examples')
    examples = ['basic.py', 'advanced.py', 'seven_tuple.py']
    for ex in examples:
        path = os.path.join(examples_dir, ex)
        if os.path.exists(path):
            print(f"\n{'█' * 60}")
            print(f"█  {ex}")
            print(f"{'█' * 60}\n")
            cmd_run(path)
            print()


def cmd_help():
    print(__doc__)


def main():
    args = sys.argv[1:]
    if not args or args[0] in ('-h', '--help', 'help'):
        cmd_help()
    elif args[0] == 'repl':
        cmd_repl()
    elif args[0] == 'run' and len(args) > 1:
        cmd_run(args[1])
    elif args[0] == 'demo':
        cmd_demo()
    else:
        print(f"Неизвестная команда: {args[0]}")
        cmd_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
