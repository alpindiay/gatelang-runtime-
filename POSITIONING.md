# GateLang Runtime Repository Positioning

## 1. Purpose of This Repository

This repository (`gatelang-runtime-`) is a **research prototype runtime** for experimenting with gate evaluation logic and policy composition in the NOALYUT system.

**Primary Goals:**
- Explore runtime implementation strategies for gate evaluation
- Experiment with policy composition and verification approaches
- Provide a testbed for gate logic prototyping
- Investigate formal verification techniques for gate systems

**Non-Goals:**
- This repository does NOT define the canonical GateLang v1 specification
- This repository does NOT serve as the authoritative language reference
- This repository does NOT claim to be production-ready without further validation

## 2. What This Repository IS

✅ **Research Prototype Runtime**
- Experimental implementation of gate evaluation logic
- Testbed for policy composition strategies
- Exploration of verification approaches

✅ **Implementation Reference**
- Example of how GateLang concepts might be implemented
- Demonstration of runtime evaluation strategies
- Proof-of-concept for gate logic execution

✅ **Development Tool**
- Useful for prototyping gate rules
- Helpful for testing gate logic
- Valuable for exploring design space

## 3. What This Repository IS NOT

❌ **NOT Canonical GateLang v1 Specification**
- The canonical GateLang v1 specification lives in separate specification documents
- Python constructors and AST forms in this repo are implementation internals
- Human-facing canonical syntax is defined in spec docs, not in this codebase

❌ **NOT Formally Verified End-to-End**
- While this repo may explore verification techniques, it does NOT claim that the entire runtime is formally verified
- Formal verification claims must be proven separately with explicit proofs
- Any verification work is research-grade, not production-grade

❌ **NOT Production-Ready**
- This is a research prototype, not a production system
- No guarantees of correctness, performance, or security
- Not intended for deployment without significant additional work

❌ **NOT General-Purpose Language**
- This runtime is domain-specific to gate evaluation
- Not designed for arbitrary computation
- Not a replacement for general-purpose programming languages

## 4. Relation to GateLang v1 Canon

### 4.1 Canonical Specification

**Authoritative Source:** The canonical GateLang v1 specification is defined in separate specification documents:
- `GATELANG_SPEC.md`: Core concepts, verdicts, triggers, gate families
- `GATELANG_GRAMMAR.md`: Syntax, grammar, reserved words
- `GATELANG_STATIC_VALIDATION.md`: Validation rules, error classification
- `GATELANG_SEMANTICS.md`: Evaluation model, rule ordering, conflict resolution
- `GATELANG_EXAMPLES.md`: Reference examples with step-by-step evaluation

**This Repository:** This repository may implement or experiment with GateLang concepts, but it does NOT define the canon by itself.

### 4.2 Implementation vs. Specification

**Specification (Canon):**
- Defines WHAT GateLang is
- Defines syntax, semantics, validation rules
- Language-agnostic (not tied to Python or any implementation language)
- Minimal, declarative, deterministic

**Implementation (This Repo):**
- Defines HOW GateLang might be implemented
- Uses Python constructors and AST forms (implementation internals)
- May include experimental features not in GateLang v1 Core
- May include runtime-specific optimizations and internals

### 4.3 Construct Classification

Constructs in this repository fall into three categories:

**A. Core Candidates:**
- Constructs that align with GateLang v1 Core specification
- May be considered for inclusion in canonical spec (with justification)
- Examples: gate, emit, verdict, transition

**B. Extended / Research:**
- Constructs that extend beyond GateLang v1 Core
- Useful for research and experimentation
- Not part of minimal v1 specification
- Examples: parallel composition, advanced policy composition

**C. Internal Runtime Only:**
- Constructs that are implementation internals
- Not exposed to end users
- Not part of language specification
- Examples: interpreter state, ledger, AST nodes

See `CORE_VS_EXTENDED.md` for detailed classification.

## 5. Relation to Formal Verification Claims

### 5.1 Verification Status

**Current Status:**
- This repository explores verification techniques for gate systems
- Any verification work is research-grade, not production-grade
- No claim is made that the entire runtime is formally verified end-to-end

**Verification Claims:**
- Formal verification claims must be proven separately with explicit proofs
- Verification proofs must be documented and auditable
- Verification scope must be clearly stated (what is verified, what is not)

### 5.2 Separation of Concerns

**Formal Model:**
- Canonical TLI formalization (in Lean) defines the formal model
- GateLang v1 specification defines the language semantics
- Formal proofs (if any) must reference these canonical sources

**Runtime Implementation:**
- This repository implements a runtime for gate evaluation
- Runtime correctness is separate from formal model correctness
- Runtime may have bugs, optimizations, or deviations from formal model

**No Overclaim:**
- Do NOT claim that this runtime is formally verified unless proven
- Do NOT claim that this runtime is bug-free or production-ready
- Do NOT claim that this runtime is the canonical implementation

### 5.3 Future Verification Work

**If Verification is Pursued:**
- Clearly document what is verified (scope, properties, assumptions)
- Provide explicit proofs (in Lean, Coq, or other proof assistant)
- Separate formal model from runtime implementation
- Do NOT overclaim verification coverage

**Recommended Approach:**
- Verify formal model (TLI in Lean) separately
- Verify GateLang semantics separately
- Verify runtime implementation separately (if needed)
- Clearly document gaps between formal model and runtime

## 6. Recommended Usage

### 6.1 For Language Designers

**Use This Repo For:**
- Exploring implementation strategies
- Prototyping new gate rules
- Testing language design decisions

**Do NOT Use This Repo For:**
- Defining canonical GateLang v1 syntax
- Claiming formal verification without proofs
- Production deployment

### 6.2 For Runtime Developers

**Use This Repo For:**
- Understanding runtime implementation approaches
- Experimenting with optimization strategies
- Testing gate evaluation logic

**Do NOT Use This Repo For:**
- Assuming this is the only correct implementation
- Claiming this is production-ready
- Ignoring canonical specification

### 6.3 For Researchers

**Use This Repo For:**
- Exploring verification techniques
- Experimenting with policy composition
- Investigating gate system properties

**Do NOT Use This Repo For:**
- Claiming end-to-end verification without proofs
- Ignoring separation between formal model and runtime
- Overclaiming correctness or completeness

## 7. Summary

| Aspect | Status |
|--------|--------|
| **Repository Type** | Research prototype runtime |
| **Canonical Spec** | NO (spec lives in separate docs) |
| **Formally Verified** | NO (unless proven separately) |
| **Production-Ready** | NO (research prototype only) |
| **Relation to GateLang v1** | May implement v1, but does not define it |
| **Python AST Forms** | Implementation internals (not canonical syntax) |
| **Verification Claims** | Must be proven separately (no overclaim) |

**Key Takeaway:** This repository is a research prototype runtime for gate evaluation. It does NOT define the canonical GateLang v1 specification, and it does NOT claim to be formally verified or production-ready. Canonical syntax and semantics live in separate specification documents.
