# GateLang Construct Classification: Core vs. Extended vs. Internal

## 1. Overview

This document classifies all major constructs in the `gatelang-runtime-` repository into three categories:

**A. CORE CANDIDATE:**
- Constructs that align with GateLang v1 Core specification
- May be considered for inclusion in canonical spec (with justification)
- Minimal, declarative, deterministic

**B. EXTENDED / RESEARCH:**
- Constructs that extend beyond GateLang v1 Core
- Useful for research and experimentation
- Not part of minimal v1 specification

**C. INTERNAL RUNTIME ONLY:**
- Constructs that are implementation internals
- Not exposed to end users
- Not part of language specification

**Requirement:** No construct should go into CORE without explicit justification.

## 2. Construct Classification

### 2.1 GGate

**Name:** `GGate`

**Current Role:** Represents a gate definition (gate name, entity type, states, rules)

**Target Classification:** **A. CORE CANDIDATE**

**Reason:**
- Aligns with GateLang v1 Core concept of "gate"
- Essential for defining gate evaluation logic
- Minimal and declarative
- Directly maps to canonical `gate` construct in GATELANG_SPEC.md

**Justification for CORE:**
- GateLang v1 Core explicitly includes `gate` as a core concept
- `GGate` is the implementation representation of this concept
- No loops, recursion, or complex control flow
- Declarative definition of gate structure

---

### 2.2 GEmit

**Name:** `GEmit`

**Current Role:** Represents an event emission action

**Target Classification:** **A. CORE CANDIDATE**

**Reason:**
- Aligns with GateLang v1 Core concept of "emit"
- Essential for emitting domain events
- Minimal and declarative
- Directly maps to canonical `emit` action in GATELANG_SPEC.md

**Justification for CORE:**
- GateLang v1 Core explicitly includes `emit` as a core concept
- `GEmit` is the implementation representation of this action
- No side effects beyond event emission
- Declarative action

---

### 2.3 GRet

**Name:** `GRet`

**Current Role:** Represents a return action (verdict, next state)

**Target Classification:** **A. CORE CANDIDATE** (with renaming)

**Reason:**
- Aligns with GateLang v1 Core concepts of "verdict" and "transition"
- Essential for returning evaluation result
- Minimal and declarative
- Maps to canonical `verdict` and `transition` actions in GATELANG_SPEC.md

**Justification for CORE:**
- GateLang v1 Core explicitly includes `verdict` and `transition` as core concepts
- `GRet` is the implementation representation of these actions
- No complex control flow
- Declarative action

**Note:** Consider renaming `GRet` to `GVerdict` or `GResult` for clarity.

---

### 2.4 GSeq

**Name:** `GSeq`

**Current Role:** Represents sequential composition of actions

**Target Classification:** **B. EXTENDED / RESEARCH** (or **C. INTERNAL RUNTIME ONLY**)

**Reason:**
- GateLang v1 Core does NOT explicitly include arbitrary sequencing
- In v1, actions within a rule are implicitly sequential (emit, then transition)
- Explicit `GSeq` construct may be runtime internal for representing action lists
- Not needed as user-facing language construct in minimal v1

**Justification for EXTENDED/INTERNAL:**
- GateLang v1 Core rules have implicit action ordering (emit before transition)
- Explicit sequencing construct is not part of minimal declarative syntax
- May be useful for runtime implementation (internal) or future extensions (research)
- Not essential for v1 Core

**Decision:** Classify as **C. INTERNAL RUNTIME ONLY** unless there's a strong justification for exposing it to users.

---

### 2.5 GPar

**Name:** `GPar`

**Current Role:** Represents parallel composition of actions

**Target Classification:** **B. EXTENDED / RESEARCH**

**Reason:**
- GateLang v1 Core does NOT include parallel composition
- Parallel execution is not needed for minimal gate evaluation
- May be useful for advanced policy composition (research)
- Not part of minimal v1 specification

**Justification for EXTENDED:**
- GateLang v1 Core is minimal and deterministic
- Parallel composition adds complexity without clear benefit for v1 use cases
- May be explored in future research (e.g., concurrent gate evaluation)
- Not essential for current 3 gate families (DailyHoursGate, PayrollGate, SafetyGate)

**Decision:** **REJECT FOR V1**, defer to Extended/Research.

---

### 2.6 GTry

**Name:** `GTry`

**Current Role:** Represents try/catch style error handling

**Target Classification:** **B. EXTENDED / RESEARCH**

**Reason:**
- GateLang v1 Core does NOT include try/catch control flow
- Error handling is not part of minimal declarative gate evaluation
- May be useful for advanced error recovery (research)
- Not part of minimal v1 specification

**Justification for EXTENDED:**
- GateLang v1 Core is minimal and deterministic
- Try/catch adds imperative control flow
- Error handling should be done at runtime layer, not in language
- Not essential for current 3 gate families

**Decision:** **REJECT FOR V1**, defer to Extended/Research.

---

### 2.7 GWith

**Name:** `GWith`

**Current Role:** Represents context management (e.g., with statement)

**Target Classification:** **B. EXTENDED / RESEARCH** (or **C. INTERNAL RUNTIME ONLY**)

**Reason:**
- GateLang v1 Core does NOT include context management
- Context management is typically a runtime concern, not language feature
- May be useful for advanced resource management (research)
- Not part of minimal v1 specification

**Justification for EXTENDED/INTERNAL:**
- GateLang v1 Core is minimal and declarative
- Context management is imperative and runtime-specific
- Not essential for current 3 gate families
- May be runtime internal for managing evaluation context

**Decision:** **REJECT FOR V1**, classify as **C. INTERNAL RUNTIME ONLY** or defer to Extended/Research.

---

### 2.8 GWhile

**Name:** `GWhile`

**Current Role:** Represents while loop

**Target Classification:** **B. EXTENDED / RESEARCH** (REJECTED FOR V1)

**Reason:**
- GateLang v1 Core explicitly does NOT include loops
- Loops are not needed for minimal gate evaluation
- Loops add complexity and non-determinism risk
- Not part of minimal v1 specification

**Justification for REJECTION:**
- GateLang v1 Core explicitly excludes loops (see GATELANG_SPEC.md, Section 8: Minimality Statement)
- Loops are not needed for current 3 gate families
- Loops add complexity and make verification harder
- Declarative rules are sufficient for v1 use cases

**Decision:** **REJECT FOR V1**, defer to Extended/Research (if ever needed).

---

### 2.9 GLoop

**Name:** `GLoop`

**Current Role:** Represents general loop construct

**Target Classification:** **B. EXTENDED / RESEARCH** (REJECTED FOR V1)

**Reason:**
- GateLang v1 Core explicitly does NOT include loops
- Loops are not needed for minimal gate evaluation
- Loops add complexity and non-determinism risk
- Not part of minimal v1 specification

**Justification for REJECTION:**
- GateLang v1 Core explicitly excludes loops (see GATELANG_SPEC.md, Section 8: Minimality Statement)
- Loops are not needed for current 3 gate families
- Loops add complexity and make verification harder
- Declarative rules are sufficient for v1 use cases

**Decision:** **REJECT FOR V1**, defer to Extended/Research (if ever needed).

---

### 2.10 GGuard

**Name:** `GGuard`

**Current Role:** Represents guard condition (conditional execution)

**Target Classification:** **A. CORE CANDIDATE** (as part of rule conditions)

**Reason:**
- GateLang v1 Core includes conditions in rules (`when` clause)
- Guard conditions are essential for rule matching
- Minimal and declarative
- Directly maps to canonical `condition` in GATELANG_SPEC.md

**Justification for CORE:**
- GateLang v1 Core explicitly includes `condition` as a core concept
- `GGuard` is the implementation representation of rule conditions
- No complex control flow (just boolean evaluation)
- Declarative condition checking

**Note:** `GGuard` should be part of rule condition evaluation, not a standalone control flow construct.

---

### 2.11 Policy Composition Constructs

**Name:** Policy composition constructs (e.g., policy parameters, policy checks)

**Current Role:** Represents policy parameter access and composition

**Target Classification:** **A. CORE CANDIDATE** (for basic policy parameters) + **B. EXTENDED / RESEARCH** (for advanced composition)

**Reason:**
- GateLang v1 Core includes basic policy parameters (`policy.flag == true/false`)
- Advanced policy composition (e.g., policy inheritance, policy merging) is not part of v1
- Basic policy checks are essential for gate evaluation
- Advanced composition is research topic

**Justification for CORE (basic):**
- GateLang v1 Core explicitly includes `policy parameter` as a core concept
- Basic policy checks (`policy.flag == true/false`) are part of v1
- No complex composition logic in v1

**Justification for EXTENDED (advanced):**
- Advanced policy composition (inheritance, merging, conflict resolution) is not part of v1
- May be explored in future research
- Not essential for current 3 gate families

**Decision:**
- **KEEP IN CORE:** Basic policy parameter access (`policy.flag`)
- **DEFER TO EXTENDED:** Advanced policy composition

---

### 2.12 Typecheck / Verification Helpers

**Name:** Typecheck and verification helper functions

**Current Role:** Provides type checking and verification support for gate rules

**Target Classification:** **C. INTERNAL RUNTIME ONLY**

**Reason:**
- Type checking is a runtime implementation concern, not a language feature
- Verification helpers are tools for developers, not end users
- Not part of language specification
- Implementation internals

**Justification for INTERNAL:**
- GateLang v1 Core does not expose type checking as a language feature
- Type checking is done by the runtime/interpreter, not by the language itself
- Verification helpers are development tools, not language constructs
- Not visible to end users writing gate rules

**Decision:** **INTERNAL ONLY**, not part of language specification.

---

### 2.13 Interpreter State / Ledger

**Name:** Interpreter state and ledger (runtime execution state)

**Current Role:** Manages runtime execution state, event ledger, entity state

**Target Classification:** **C. INTERNAL RUNTIME ONLY**

**Reason:**
- Interpreter state is a runtime implementation concern, not a language feature
- Ledger is a runtime data structure, not a language construct
- Not part of language specification
- Implementation internals

**Justification for INTERNAL:**
- GateLang v1 Core is stateless (evaluation is input → output)
- Runtime state management is separate from language semantics
- Ledger is a runtime optimization, not a language feature
- Not visible to end users writing gate rules

**Decision:** **INTERNAL ONLY**, not part of language specification.

---

## 3. Summary Table

| Construct | Current Role | Target Classification | Reason |
|-----------|--------------|----------------------|--------|
| `GGate` | Gate definition | **A. CORE CANDIDATE** | Aligns with v1 `gate` concept |
| `GEmit` | Event emission | **A. CORE CANDIDATE** | Aligns with v1 `emit` action |
| `GRet` | Return verdict/state | **A. CORE CANDIDATE** | Aligns with v1 `verdict`/`transition` |
| `GSeq` | Sequential composition | **C. INTERNAL RUNTIME ONLY** | Implicit in v1, not user-facing |
| `GPar` | Parallel composition | **B. EXTENDED / RESEARCH** | Not needed for v1, research topic |
| `GTry` | Try/catch error handling | **B. EXTENDED / RESEARCH** | Not needed for v1, research topic |
| `GWith` | Context management | **C. INTERNAL RUNTIME ONLY** | Runtime concern, not language feature |
| `GWhile` | While loop | **B. EXTENDED / RESEARCH** | **REJECTED FOR V1** (explicitly excluded) |
| `GLoop` | General loop | **B. EXTENDED / RESEARCH** | **REJECTED FOR V1** (explicitly excluded) |
| `GGuard` | Guard condition | **A. CORE CANDIDATE** | Aligns with v1 `condition` concept |
| Policy (basic) | Policy parameter access | **A. CORE CANDIDATE** | Aligns with v1 `policy parameter` |
| Policy (advanced) | Policy composition | **B. EXTENDED / RESEARCH** | Not needed for v1, research topic |
| Typecheck | Type checking helpers | **C. INTERNAL RUNTIME ONLY** | Runtime implementation concern |
| Interpreter State | Runtime execution state | **C. INTERNAL RUNTIME ONLY** | Runtime implementation concern |
| Ledger | Event ledger | **C. INTERNAL RUNTIME ONLY** | Runtime data structure |

## 4. Classification Counts

**A. CORE CANDIDATE:** 5 constructs
- `GGate`, `GEmit`, `GRet`, `GGuard`, Policy (basic)

**B. EXTENDED / RESEARCH:** 5 constructs
- `GPar`, `GTry`, `GWhile`, `GLoop`, Policy (advanced)

**C. INTERNAL RUNTIME ONLY:** 4 constructs
- `GSeq`, `GWith`, Typecheck, Interpreter State/Ledger

**Total:** 14 constructs classified

## 5. Key Takeaways

1. **Core is Minimal:** Only 5 constructs are candidates for GateLang v1 Core
2. **Loops Rejected:** `GWhile` and `GLoop` are explicitly rejected for v1
3. **Runtime Internals:** Many constructs are implementation internals, not language features
4. **Research Topics:** Advanced features (parallel composition, try/catch, advanced policy) are deferred to research
5. **No Overclaim:** This classification does NOT automatically make constructs part of v1 Core; they are candidates only

**Next Step:** See `MIGRATION_DECISIONS.md` for final decisions on each construct.
