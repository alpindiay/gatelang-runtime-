"""
gatelang/server.py
-------------------
REST API server for GateLang Runtime.
Author: A. A. Noh · UTE TLI SYSTEMS · DOI: 10.17605/OSF.IO/49UMB

Endpoints:
  POST /run          — execute a GateLang program
  POST /typecheck    — typecheck without execution
  POST /compile      — compile to LedgerRecord list
  GET  /health       — health check
  GET  /info         — runtime info

Dependencies: pip install flask --break-system-packages
"""

from __future__ import annotations
import json
import sys
import os
from typing import Any, Dict, Tuple

# Add parent dir to path if running directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from flask import Flask, request, jsonify, Response
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

from .types import POLICY_ZERO
from .semantics import run, compile2, eval2
from .typechecker import verify_program, typecheck_safe
from .export import (
    trace_to_json, record_to_json, type_to_json,
    policy_from_json, expr_from_json, to_json
)

__version__ = "0.1.0"


def create_app() -> "Flask":
    if not FLASK_AVAILABLE:
        raise ImportError(
            "Flask not installed. Run: pip install flask --break-system-packages"
        )

    app = Flask(__name__)
    app.config["JSON_ENSURE_ASCII"] = False

    # ─────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────

    def ok(data: Dict, status: int = 200) -> Response:
        return Response(
            json.dumps(data, indent=2, ensure_ascii=False),
            status=status,
            mimetype="application/json"
        )

    def err(message: str, status: int = 400) -> Response:
        return ok({"ok": False, "error": message}, status)

    def parse_request() -> Tuple[Any, Any, Any, int]:
        """Parse common request fields: expr, scope, context_policy, fuel."""
        data = request.get_json(force=True, silent=True) or {}
        try:
            expr = expr_from_json(data.get("expr", {}))
        except Exception as e:
            return None, None, None, -1, str(e)

        scope = data.get("scope", 0)
        ctx_pol = data.get("context_policy")
        context_policy = policy_from_json(ctx_pol) if ctx_pol else POLICY_ZERO
        fuel = data.get("fuel", 1000)
        return expr, scope, context_policy, fuel, None

    # ─────────────────────────────────────────
    # ENDPOINTS
    # ─────────────────────────────────────────

    @app.get("/health")
    def health():
        """Health check."""
        return ok({"ok": True, "status": "running", "version": __version__})

    @app.get("/info")
    def info():
        """Runtime information."""
        return ok({
            "ok": True,
            "name": "GateLang Runtime",
            "version": __version__,
            "author": "A. A. Noh · UTE TLI SYSTEMS",
            "doi": "10.17605/OSF.IO/49UMB",
            "lean_repo": "github.com/alpindiay/lean4-ute-tli",
            "runtime_repo": "github.com/alpindiay/gatelang-runtime-",
            "verified_theorems": 1213,
            "sorry_count": 0,
            "constructs": [
                "gGate", "gSeq", "gPar", "gTry",
                "gWith", "gWhile", "gLoop", "gEmit", "gRet"
            ]
        })

    @app.post("/run")
    def run_program():
        """
        Execute a GateLang program.

        Request body:
        {
          "expr": { "type": "gGate", "evidence": [...], "policy": {...}, "agent_id": 42 },
          "scope": 0,
          "context_policy": { "id": 0, "min_evidence": 0, "effective_at": 0 },
          "fuel": 1000
        }

        Response:
        {
          "ok": true,
          "result": { "type": "gFact", "record": {...} },
          "records": [...],
          "event7s": [...],
          "emit_codes": [...],
          "stats": { "record_count": 1, "pass_count": 1, ... }
        }
        """
        expr, scope, context_policy, fuel, parse_err = parse_request()
        if parse_err:
            return err(f"Parse error: {parse_err}")

        try:
            trace = run(expr, scope=scope, context_policy=context_policy, fuel=fuel)
            data = trace_to_json(trace)
            data["ok"] = True
            return ok(data)
        except Exception as e:
            return err(f"Runtime error: {str(e)}", 500)

    @app.post("/typecheck")
    def typecheck_program():
        """
        Typecheck a GateLang program without executing it.

        Request body:
        {
          "expr": { ... },
          "context_policy": { ... }  (optional)
        }

        Response:
        {
          "ok": true,
          "type_checks": true,
          "type": { "type": "TFact", "policy": {...} }
        }
        """
        data = request.get_json(force=True, silent=True) or {}
        try:
            expr = expr_from_json(data.get("expr", {}))
        except Exception as e:
            return err(f"Parse error: {str(e)}")

        ctx_pol = data.get("context_policy")
        context_policy = policy_from_json(ctx_pol) if ctx_pol else POLICY_ZERO

        ok_flag, typ, type_err = verify_program(expr, context_policy)
        return ok({
            "ok": True,
            "type_checks": ok_flag,
            "type": type_to_json(typ) if typ else None,
            "error": type_err
        })

    @app.post("/compile")
    def compile_program():
        """
        Compile a GateLang program to a list of LedgerRecords.

        Response:
        {
          "ok": true,
          "records": [...],
          "count": 1
        }
        """
        expr, scope, context_policy, fuel, parse_err = parse_request()
        if parse_err:
            return err(f"Parse error: {parse_err}")

        try:
            records = compile2(expr, scope, context_policy, fuel)
            return ok({
                "ok": True,
                "records": [record_to_json(r) for r in records],
                "count": len(records),
                "all_valid": all(r.valid for r in records)
            })
        except Exception as e:
            return err(f"Compile error: {str(e)}", 500)

    @app.post("/batch")
    def batch_run():
        """
        Run multiple programs in one request.

        Request body:
        {
          "programs": [
            { "id": "prog1", "expr": {...}, "scope": 0 },
            { "id": "prog2", "expr": {...}, "scope": 1 }
          ],
          "fuel": 1000
        }
        """
        data = request.get_json(force=True, silent=True) or {}
        programs = data.get("programs", [])
        fuel = data.get("fuel", 1000)
        results = []

        for prog in programs:
            prog_id = prog.get("id", "unknown")
            try:
                expr = expr_from_json(prog.get("expr", {}))
                scope = prog.get("scope", 0)
                ctx_pol = prog.get("context_policy")
                context_policy = policy_from_json(ctx_pol) if ctx_pol else POLICY_ZERO
                trace = run(expr, scope=scope, context_policy=context_policy, fuel=fuel)
                result = trace_to_json(trace)
                result["id"] = prog_id
                result["ok"] = True
            except Exception as e:
                result = {"id": prog_id, "ok": False, "error": str(e)}
            results.append(result)

        return ok({"ok": True, "results": results, "count": len(results)})

    @app.errorhandler(404)
    def not_found(e):
        return err("Not found. Available: GET /health, GET /info, POST /run, POST /typecheck, POST /compile, POST /batch", 404)

    @app.errorhandler(405)
    def method_not_allowed(e):
        return err("Method not allowed", 405)

    return app


def start_server(host: str = "127.0.0.1", port: int = 8080, debug: bool = False):
    """Start the GateLang REST API server."""
    print(f"""
╔══════════════════════════════════════════════════════╗
║          GateLang REST API v{__version__}                   ║
║  А. А. Но · DOI: 10.17605/OSF.IO/49UMB               ║
╚══════════════════════════════════════════════════════╝

Endpoints:
  GET  http://{host}:{port}/health
  GET  http://{host}:{port}/info
  POST http://{host}:{port}/run
  POST http://{host}:{port}/typecheck
  POST http://{host}:{port}/compile
  POST http://{host}:{port}/batch
""")
    app = create_app()
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="GateLang REST API Server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    start_server(args.host, args.port, args.debug)
