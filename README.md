# Dynamic Commitment Layer (DCL)

**v0.2.0 — surgical rewrite**

**Short technical note:** [TECHNICAL_NOTE.md](TECHNICAL_NOTE.md)

A minimal decision module that introduces an explicit **dynamic hidden variable** required for correct long-horizon residual-diagnostic behavior.

---

### Core Claim

There exist residual-diagnostic processes whose correct long-horizon behavior is impossible without a dynamic hidden variable that simultaneously:

1. **stores memory** the visible system is structurally forbidden to retain,
2. **collapses ambiguity** by selecting among multiple futures consistent with the observations, and
3. **maintains an internal model** of the process.

Once this variable is admitted, the joint process becomes well-posed.  
Any monitor limited to the visible residual and competence signals is information-theoretically incomplete.

The Dynamic Commitment Layer supplies that variable explicitly.

---

### The Hidden Variable χ

| Role                    | Function                                                                 |
|-------------------------|--------------------------------------------------------------------------|
| **B – Forbidden Memory**    | χ retains information that the visible pair (d, c) cannot carry forward |
| **C – Future Selection**    | When multiple futures remain consistent with observations, χ selects one |
| **D – Internal Model**      | χ acts as a minimal internal predictor / state estimate                 |

These three roles are performed by the *same* bit.  
No function of finite windows of the visible signals can satisfy all three simultaneously.

---

### State

```c
typedef struct {
    double d;       /* visible residual disorder           [0,1] */
    double c;       /* visible diagnostic competence       [0,1] */
    double lambda;  /* commitment tension                  [0,1] */
    int    chi;     /* dynamic commitment variable χ       0/1  */
} dcl_state_t;
```

- `d, c` — the only observables available to any external monitor
- `lambda` — commitment tension
- `chi` — the hidden commitment variable

---

### Non-Reducibility

Any residual + confidence + hysteresis construction maintains state that is a pure function of a finite history of `(d, c)`.

The value of χ controls both polarity and timing of subsequent commitment acts. After an odd number of transitions of χ, the future trajectory of the joint process diverges from every trajectory generable by a monitor that only sees the visible signals.

The information gap is permanent.

---

### Usage

```c
#include "dynamic_commitment.h"

dcl_state_t s;
dcl_init(&s);

dcl_step(&s, &DCL_DEFAULTS, r_fresh, k_fresh, r_corr);

if (dcl_commit(&s, &DCL_DEFAULTS, r_corr)) {
    /* adopt committed (restricted) disposition */
} else {
    /* ordinary residual handling */
}
```

---

### Files

| File | Description |
|------|-------------|
| `dynamic_commitment.h` | Header-only implementation |
| `DCL_DESIGN_NOTE.md` | Full design rationale and non-reducibility argument |
| `TECHNICAL_NOTE.md` | Polished short technical note |
| `dcl_harness.py` | Empirical stress test |

---

### Historical Note

This module was previously released as the Residual Sublation Layer (v0.1.0).  
The surgical rewrite retains the repository and the hidden-variable DNA while discarding the elevation/sublation framing in favour of explicit dynamic commitment.

---

License: MIT
