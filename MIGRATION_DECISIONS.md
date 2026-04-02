# GateLang Migration Decisions: Core vs. Extended vs. Rejected

## 1. Overview

This document provides final decisions on each construct in the `gatelang-runtime-` repository:

**Decision Categories:**
- **KEEP IN CORE:** Construct is part of GateLang v1 Core specification
- **DEFER TO EXTENDED:** Construct is deferred to GateLang Extended/Research (not in v1)
- **REJECT FOR V1:** Construct is explicitly rejected for v1 (may be reconsidered later)
- **INTERNAL ONLY:** Construct is runtime implementation internal (not part of language spec)

## 2. Construct Decisions

### 2.1 GGate

**Decision:** **KEEP IN CORE**

**Rationale:**
- Essential for defining gate evaluation logic
- Aligns with GateLang v1 Core `gate` concept
- Minimal, declarative, deterministic
- Required for all 3 gate families (DailyHoursGate, PayrollGate, SafetyGate)

**Canonical Mapping:**
- `GGate` → `gate <Name>` in GATELANG_GRAMMAR.md
- Includes: gate name, entity type, states, rules

---

### 2.2 GEmit

**Decision:** **KEEP IN CORE**

**Rationale:**
- Essential for emitting domain events
- Aligns with GateLang v1 Core `emit` action
- Minimal, declarative, no side effects beyond event emission
- Required for all 3 gate families

**Canonical Mapping:**
- `GEmit` → `emit <EventName>` in GATELANG_GRAMMAR.md

---

### 2.3 GRet

**Decision:** **KEEP IN CORE** (with renaming recommendation)

**Rationale:**
- Essential for returning evaluation result (verdict, next state)
- Aligns with GateLang v1 Core `verdict` and `transition` actions
- Minimal, declarative, no complex control flow
- Required for all 3 gate families

**Canonical Mapping:**
- `GRet` → `verdict <Verdict>` + `transition <StateName>` in GATELANG_GRAMMAR.md

**Recommendation:** Consider renaming `GRet` to `GVerdict` or `GResult` for clarity.

---

### 2.4 GSeq

**Decision:** **INTERNAL ONLY**

**Rationale:**
- GateLang v1 Core does NOT expose arbitrary sequencing to users
- Actions within a rule are implicitly sequential (emit, then transition)
- `GSeq` is a runtime internal for representing action lists
- Not needed as user-facing language construct

**Canonical Mapping:**
- No direct mapping to user-facing syntax
- Implicit in rule action ordering

**Note:** `GSeq` may be used internally by the interpreter to represent action sequences, but it is NOT part of the language specification.

---

### 2.5 GPar

**Decision:** **REJECT FOR V1** (defer to Extended/Research)

**Rationale:**
- GateLang v1 Core does NOT include parallel composition
- Parallel execution is not needed for minimal gate evaluation
- Adds complexity without clear benefit for v1 use cases
- Not required for current 3 gate families

**Future Consideration:**
- May be explored in GateLang Extended for concurrent gate evaluation
- Requires careful design to maintain determinism
- Not a priority for v1

---

### 2.6 GTry

**Decision:** **REJECT FOR V1** (defer to Extended/Research)

**Rationale:**
- GateLang v1 Core does NOT include try/catch control flow
- Error handling is not part of minimal declarative gate evaluation
- Adds imperative control flow
- Error handling should be done at runtime layer, not in language

**Future Consideration:**
- May be explored in GateLang Extended for advanced error recovery
- Not a priority for v1

---

### 2.7 GWith

**Decision:** **INTERNAL ONLY**

**Rationale:**
- GateLang v1 Core does NOT include context management
- Context management is a runtime concern, not a language feature
- May be used internally for managing evaluation context
- Not visible to end users

**Canonical Mapping:**
- No direct mapping to user-facing syntax

---

### 2.8 GWhile

**Decision:** **REJECT FOR V1** (explicitly excluded)

**Rationale:**
- GateLang v1 Core explicitly excludes loops (see GATELANG_SPEC.md, Section 8)
- Loops are not needed for current 3 gate families
- Loops add complexity and make verification harder
- Declarative rules are sufficient for v1 use cases

**Explicit Exclusion:**
- GateLang v1 Minimality Statement explicitly lists loops as NOT SUPPORTED
- This is a design decision to keep the language minimal and auditable

**Future Consideration:**
- Unlikely to be added even in Extended (loops are antithetical to declarative design)

---

### 2.9 GLoop

**Decision:** **REJECT FOR V1** (explicitly excluded)

**Rationale:**
- GateLang v1 Core explicitly excludes loops (see GATELANG_SPEC.md, Section 8)
- Loops are not needed for current 3 gate families
- Loops add complexity and make verification harder
- Declarative rules are sufficient for v1 use cases

**Explicit Exclusion:**
- GateLang v1 Minimality Statement explicitly lists loops as NOT SUPPORTED
- This is a design decision to keep the language minimal and auditable

**Future Consideration:**
- Unlikely to be added even in Extended (loops are antithetical to declarative design)

---

### 2.10 GGuard

**Decision:** **KEEP IN CORE** (as part of rule conditions)

**Rationale:**
- Essential for rule matching and conditional execution
- Aligns with GateLang v1 Core `condition` concept
- Minimal, declarative, boolean-only evaluation
- Required for all 3 gate families

**Canonical Mapping:**
- `GGuard` → `when <Condition>` in GATELANG_GRAMMAR.md
- Includes: state checks, event checks, timeout checks, policy checks, count checks, field checks

**Note:** `GGuard` should be part of rule condition evaluation, not a standalone control flow construct.

---

### 2.11 Policy Composition Constructs

**Decision:**
- **KEEP IN CORE:** Basic policy parameter access (`policy.flag == true/false`)
- **DEFER TO EXTENDED:** Advanced policy composition (inheritance, merging, conflict resolution)

**Rationale (Basic):**
- Basic policy checks are essential for gate evaluation
- Aligns with GateLang v1 Core `policy parameter` concept
- Minimal, declarative, no complex composition logic
- Required for current 3 gate families

**Rationale (Advanced):**
- Advanced policy composition is not needed for v1
- Adds complexity without clear benefit for current use cases
- May be explored in GateLang Extended for advanced policy management

**Canonical Mapping (Basic):**
- `policy.flag` → `policy.<ParameterName> == true/false` in GATELANG_GRAMMAR.md

---

### 2.12 Typecheck / Verification Helpers

**Decision:** **INTERNAL ONLY**

**Rationale:**
- Type checking is a runtime implementation concern, not a language feature
- Verification helpers are tools for developers, not end users
- Not part of language specification
- Not visible to end users writing gate rules

**Canonical Mapping:**
- No direct mapping to user-facing syntax

---

### 2.13 Interpreter State / Ledger

**Decision:** **INTERNAL ONLY**

**Rationale:**
- Interpreter state is a runtime implementation concern, not a language feature
- Ledger is a runtime data structure, not a language construct
- GateLang v1 Core is stateless (evaluation is input → output)
- Not visible to end users writing gate rules

**Canonical Mapping:**
- No direct mapping to user-facing syntax

---

## 3. Decision Summary Table

| Construct | Decision | Rationale |
|-----------|----------|-----------|
| `GGate` | **KEEP IN CORE** | Essential, aligns with v1 `gate` |
| `GEmit` | **KEEP IN CORE** | Essential, aligns with v1 `emit` |
| `GRet` | **KEEP IN CORE** | Essential, aligns with v1 `verdict`/`transition` |
| `GSeq` | **INTERNAL ONLY** | Implicit in v1, not user-facing |
| `GPar` | **REJECT FOR V1** | Not needed, defer to Extended |
| `GTry` | **REJECT FOR V1** | Not needed, defer to Extended |
| `GWith` | **INTERNAL ONLY** | Runtime concern, not language feature |
| `GWhile` | **REJECT FOR V1** | Explicitly excluded (loops not supported) |
| `GLoop` | **REJECT FOR V1** | Explicitly excluded (loops not supported) |
| `GGuard` | **KEEP IN CORE** | Essential, aligns with v1 `condition` |
| Policy (basic) | **KEEP IN CORE** | Essential, aligns with v1 `policy parameter` |
| Policy (advanced) | **DEFER TO EXTENDED** | Not needed for v1, research topic |
| Typecheck | **INTERNAL ONLY** | Runtime implementation concern |
| Interpreter State | **INTERNAL ONLY** | Runtime implementation concern |
| Ledger | **INTERNAL ONLY** | Runtime data structure |

## 4. Decision Counts

**KEEP IN CORE:** 5 constructs
- `GGate`, `GEmit`, `GRet`, `GGuard`, Policy (basic)

**REJECT FOR V1:** 5 constructs
- `GPar`, `GTry`, `GWhile`, `GLoop`, Policy (advanced - deferred)

**INTERNAL ONLY:** 5 constructs
- `GSeq`, `GWith`, Typecheck, Interpreter State, Ledger

**Total:** 15 decisions

## 5. Minimal GateLang v1 Core

### 5.1 Core Constructs (User-Facing)

GateLang v1 Core includes ONLY:

1. **gate:** Gate definition (`gate <Name>`)
2. **entity:** Entity type declaration (`entity <EntityType>`)
3. **states:** State list declaration (`states { ... }`)
4. **trigger:** Trigger type (`on USER_ACTION | SYSTEM_TIMEOUT | SYSTEM_ACTION`)
5. **condition:** Boolean condition (`when <Condition>`)
6. **verdict:** Verdict action (`verdict PASS | HOLD | DENY`)
7. **emit:** Event emission action (`emit <EventName>`)
8. **transition:** State transition action (`transition <StateName>`)
9. **policy parameter:** Policy parameter access (`policy.<ParameterName>`)

### 5.2 Explicitly Rejected for v1

GateLang v1 Core explicitly does NOT include:

1. **while:** While loop (`GWhile`)
2. **loop:** General loop (`GLoop`)
3. **general recursion:** Recursive function calls
4. **arbitrary sequencing:** Explicit sequencing construct (implicit only)
5. **parallel composition:** Parallel execution (`GPar`)
6. **try/catch:** Error handling control flow (`GTry`)

### 5.3 Python AST / Constructors

**Classification:** **INTERNAL REPRESENTATION**

**Rationale:**
- Python constructors (`GGate`, `GEmit`, etc.) are implementation internals
- NOT human-facing canonical syntax
- Canonical syntax is defined in GATELANG_GRAMMAR.md (text-based, not Python)
- Python AST is one possible implementation, not the only one

**Implication:**
- Users write GateLang rules in text format (see GATELANG_GRAMMAR.md)
- Runtime parses text into Python AST (internal representation)
- Python AST is NOT the canonical syntax

### 5.4 Verification Claims

**Separation of Concerns:**

1. **Formal Model (TLI in Lean):**
   - Defines canonical semantics of gate evaluation
   - Formally verified (if proofs exist)
   - Separate from runtime implementation

2. **GateLang v1 Specification:**
   - Defines language syntax and semantics
   - Documented in specification files
   - Separate from runtime implementation

3. **Runtime Implementation (this repo):**
   - Implements gate evaluation logic
   - May have bugs, optimizations, or deviations
   - NOT automatically verified (unless proven separately)

**No Overclaim:**
- Do NOT claim that this runtime is formally verified unless proven
- Do NOT claim that this runtime is bug-free or production-ready
- Do NOT claim that this runtime is the canonical implementation
- Verification proofs must be documented separately

## 6. Recommended Clean Boundary

### 6.1 What Becomes GateLang v1 Canon

**Canonical Specification (Authoritative):**
- `GATELANG_SPEC.md`: Core concepts, verdicts, triggers, gate families
- `GATELANG_GRAMMAR.md`: Syntax, grammar, reserved words
- `GATELANG_STATIC_VALIDATION.md`: Validation rules, error classification
- `GATELANG_SEMANTICS.md`: Evaluation model, rule ordering, conflict resolution
- `GATELANG_EXAMPLES.md`: Reference examples with step-by-step evaluation

**Core Constructs (User-Facing):**
- gate, entity, states, trigger, condition, verdict, emit, transition, policy parameter

**Excluded from v1:**
- while, loop, general recursion, arbitrary sequencing, parallel composition, try/catch

### 6.2 What Remains Research Runtime

**Research Prototype Runtime (this repo):**
- Experimental implementation of gate evaluation logic
- Testbed for policy composition strategies
- Exploration of verification approaches
- NOT canonical specification
- NOT production-ready

**Extended/Research Constructs:**
- Parallel composition (`GPar`)
- Try/catch error handling (`GTry`)
- Advanced policy composition
- Future experimental features

**Internal Runtime Constructs:**
- Sequential composition (`GSeq`)
- Context management (`GWith`)
- Type checking helpers
- Interpreter state / ledger

### 6.3 What Should Be Ignored for Current Patent/Product Path

**Ignore for Patent/Product:**
- Loops (`GWhile`, `GLoop`) - explicitly excluded from v1
- Try/catch (`GTry`) - not part of minimal v1
- Parallel composition (`GPar`) - not needed for v1
- Advanced policy composition - not needed for v1
- Runtime implementation internals - not part of language spec

**Focus for Patent/Product:**
- GateLang v1 Core specification (minimal, declarative, deterministic)
- Core constructs (gate, entity, state, trigger, condition, verdict, emit, transition, policy)
- Canonical syntax and semantics (GATELANG_SPEC.md, GATELANG_GRAMMAR.md, etc.)
- Validation model (GATELANG_STATIC_VALIDATION.md)
- Evaluation model (GATELANG_SEMANTICS.md)

### 6.4 Clean Boundary Summary

| Aspect | GateLang v1 Canon | Research Runtime | Ignore for Patent/Product |
|--------|-------------------|------------------|---------------------------|
| **Specification** | GATELANG_*.md files | This repo (implementation) | Runtime internals |
| **Core Constructs** | 9 constructs (gate, entity, ...) | Extended constructs | Loops, try/catch, parallel |
| **Syntax** | Text-based (GATELANG_GRAMMAR.md) | Python AST (internal) | Python constructors |
| **Verification** | Formal model (TLI in Lean) | Runtime (not verified) | Unproven verification claims |
| **Status** | Canonical, authoritative | Research prototype | Experimental features |

## 7. Final Recommendations

### 7.1 For Language Specification

**Use:**
- GATELANG_*.md files as canonical specification
- Core constructs only (9 constructs)
- Text-based syntax (GATELANG_GRAMMAR.md)

**Avoid:**
- Python AST as canonical syntax
- Extended/research constructs in v1
- Unproven verification claims

### 7.2 For Runtime Implementation

**Use:**
- This repo as reference implementation
- Core constructs as foundation
- Extended constructs for research

**Avoid:**
- Claiming this is the only correct implementation
- Claiming this is production-ready
- Ignoring canonical specification

### 7.3 For Patent/Product

**Focus:**
- GateLang v1 Core specification
- Minimal, declarative, deterministic design
- Core constructs (9 constructs)
- Validation and evaluation models

**Ignore:**
- Loops, try/catch, parallel composition
- Runtime implementation internals
- Unproven verification claims
- Extended/research features

## 8. Conclusion

**Key Takeaways:**

1. **GateLang v1 Core is Minimal:** Only 9 core constructs (gate, entity, state, trigger, condition, verdict, emit, transition, policy)
2. **Loops Explicitly Rejected:** `GWhile` and `GLoop` are NOT part of v1
3. **Python AST is Internal:** Python constructors are implementation internals, not canonical syntax
4. **Verification Separate:** Formal model (TLI) is separate from runtime implementation
5. **Clean Boundary Established:** Clear separation between v1 Canon, Research Runtime, and Ignored Features

**Next Steps:**

1. Update this repo's README to reference POSITIONING.md
2. Document canonical specification location (GATELANG_*.md files)
3. Clearly mark extended/research features as non-v1
4. Separate formal verification claims from runtime implementation
5. Focus patent/product efforts on GateLang v1 Core specification

**Status:** Contradictions reduced, clean boundary established, ready for patent/product path.
